"""Test the Grundfos entities."""

# Written by Claude, guided by Chris.

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from modbus_connection.mock import MockModbusConnection
import pytest
from tests.common import MockConfigEntry, async_fire_time_changed
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.typing import ClientSessionGenerator

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM


async def _poll(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    ("entity_id", "state"),
    [
        ("sensor.magna3_liquid_temperature", "47.23"),
        ("sensor.magna3_flow", "2.2"),
        ("sensor.magna3_head", "0.803"),
        ("sensor.magna3_power", "199"),
        ("sensor.magna3_energy", "1264"),
        ("sensor.magna3_speed", "4288"),
        ("sensor.magna3_relative_performance", "98.03"),
        ("sensor.magna3_control_mode", "constant_flow"),
        ("sensor.magna3_operating_mode", "auto_control"),
        ("sensor.magna3_alarm", "none"),
        ("sensor.magna3_warning", "none"),
        ("sensor.magna3_alarm_code", "0"),
        ("sensor.magna3_user_setpoint", "63.81"),
        ("sensor.magna3_actual_setpoint", "60.77"),
        ("sensor.magna3_process_feedback", "9.69"),
        ("sensor.magna3_control_source", "display"),
        ("sensor.magna3_flow_estimation", "within_range"),
        ("sensor.magna3_electronics_temperature", "42.0"),
        ("sensor.magna3_motor_current", "1.0"),
        ("sensor.magna3_dc_link_voltage", "198.0"),
        ("sensor.magna3_motor_frequency", "141.2"),
        ("sensor.magna3_specific_energy", "103"),
        ("sensor.magna3_operating_hours", "5760"),
        ("sensor.magna3_powered_hours", "5762"),
        ("sensor.magna3_starts", "449"),
        ("sensor.magna3_pumped_volume", "13629.0"),
        ("binary_sensor.magna3_running", STATE_ON),
        ("binary_sensor.magna3_started", STATE_ON),
        ("binary_sensor.magna3_alarm_active", STATE_OFF),
        ("binary_sensor.magna3_warning_active", STATE_OFF),
        ("binary_sensor.magna3_remote_control", STATE_OFF),
        ("binary_sensor.magna3_at_maximum_speed", STATE_ON),
        ("binary_sensor.magna3_at_minimum_speed", STATE_OFF),
        ("binary_sensor.magna3_low_flow_stop", STATE_OFF),
    ],
)
async def test_entity_states(
    hass: HomeAssistant, init_integration: MockConfigEntry, entity_id: str, state: str
) -> None:
    """Every entity decodes the live MAGNA3's registers."""
    assert hass.states.get(entity_id).state == state


@pytest.mark.parametrize(
    "entity_id",
    [
        "sensor.magna3_inlet_pressure",
        "sensor.magna3_remote_temperature_1",
        "sensor.magna3_remote_temperature_2",
        "sensor.magna3_motor_voltage",
        "sensor.magna3_heat_power",
        "sensor.magna3_heat_energy",
        "sensor.magna3_heat_differential_temperature",
    ],
)
async def test_absent_readings_create_no_entity(
    hass: HomeAssistant, init_integration: MockConfigEntry, entity_id: str
) -> None:
    """Readings the pump doesn't supply, and the heat meter without one, get none."""
    assert hass.states.get(entity_id) is None


async def test_duplicate_head_is_disabled_by_default(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """On a MAGNA3 differential pressure repeats head, so it starts disabled."""
    entry = entity_registry.async_get("sensor.magna3_differential_pressure")
    assert entry is not None
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_heat_meter_and_remote_sensor(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_connection: MockModbusConnection,
    patch_unit: None,
) -> None:
    """A second temperature sensor brings its reading and the heat meter."""
    unit = mock_connection.for_unit(1)
    unit.holding[336] = 30815  # remote temperature 2: 35.0 C
    unit.holding[353], unit.holding[354] = 0, 4200  # heat power 4200 W
    unit.holding[355] = 1223  # 12.23 K
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.magna3_remote_temperature_2").state == "35.0"
    assert hass.states.get("sensor.magna3_heat_power").state == "4200"
    assert hass.states.get("sensor.magna3_heat_energy").state == "0"
    assert hass.states.get("sensor.magna3_heat_differential_temperature").state == (
        "12.23"
    )


async def test_alarm(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
    freezer: FrozenDateTimeFactory,
) -> None:
    """An alarm raises the problem sensor and names the cause."""
    unit = mock_connection.for_unit(1)
    unit.holding[200] = 8896 | 1 << 10
    unit.holding[204] = 57  # dry running
    await _poll(hass, freezer)
    assert hass.states.get("binary_sensor.magna3_alarm_active").state == STATE_ON
    assert hass.states.get("sensor.magna3_alarm").state == "dry_running"
    assert hass.states.get("sensor.magna3_alarm_code").state == "57"


async def test_an_unlisted_code_reads_unknown(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
    freezer: FrozenDateTimeFactory,
) -> None:
    """A warning code the profile doesn't list leaves the decoded warning unknown."""
    mock_connection.for_unit(1).holding[205] = 250
    await _poll(hass, freezer)
    assert hass.states.get("sensor.magna3_warning").state == STATE_UNKNOWN
    assert hass.states.get("sensor.magna3_warning_code").state == "250"


async def test_us_customary_conversion(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, patch_unit: None
) -> None:
    """Native metric readings convert for a US-customary install."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    liquid = float(hass.states.get("sensor.magna3_liquid_temperature").state)
    assert liquid == pytest.approx(117.01, abs=0.01)
    head = float(hass.states.get("sensor.magna3_head").state)
    assert head == pytest.approx(11.65, abs=0.01)  # psi


async def test_unique_ids_keep_their_keys(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Unique IDs are the entry ID plus a stable key."""
    entry = entity_registry.async_get("sensor.magna3_flow")
    assert entry.unique_id == f"{init_integration.entry_id}_flow"


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    init_integration: MockConfigEntry,
) -> None:
    """Diagnostics carry the product and the raw blocks."""
    result = await get_diagnostics_for_config_entry(hass, hass_client, init_integration)
    assert result["product"] == "MAGNA3"
    assert result["registers"]["holding"]["202"] == 7
    assert result["failed"] == {}
