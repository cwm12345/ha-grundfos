# Written by Claude, guided by Chris.
"""Code tables from Grundfos' "Modbus for Grundfos pumps" functional profile."""

from __future__ import annotations

from enum import IntEnum, IntFlag

__all__ = [
    "NOT_AVAILABLE",
    "NOT_AVAILABLE_32",
    "AlarmCode",
    "ControlMode",
    "ControlSource",
    "FeedbackSensorUnit",
    "FlowEstimationState",
    "OperationMode",
    "PumpStatus",
]

NOT_AVAILABLE = 0xFFFF
"""What a 16-bit register holds when the pump doesn't supply that value."""

NOT_AVAILABLE_32 = 0xFFFFFFFF
"""The same for a 32-bit value split over two registers."""


class PumpStatus(IntFlag):
    """Register 00201, the pump's status bits."""

    LOW_FLOW_STOP = 1 << 0
    COPY_TO_LOCAL = 1 << 1
    MAX_FLOW_LIMIT_ENABLED = 1 << 2
    RESET_ALARM_ACK = 1 << 3
    SETPOINT_INFLUENCE = 1 << 4
    AT_MAX_POWER = 1 << 5
    ROTATING = 1 << 6
    COUNTERCLOCKWISE = 1 << 7
    """Rotation direction seen from the fan end."""
    REMOTE = 1 << 8
    """Controlled by the Modbus master rather than a local source."""
    ON = 1 << 9
    """Started. Not the same as rotating: a low-flow stop is on but still."""
    ALARM = 1 << 10
    WARNING = 1 << 11
    FORCED_TO_LOCAL = 1 << 12
    AT_MAX_SPEED = 1 << 13
    AT_MIN_SPEED = 1 << 15


class ControlMode(IntEnum):
    """Register 00203, the control mode in use."""

    CONSTANT_SPEED = 0
    CONSTANT_FREQUENCY = 1
    CONSTANT_HEAD = 3
    CONSTANT_PRESSURE = 4
    CONSTANT_DIFFERENTIAL_PRESSURE = 5
    PROPORTIONAL_PRESSURE = 6
    CONSTANT_FLOW = 7
    CONSTANT_TEMPERATURE = 8
    CONSTANT_DIFFERENTIAL_TEMPERATURE = 9
    CONSTANT_LEVEL = 10
    AUTOADAPT = 128
    FLOWADAPT = 129
    CLOSED_LOOP_SENSOR = 130
    AUTOADAPT_CONSTANT_PRESSURE = 131


class OperationMode(IntEnum):
    """Register 00204, the operating mode in use."""

    AUTO_CONTROL = 0
    OPEN_LOOP_MIN = 4
    """Running at minimum speed."""
    OPEN_LOOP_MAX = 6
    """Running at maximum speed."""
    USER_CURVE = 7
    STOP_BUTTON = 8
    HAND_MODE = 9


class FeedbackSensorUnit(IntEnum):
    """Register 00209, the unit of the closed-loop feedback sensor."""

    BAR = 0
    MBAR = 1
    M = 2
    KPA = 3
    PSI = 4
    FT = 5
    M3_PER_H = 6
    M3_PER_S = 7
    L_PER_S = 8
    GPM = 9
    CELSIUS = 10
    FAHRENHEIT = 11
    PERCENT = 12
    KELVIN = 13
    WATT = 14


class FlowEstimationState(IntEnum):
    """Register 00221, whether the flow estimate is within its valid range."""

    WITHIN_RANGE = 0
    BELOW_RANGE = 1
    ABOVE_RANGE = 2


class ControlSource(IntEnum):
    """Register 00225, what is controlling the pump."""

    DISPLAY = 1
    BUS = 2
    GO_APP = 3
    DIGITAL_INPUT = 4
    OFF_BUTTON = 5


class AlarmCode(IntEnum):
    """Registers 00205 (alarm) and 00206 (warning): the cause, or NONE.

    The profile's full list; not every code applies to every pump.
    """

    NONE = 0
    LEAKAGE_CURRENT = 1
    MISSING_PHASE = 2
    EXTERNAL_FAULT_SIGNAL = 3
    TOO_MANY_RESTARTS = 4
    TOO_MANY_HARDWARE_SHUTDOWNS = 7
    DC_LINK_PROTECTION = 14
    OTHER = 16
    TURBINE_OPERATION = 29
    CHANGE_BEARINGS = 30
    CHANGE_VARISTORS = 31
    OVERVOLTAGE = 32
    UNDERVOLTAGE = 40
    UNDERVOLTAGE_TRANSIENT = 41
    CUT_IN_FAULT = 42
    VOLTAGE_ASYMMETRY = 45
    OVERLOAD = 48
    OVERCURRENT = 49
    MOTOR_PROTECTION_SHUTDOWN = 50
    BLOCKED_MOTOR_OR_PUMP = 51
    MOTOR_PROTECTION_3_SECOND_LIMIT = 54
    MOTOR_CURRENT_PROTECTION = 55
    UNDERLOAD = 56
    DRY_RUNNING = 57
    LOW_INPUT_POWER = 60
    SAFE_TORQUE_OFF = 62
    OVERTEMPERATURE = 64
    MOTOR_TEMPERATURE_1 = 65
    CONTROL_ELECTRONICS_TEMPERATURE_HIGH = 66
    FREQUENCY_CONVERTER_TEMPERATURE_HIGH = 67
    WATER_TEMPERATURE_HIGH = 68
    MOTOR_THERMAL_RELAY_2 = 70
    HARDWARE_FAULT_TYPE_1 = 72
    HARDWARE_SHUTDOWN = 73
    INTERNAL_COMMUNICATION_FAULT = 76
    TWIN_HEAD_COMMUNICATION_FAULT = 77
    HARDWARE_FAULT_TYPE_2 = 80
    FE_PARAMETER_VERIFICATION_ERROR = 83
    MEMORY_ACCESS_ERROR = 84
    BE_PARAMETER_VERIFICATION_ERROR = 85
    SENSOR_FAULT = 88
    FEEDBACK_SENSOR_1_SIGNAL_FAULT = 89
    TEMPERATURE_1_SENSOR_SIGNAL_FAULT = 91
    SENSOR_2_SIGNAL_FAULT = 93
    SETPOINT_SIGNAL_OUT_OF_RANGE = 96
    RECTIFIER_PROTECTION = 105
    INVERTER_PROTECTION = 106
    GDS_SENSOR_SIGNAL_FAULT = 135
    BEARING_TEMPERATURE_HIGH_DRIVE_END = 148
    BEARING_TEMPERATURE_HIGH_NON_DRIVE_END = 149
    INRUSH_FAULT = 155
    FREQUENCY_CONVERTER_COMMUNICATION_FAULT = 156
    REAL_TIME_CLOCK_ERROR = 157
    CIM_LOST_CONNECTION = 159
    SENSOR_SUPPLY_FAULT_5V = 161
    SENSOR_SUPPLY_FAULT_24V = 162
    MOTOR_PROTECTION_MEASUREMENT_FAULT = 163
    LIQTEC_SENSOR_SIGNAL_FAULT = 164
    ANALOG_INPUT_1_SIGNAL_FAULT = 165
    ANALOG_INPUT_2_SIGNAL_FAULT = 166
    ANALOG_INPUT_3_SIGNAL_FAULT = 167
    TEMPERATURE_SENSOR_2_SIGNAL_FAULT = 175
    TEMPERATURE_SENSOR_3_SIGNAL_FAULT = 176
    SENSOR_1_LIMIT_EXCEEDED = 190
    SENSOR_2_LIMIT_EXCEEDED = 191
    NON_RETURN_VALVE_FAULT = 209
    SOFT_PRESSURE_BUILDUP_TIMEOUT = 215
    LUBRICATE_BEARINGS = 240
    MOTOR_PHASE_FAILURE = 241
    MOTOR_MODEL_RECOGNITION_FAILED = 242
