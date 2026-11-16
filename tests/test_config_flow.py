"""Test the Grundfos config flow."""

# Written by Claude, guided by Chris.

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, _patch, patch

from modbus_connection import ModbusTcpParams, ModbusTimeoutError
from modbus_connection.mock import MockModbusConnection, MockModbusUnit
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.grundfos.const import DEFAULT_NAME, DOMAIN
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError

from . import MOCK_UNIQUE_ID, MOCK_USER_INPUT, seed_pump


def _patch_temporary_unit(connection: MockModbusConnection) -> _patch:
    """Stand in for async_get_temporary_unit, handing out a unit on connection."""

    @asynccontextmanager
    async def _get_temporary_unit(
        hass: HomeAssistant, params: ModbusTcpParams, unit_id: int
    ) -> AsyncIterator[MockModbusUnit]:
        yield connection.for_unit(unit_id)

    return patch(
        "custom_components.grundfos.config_flow.async_get_temporary_unit",
        side_effect=_get_temporary_unit,
    )


async def test_user_step_shows_form(hass: HomeAssistant) -> None:
    """The form renders with no errors before any input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_step_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """A pump that answers creates an entry titled with its product name."""
    connection = MockModbusConnection()
    seed_pump(connection.for_unit(1))

    with _patch_temporary_unit(connection):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_USER_INPUT,
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "MAGNA3"
    assert result["data"] == MOCK_USER_INPUT
    assert result["result"].unique_id == MOCK_UNIQUE_ID
    assert len(mock_setup_entry.mock_calls) == 1


async def test_an_unknown_product_gets_the_default_title(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """A unit family/type the profile doesn't name falls back to a generic title."""
    connection = MockModbusConnection()
    unit = connection.for_unit(1)
    seed_pump(unit)
    unit.holding[29] = 99

    with _patch_temporary_unit(connection):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_USER_INPUT,
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME


@pytest.mark.parametrize(
    "error", [ModbusTimeoutError("pump off"), HomeAssistantError("in use")]
)
async def test_user_step_cannot_connect_then_recovers(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, error: Exception
) -> None:
    """An unreachable module shows cannot_connect, and a retry succeeds."""
    connection = MockModbusConnection()
    seed_pump(connection.for_unit(1))
    connection.for_unit(1).fail_requests(error)

    with _patch_temporary_unit(connection):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_USER_INPUT,
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    connection.for_unit(1).fail_requests(None)
    with _patch_temporary_unit(connection):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_USER_INPUT
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_already_configured(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """The same host, port and unit ID aborts."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=MOCK_USER_INPUT,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
