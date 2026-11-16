"""Data update coordinator for Grundfos pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from datetime import timedelta
import logging

from modbus_connection import ModbusError
from modbus_connection.model import UpdateReport

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MANUFACTURER, SCAN_INTERVAL
from .grundfos_modbus import GrundfosPump

_LOGGER = logging.getLogger(__name__)

type GrundfosConfigEntry = ConfigEntry[GrundfosCoordinator]


class GrundfosCoordinator(DataUpdateCoordinator[UpdateReport]):
    """Poll the three register blocks of one pump."""

    config_entry: GrundfosConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: GrundfosConfigEntry, device: GrundfosPump
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.device = device
        self._failed: frozenset[str] = frozenset()

    @property
    def device_info(self) -> DeviceInfo:
        """The pump, named for the product the module reports.

        The module reports no serial number; the config entry is its identity.
        """
        cim = self.device.cim
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name=self.config_entry.title,
            manufacturer=MANUFACTURER,
            model=cim.product,
            sw_version=cim.software_version,
        )

    async def _async_update_data(self) -> UpdateReport:
        try:
            report = await self.device.async_update()
        except ModbusError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="modbus_error",
                translation_placeholders={"error": str(err) or type(err).__name__},
            ) from err
        if not report.updated:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="no_component_answered",
            ) from ExceptionGroup(
                "every component failed to refresh", list(report.failed.values())
            )

        for name in sorted(report.failed.keys() - self._failed):
            _LOGGER.warning(
                "%s: %s failed to refresh: %s", self.name, name, report.failed[name]
            )
        for name in sorted(self._failed - report.failed.keys()):
            _LOGGER.info("%s: %s is available again", self.name, name)
        self._failed = frozenset(report.failed)
        return report
