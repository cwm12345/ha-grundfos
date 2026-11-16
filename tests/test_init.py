"""Test setting up and tearing down the Grundfos integration."""

# Written by Claude, guided by Chris.

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from modbus_connection import (
    IllegalDataAddressError,
    ModbusConnectionError,
    ModbusTimeoutError,
)
from modbus_connection.mock import MockModbusConnection
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.grundfos.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

LIQUID = "sensor.magna3_liquid_temperature"
PRODUCT_SENSOR = "binary_sensor.magna3_running"


async def test_setup_and_unload(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """The entry loads, creates entities, and unloads."""
    assert init_integration.state is ConfigEntryState.LOADED
    assert hass.states.get(LIQUID).state == "47.23"

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    assert init_integration.state is ConfigEntryState.NOT_LOADED


async def test_device_names_the_product(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """The device takes its model from the module's unit family and type."""
    device = device_registry.async_get_device({(DOMAIN, init_integration.entry_id)})
    assert device is not None
    assert device.manufacturer == "Grundfos"
    assert device.model == "MAGNA3"
    assert device.sw_version is None  # the module reports no software version


async def test_setup_retries_while_the_pump_is_off(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_connection: MockModbusConnection,
    patch_unit: None,
) -> None:
    """A module with no power (pump switched off) makes setup retry."""
    mock_connection.for_unit(1).fail_requests(ModbusTimeoutError())
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_a_refused_block_only_hides_its_entities(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
    freezer: FrozenDateTimeFactory,
) -> None:
    """A refused status block hides the status entities, not the data ones."""
    mock_connection.for_unit(1).fail_read(200, IllegalDataAddressError())
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(PRODUCT_SENSOR).state == STATE_UNAVAILABLE
    assert hass.states.get(LIQUID).state == "47.23"


async def test_pump_switched_off_and_back_on(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Readings go unavailable while the pump is off and return with it."""
    unit = mock_connection.for_unit(1)
    unit.fail_requests(ModbusConnectionError())
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(LIQUID).state == STATE_UNAVAILABLE
    assert init_integration.state is ConfigEntryState.LOADED

    unit.fail_requests(None)
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(LIQUID).state == "47.23"
