# Written by Claude, guided by Chris.
"""The pump status block: state bits, modes, alarm and warning codes, limits."""

from __future__ import annotations

from modbus_connection.model import Component, gauge, integer

from ._decode import code
from .enums import (
    NOT_AVAILABLE,
    AlarmCode,
    ControlMode,
    ControlSource,
    FeedbackSensorUnit,
    FlowEstimationState,
    OperationMode,
    PumpStatus,
)

__all__ = ["Status"]

_NA = NOT_AVAILABLE


class Status(Component):
    """Registers 00201-00225, read in one block."""

    register_ranges = ((200, 224),)

    flags_raw = integer(200, signed=False, nan=_NA)
    """00201, the status bits. See ``flags``."""
    process_feedback = gauge(201, 0.01, signed=False, nan=_NA, unit="%")
    """00202, closed loop: % of the feedback sensor's range; open loop: % of
    performance."""
    control_mode_raw = integer(202, signed=False, nan=_NA)
    """00203. See ``control_mode``."""
    operation_mode_raw = integer(203, signed=False, nan=_NA)
    """00204. See ``operation_mode``."""
    alarm_code = integer(204, signed=False, nan=_NA)
    """00205, raw. See ``alarm``."""
    warning_code = integer(205, signed=False, nan=_NA)
    """00206, raw. See ``warning``."""
    feedback_sensor_unit_raw = integer(208, signed=False, nan=_NA)
    """00209. See ``feedback_sensor_unit``."""
    feedback_sensor_min = integer(209, signed=False, nan=_NA)
    """00210, in ``feedback_sensor_unit``."""
    feedback_sensor_max = integer(210, signed=False, nan=_NA)
    """00211, in ``feedback_sensor_unit``."""
    nominal_frequency = gauge(211, 0.1, signed=False, nan=_NA, unit="Hz")
    """00212."""
    min_frequency = gauge(212, 0.01, signed=False, nan=_NA, unit="%")
    """00213, % of nominal frequency."""
    max_frequency = gauge(213, 0.01, signed=False, nan=_NA, unit="%")
    """00214, % of nominal frequency."""
    setpoint_range_min = gauge(214, 0.01, signed=False, nan=_NA, unit="%")
    """00215, % of the sensor maximum."""
    setpoint_range_max = gauge(215, 0.01, signed=False, nan=_NA, unit="%")
    """00216, % of the sensor maximum."""
    flow_estimation_state_raw = integer(220, signed=False, nan=_NA)
    """00221. See ``flow_estimation_state``."""
    kp = gauge(221, 0.1, signed=False, nan=_NA)
    """00222, the controller's proportional gain."""
    ti = gauge(222, 0.1, signed=False, nan=_NA, unit="s")
    """00223, the controller's integral action time."""
    direct_control = integer(223, signed=False, nan=_NA)
    """00224, 1 for direct control, 0 for inverse."""
    control_source_raw = integer(224, signed=False, nan=_NA)
    """00225. See ``control_source``."""

    @property
    def flags(self) -> PumpStatus | None:
        """The status bits that are set."""
        raw = self.flags_raw
        return None if raw is None else PumpStatus(raw)

    def flag(self, which: PumpStatus) -> bool | None:
        """Whether one status bit is set."""
        flags = self.flags
        return None if flags is None else which in flags

    @property
    def control_mode(self) -> ControlMode | int | None:
        """The control mode; one the profile doesn't list stays an int."""
        return code(self.control_mode_raw, ControlMode)

    @property
    def operation_mode(self) -> OperationMode | int | None:
        """The operating mode; one the profile doesn't list stays an int."""
        return code(self.operation_mode_raw, OperationMode)

    @property
    def alarm(self) -> AlarmCode | int | None:
        """The alarm cause, AlarmCode.NONE when there is no alarm."""
        return code(self.alarm_code, AlarmCode)

    @property
    def warning(self) -> AlarmCode | int | None:
        """The warning cause, AlarmCode.NONE when there is no warning."""
        return code(self.warning_code, AlarmCode)

    @property
    def feedback_sensor_unit(self) -> FeedbackSensorUnit | int | None:
        """The unit of the feedback sensor and its min/max registers."""
        return code(self.feedback_sensor_unit_raw, FeedbackSensorUnit)

    @property
    def flow_estimation_state(self) -> FlowEstimationState | int | None:
        """Whether the pump's flow estimate is within its valid range."""
        return code(self.flow_estimation_state_raw, FlowEstimationState)

    @property
    def control_source(self) -> ControlSource | int | None:
        """What is controlling the pump."""
        return code(self.control_source_raw, ControlSource)
