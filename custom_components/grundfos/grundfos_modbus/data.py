# Written by Claude, guided by Chris.
"""The pump data block: measured values, counters and the heat meter."""

from __future__ import annotations

from modbus_connection.model import Component, NumberField, gauge, integer, uint32

from .enums import NOT_AVAILABLE, NOT_AVAILABLE_32

__all__ = ["Data"]

_NA = NOT_AVAILABLE
_NA32 = NOT_AVAILABLE_32


def _celsius(address: int) -> NumberField[float]:
    """A temperature sent in hundredths of a kelvin, read as °C."""
    return gauge(address, 0.01, offset=-273.15, signed=False, nan=_NA, unit="°C")


def _bar(address: int, *, offset: float = 0.0) -> NumberField[float]:
    return gauge(address, 0.001, offset=offset, signed=False, nan=_NA, unit="bar")


def _flow(address: int) -> NumberField[float]:
    return gauge(address, 0.1, signed=False, nan=_NA, unit="m³/h")


def _percent(address: int) -> NumberField[float]:
    return gauge(address, 0.01, signed=False, nan=_NA, unit="%")


class Data(Component):
    """Registers 00301-00362, read in one block.

    A register the pump doesn't supply reads 0xFFFF (0xFFFFFFFF for a 32-bit
    value) and decodes to None. Which ones a pump supplies depends on its type
    and on which sensors are fitted; the profile marks a MAGNA3 as always
    supplying head, flow, performance, speed, frequency, setpoint, current,
    DC-link voltage, power, electronics and liquid temperature, specific
    energy, the hour/energy/start counters, differential pressure, the clock,
    the flow limit and pumped volume. The heat meter values need a second
    temperature sensor.
    """

    register_ranges = ((300, 361),)

    head = _bar(300)
    """00301, head (pressure across the pump)."""
    volume_flow = _flow(301)
    """00302."""
    relative_performance = _percent(302)
    """00303, % of maximum performance."""
    speed = integer(303, signed=False, nan=_NA, unit="rpm")
    """00304."""
    frequency = gauge(304, 0.1, signed=False, nan=_NA, unit="Hz")
    """00305, the control signal applied to the motor."""
    digital_inputs = integer(305, signed=False, nan=_NA)
    """00306, external digital inputs, one bit each."""
    digital_outputs = integer(306, signed=False, nan=_NA)
    """00307, external digital outputs (relays), one bit each."""
    actual_setpoint = _percent(307)
    """00308, closed loop: % of the sensor maximum; open loop: % of nominal
    frequency."""
    motor_current = gauge(308, 0.1, signed=False, nan=_NA, unit="A")
    """00309."""
    dc_link_voltage = gauge(309, 0.1, signed=False, nan=_NA, unit="V")
    """00310."""
    motor_voltage = gauge(310, 0.1, signed=False, nan=_NA, unit="V")
    """00311."""
    power = uint32(311, nan=_NA32, unit="W")
    """00312-00313, power drawn."""
    remote_flow = _flow(313)
    """00314, from an external flow sensor."""
    inlet_pressure = _bar(314, offset=-1.0)
    """00315, relative to atmosphere."""
    remote_pressure_1 = _bar(315)
    """00316, from an external sensor."""
    feed_tank_level = gauge(316, 0.01, offset=-100.0, signed=False, nan=_NA, unit="m")
    """00317."""
    power_electronics_temperature = _celsius(317)
    """00318, the frequency converter."""
    motor_temperature = _celsius(318)
    """00319, motor winding."""
    remote_temperature_1 = _celsius(319)
    """00320, an external sensor."""
    electronics_temperature = _celsius(320)
    """00321, the pump's electronics."""
    liquid_temperature = _celsius(321)
    """00322, the pumped liquid."""
    bearing_temperature_drive_end = _celsius(322)
    """00323."""
    bearing_temperature_non_drive_end = _celsius(323)
    """00324."""
    aux_sensor_input = _percent(324)
    """00325."""
    specific_energy = integer(325, signed=False, nan=_NA, unit="Wh/m³")
    """00326, energy per volume pumped."""
    operating_hours = uint32(326, nan=_NA32, unit="h")
    """00327-00328, hours running."""
    powered_hours = uint32(328, nan=_NA32, unit="h")
    """00329-00330, hours powered."""
    torque = gauge(330, 0.1, signed=False, nan=_NA, unit="N·m")
    """00331."""
    energy = uint32(331, nan=_NA32, unit="kWh")
    """00332-00333, lifetime energy drawn."""
    starts = uint32(333, nan=_NA32)
    """00334-00335, lifetime starts."""
    remote_temperature_2 = _celsius(336)
    """00337, an external sensor."""
    user_setpoint = _percent(337)
    """00338, the setpoint chosen on the pump."""
    differential_pressure = _bar(338)
    """00339, between the pump flanges."""
    outlet_pressure = _bar(339)
    """00340."""
    remote_pressure_2 = _bar(340)
    """00341."""
    load = _percent(341)
    """00342, motor current as % of rated."""
    clock = uint32(342, nan=_NA32, unit="s")
    """00343-00344, the pump's clock in Unix seconds."""
    max_flow_limit = _flow(344)
    """00345, the FLOWLIMIT in force."""
    remote_differential_temperature = gauge(345, 0.01, signed=False, nan=_NA, unit="K")
    """00346."""
    inlet_differential_pressure = _bar(346)
    """00347."""
    outlet_differential_pressure = _bar(347)
    """00348."""
    remote_differential_pressure = _bar(348)
    """00349."""
    storage_tank_level = gauge(
        349, 0.01, offset=-100.0, signed=False, nan=_NA, unit="m"
    )
    """00350."""
    ambient_temperature = _celsius(350)
    """00351."""
    heat_energy_1 = uint32(351, nan=_NA32, unit="kWh")
    """00352-00353, heat delivered in flow direction 1."""
    heat_power = uint32(353, nan=_NA32, unit="W")
    """00354-00355, heat being delivered now."""
    heat_differential_temperature = gauge(355, 0.01, signed=False, nan=_NA, unit="K")
    """00356, the supply/return difference the heat meter uses."""
    volume_1 = uint32(356, scale=0.01, nan=_NA32, unit="m³")
    """00357-00358, volume pumped in flow direction 1."""
    heat_energy_2 = uint32(358, nan=_NA32, unit="kWh")
    """00359-00360, heat delivered in flow direction 2."""
    volume_2 = uint32(360, scale=0.01, nan=_NA32, unit="m³")
    """00361-00362, volume pumped in flow direction 2."""

    @property
    def has_heat_meter(self) -> bool:
        """Whether the pump is computing heat power.

        It needs flow plus a supply/return temperature difference. Without one,
        the heat energy counters still read 0 rather than not available.
        """
        return self.heat_power is not None
