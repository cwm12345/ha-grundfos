# Written by Claude, guided by Chris.
"""The top-level object for a Grundfos pump with a CIM Modbus module."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from modbus_connection.model import Device, Raw, UpdateReport

from .cim import Cim
from .data import Data
from .status import Status

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

__all__ = ["COMPONENTS", "GrundfosPump"]

COMPONENTS: tuple[str, ...] = ("cim", "status", "data")
"""The three read-only blocks; each is one block read."""


class GrundfosPump(Device):
    """A Grundfos pump read through a CIM 200 / CIM 500 Modbus module.

    Follows Grundfos' "Modbus for Grundfos pumps" functional profile, which
    covers MAGNA3 circulators, E-pumps with MGE motors (TPE, NBE, CRE and so
    on) and CUE drives. Hand it a ``ModbusUnit``; it owns no connection.
    A CIM 500 speaks Modbus TCP (rotary switch at 1) and ignores the unit ID;
    a CIM 200 speaks Modbus RTU.

    The module is powered by the pump, so it is unreachable whenever the pump
    is switched off at its supply.
    """

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit)
        self.cim = Cim(unit)
        self.status = Status(unit)
        self.data = Data(unit)

    async def async_update(self) -> UpdateReport:
        """Refresh all three blocks in one report."""
        return await self.async_poll(COMPONENTS)

    async def async_read_raw(self, names: Iterable[str] | None = None) -> Raw:
        """Every register this pump reads, undecoded, for diagnostics."""
        return await super().async_read_raw(COMPONENTS if names is None else names)
