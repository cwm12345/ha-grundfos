# Written by Claude, guided by Chris.
"""The CIM status block: what the module is attached to, and its link counters."""

from __future__ import annotations

from datetime import date

from modbus_connection.model import Component, integer, uint32

from ._decode import bcd_date, bcd_pair
from .enums import NOT_AVAILABLE, NOT_AVAILABLE_32

__all__ = ["PRODUCTS", "Cim"]

_NA = NOT_AVAILABLE

PRODUCTS: dict[tuple[int, int], str] = {
    (1, 5): "UPE, 3-phase",
    (1, 7): "MAGNA, 1-phase",
    (1, 9): "MAGNA, 1-phase, small",
    (1, 10): "MAGNA3",
    (2, 2): "MGE, 1-phase, model C or earlier",
    (2, 3): "MGE, 3-phase, model D",
    (2, 4): "MGE, 3-phase, large, model F",
    (2, 5): "CUE",
    (2, 6): "MGE, 3-phase, model G",
    (2, 7): "MGE, model H/I/J",
    (2, 8): "CUE II",
    (2, 9): "MGE, model K",
    (38, 10): "MAGNA3-D",
}
"""Product names by (unit family, unit type), from the profile's table."""


class Cim(Component):
    """Registers 00021-00037, read in one block.

    The communication module's own status: its GENIbus link to the pump, its
    firmware, and the unit family and type of the product it's fitted to.
    """

    register_ranges = ((20, 36),)

    genibus_crc_errors = integer(20, signed=False)
    """00021, CRC errors on the module's link to the pump."""
    genibus_data_errors = integer(21, signed=False)
    """00022, data errors on the module's link to the pump."""
    version_number_raw = integer(22, signed=False, nan=_NA)
    """00023, the module's Grundfos version number, BCD. See ``version``."""
    modbus_address = integer(23, signed=False)
    """00024. Modbus TCP ignores it."""
    genibus_tx_count = uint32(24, nan=NOT_AVAILABLE_32)
    """00025-00026, telegrams sent to the pump."""
    genibus_rx_count = uint32(26, nan=NOT_AVAILABLE_32)
    """00027-00028, telegrams received from the pump."""
    unit_family = integer(29, signed=False, nan=_NA)
    """00030."""
    unit_type = integer(30, signed=False, nan=_NA)
    """00031."""
    unit_version = integer(31, signed=False, nan=_NA)
    """00032."""
    software_version_high = integer(33, signed=False, nan=_NA)
    """00034, product software version digits 1-4, BCD."""
    software_version_low = integer(34, signed=False, nan=_NA)
    """00035, product software version digits 5-8, BCD."""
    software_day_month = integer(35, signed=False, nan=_NA)
    """00036, product software date, BCD ddmm."""
    software_year = integer(36, signed=False, nan=_NA)
    """00037, product software year, BCD."""

    @property
    def product(self) -> str | None:
        """The product the module is fitted to, if the profile names it."""
        family, kind = self.unit_family, self.unit_type
        if family is None or kind is None:
            return None
        return PRODUCTS.get((family, kind))

    @property
    def version(self) -> str | None:
        """The module's version number, e.g. "10.01"."""
        return bcd_pair(self.version_number_raw)

    @property
    def software_version(self) -> str | None:
        """The product's software version as aa.bb.cc.dd, or None if unreported."""
        high, low = self.software_version_high, self.software_version_low
        if not high and not low:
            return None
        return f"{bcd_pair(high or 0)}.{bcd_pair(low or 0)}"

    @property
    def software_date(self) -> date | None:
        """The product's software date."""
        return bcd_date(self.software_day_month, self.software_year)
