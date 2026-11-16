# Written by Claude, guided by Chris.
"""Small decoders shared by the components."""

from __future__ import annotations

from datetime import date
from enum import IntEnum


def code[E: IntEnum](raw: int | None, table: type[E]) -> E | int | None:
    """Look a code up in its table, keeping an unlisted code as a plain int."""
    if raw is None:
        return None
    try:
        return table(raw)
    except ValueError:
        return raw


def bcd(raw: int) -> int:
    """Decode a binary-coded-decimal word, e.g. 0x2018 -> 2018."""
    value = 0
    for shift in (12, 8, 4, 0):
        value = value * 10 + ((raw >> shift) & 0xF)
    return value


def bcd_pair(raw: int | None) -> str | None:
    """Decode a BCD word as two two-digit groups, e.g. 0x1001 -> "10.01"."""
    if raw is None:
        return None
    digits = f"{bcd(raw):04d}"
    return f"{digits[:2]}.{digits[2:]}"


def bcd_date(day_month: int | None, year: int | None) -> date | None:
    """Decode a BCD ddmm word and a BCD yyyy word, or None if either is unusable."""
    if day_month is None or year is None:
        return None
    ddmm = bcd(day_month)
    try:
        return date(bcd(year), ddmm % 100, ddmm // 100)
    except ValueError:
        return None
