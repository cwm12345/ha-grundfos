"""Common fixtures for the Grundfos tests."""

# Written by Claude, guided by Chris.

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from modbus_connection.mock import MockModbusConnection
import pytest
from tests.common import MockConfigEntry

from homeassistant.components.grundfos.const import DOMAIN
from homeassistant.core import HomeAssistant

from . import MOCK_TITLE, MOCK_UNIQUE_ID, MOCK_USER_INPUT, seed_pump


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.grundfos.async_setup_entry",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_connection() -> MockModbusConnection:
    """Return a fake Modbus TCP connection seeded as the live MAGNA3."""
    connection = MockModbusConnection()
    seed_pump(connection.for_unit(1))
    return connection


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a Grundfos config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_UNIQUE_ID,
        data=MOCK_USER_INPUT,
        title=MOCK_TITLE,
        version=1,
    )


@pytest.fixture
def patch_unit(mock_connection: MockModbusConnection) -> Generator[None]:
    """Hand the integration units from the mock connection."""
    with patch(
        "homeassistant.components.grundfos.async_get_unit",
        side_effect=lambda hass, entry, params, unit_id: mock_connection.for_unit(
            unit_id
        ),
    ):
        yield


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, patch_unit: None
) -> MockConfigEntry:
    """Set up the integration against the mock connection."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    return mock_config_entry
