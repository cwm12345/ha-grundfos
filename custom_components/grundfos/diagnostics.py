"""Diagnostics for Grundfos pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from typing import Any

from modbus_connection import ModbusError

from homeassistant.core import HomeAssistant

from .coordinator import GrundfosConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: GrundfosConfigEntry
) -> dict[str, Any]:
    """Return the raw register blocks and the latest poll's outcome.

    The module holds no serial number or other personal information, so
    nothing needs redacting from the registers. The module's address is left
    out.
    """
    coordinator = entry.runtime_data
    device = coordinator.device
    try:
        registers: dict[str, Any] = await device.async_read_raw()
    except ModbusError as err:
        registers = {"error": str(err) or type(err).__name__}
    return {
        "product": device.cim.product,
        "updated": sorted(coordinator.data.updated),
        "failed": {k: str(v) for k, v in coordinator.data.failed.items()},
        "registers": registers,
    }
