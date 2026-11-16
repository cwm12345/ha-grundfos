"""Sensors for Grundfos pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum

from grundfos_modbus import (
    AlarmCode,
    ControlMode,
    ControlSource,
    FlowEstimationState,
    GrundfosPump,
    OperationMode,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfLength,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import GrundfosConfigEntry
from .entity import GrundfosEntity, GrundfosEntityDescription

PARALLEL_UPDATES = 0

_DIAGNOSTIC = EntityCategory.DIAGNOSTIC
_MEASUREMENT = SensorStateClass.MEASUREMENT
_TOTAL_INCREASING = SensorStateClass.TOTAL_INCREASING


@dataclass(frozen=True, kw_only=True)
class GrundfosSensorDescription(SensorEntityDescription, GrundfosEntityDescription):
    """Describe a Grundfos sensor."""

    value_fn: Callable[[GrundfosPump], StateType]
    exists_fn: Callable[[GrundfosPump], bool] = lambda _: True


def _data(
    key: str,
    value_fn: Callable[[GrundfosPump], StateType],
    *,
    optional: bool = False,
    **kwargs: object,
) -> GrundfosSensorDescription:
    """Describe a pump data reading.

    ``optional`` readings depend on a sensor or pump type; they get an entity
    only when the pump supplied a value on the first poll.
    """
    return GrundfosSensorDescription(
        key=key,
        translation_key=key,
        component="data",
        value_fn=value_fn,
        exists_fn=(lambda d: value_fn(d) is not None) if optional else lambda _: True,
        **kwargs,  # type: ignore[arg-type]
    )


def _temperature(
    key: str, value_fn: Callable[[GrundfosPump], StateType], **kwargs: object
) -> GrundfosSensorDescription:
    return _data(
        key,
        value_fn,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=_MEASUREMENT,
        suggested_display_precision=1,
        **kwargs,
    )


def _pressure(
    key: str, value_fn: Callable[[GrundfosPump], StateType], **kwargs: object
) -> GrundfosSensorDescription:
    return _data(
        key,
        value_fn,
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.BAR,
        state_class=_MEASUREMENT,
        suggested_display_precision=2,
        **kwargs,
    )


def _flow(
    key: str, value_fn: Callable[[GrundfosPump], StateType], **kwargs: object
) -> GrundfosSensorDescription:
    return _data(
        key,
        value_fn,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=_MEASUREMENT,
        suggested_display_precision=1,
        **kwargs,
    )


def _percent(
    key: str,
    value_fn: Callable[[GrundfosPump], StateType],
    *,
    component: str = "data",
    **kwargs: object,
) -> GrundfosSensorDescription:
    return GrundfosSensorDescription(
        key=key,
        translation_key=key,
        component=component,
        native_unit_of_measurement=PERCENTAGE,
        state_class=_MEASUREMENT,
        value_fn=value_fn,
        **kwargs,  # type: ignore[arg-type]
    )


def _enum[E: IntEnum](
    key: str,
    table: type[E],
    value_fn: Callable[[GrundfosPump], E | int | None],
    *,
    entity_category: EntityCategory | None = None,
) -> GrundfosSensorDescription:
    """Describe a decoded code; one the profile doesn't list reads unknown."""

    def value(device: GrundfosPump) -> str | None:
        code = value_fn(device)
        return code.name.lower() if isinstance(code, table) else None

    return GrundfosSensorDescription(
        key=key,
        translation_key=key,
        component="status",
        device_class=SensorDeviceClass.ENUM,
        options=[member.name.lower() for member in table],
        entity_category=entity_category,
        value_fn=value,
    )


def _raw(
    key: str, component: str, value_fn: Callable[[GrundfosPump], StateType]
) -> GrundfosSensorDescription:
    """Describe a raw code, for diagnostics."""
    return GrundfosSensorDescription(
        key=key,
        translation_key=key,
        component=component,
        entity_category=_DIAGNOSTIC,
        value_fn=value_fn,
    )


def _has_heat_meter(device: GrundfosPump) -> bool:
    return device.data.has_heat_meter


# Keys are part of each entity's unique ID; keep them stable.
SENSOR_DESCRIPTIONS: tuple[GrundfosSensorDescription, ...] = (
    # What the pump is doing.
    _temperature("liquid_temperature", lambda d: d.data.liquid_temperature),
    _flow("flow", lambda d: d.data.volume_flow),
    _pressure("head", lambda d: d.data.head),
    _data(
        "power",
        lambda d: d.data.power,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=_MEASUREMENT,
    ),
    _data(
        "energy",
        lambda d: d.data.energy,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=_TOTAL_INCREASING,
    ),
    _data(
        "speed",
        lambda d: d.data.speed,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=_MEASUREMENT,
    ),
    _percent("relative_performance", lambda d: d.data.relative_performance),
    _enum("control_mode", ControlMode, lambda d: d.status.control_mode),
    _enum("operation_mode", OperationMode, lambda d: d.status.operation_mode),
    _enum("alarm", AlarmCode, lambda d: d.status.alarm),
    _enum("warning", AlarmCode, lambda d: d.status.warning),
    # Settings and internals.
    _percent(
        "user_setpoint", lambda d: d.data.user_setpoint, entity_category=_DIAGNOSTIC
    ),
    _percent(
        "actual_setpoint",
        lambda d: d.data.actual_setpoint,
        entity_category=_DIAGNOSTIC,
    ),
    _percent(
        "process_feedback",
        lambda d: d.status.process_feedback,
        component="status",
        entity_category=_DIAGNOSTIC,
    ),
    _enum(
        "control_source",
        ControlSource,
        lambda d: d.status.control_source,
        entity_category=_DIAGNOSTIC,
    ),
    _enum(
        "flow_estimation",
        FlowEstimationState,
        lambda d: d.status.flow_estimation_state,
        entity_category=_DIAGNOSTIC,
    ),
    _temperature(
        "electronics_temperature",
        lambda d: d.data.electronics_temperature,
        entity_category=_DIAGNOSTIC,
    ),
    _data(
        "motor_current",
        lambda d: d.data.motor_current,
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=_MEASUREMENT,
        entity_category=_DIAGNOSTIC,
    ),
    _data(
        "dc_link_voltage",
        lambda d: d.data.dc_link_voltage,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=_MEASUREMENT,
        entity_category=_DIAGNOSTIC,
    ),
    _data(
        "frequency",
        lambda d: d.data.frequency,
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=_MEASUREMENT,
        entity_category=_DIAGNOSTIC,
    ),
    _data(
        "specific_energy",
        lambda d: d.data.specific_energy,
        native_unit_of_measurement="Wh/m³",
        state_class=_MEASUREMENT,
        entity_category=_DIAGNOSTIC,
    ),
    _data(
        "operating_hours",
        lambda d: d.data.operating_hours,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=_TOTAL_INCREASING,
        entity_category=_DIAGNOSTIC,
    ),
    _data(
        "powered_hours",
        lambda d: d.data.powered_hours,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=_TOTAL_INCREASING,
        entity_category=_DIAGNOSTIC,
    ),
    _data(
        "starts",
        lambda d: d.data.starts,
        state_class=_TOTAL_INCREASING,
        entity_category=_DIAGNOSTIC,
    ),
    _data(
        "pumped_volume",
        lambda d: d.data.volume_1,
        optional=True,
        device_class=SensorDeviceClass.VOLUME,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=_TOTAL_INCREASING,
        entity_category=_DIAGNOSTIC,
    ),
    _flow(
        "max_flow_limit",
        lambda d: d.data.max_flow_limit,
        optional=True,
        entity_category=_DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _raw("alarm_code", "status", lambda d: d.status.alarm_code),
    _raw("warning_code", "status", lambda d: d.status.warning_code),
    # Readings that need a sensor or a particular pump type.
    _pressure(
        "differential_pressure",
        lambda d: d.data.differential_pressure,
        optional=True,
        entity_registry_enabled_default=False,
    ),
    _pressure("inlet_pressure", lambda d: d.data.inlet_pressure, optional=True),
    _pressure("outlet_pressure", lambda d: d.data.outlet_pressure, optional=True),
    _pressure("remote_pressure_1", lambda d: d.data.remote_pressure_1, optional=True),
    _pressure("remote_pressure_2", lambda d: d.data.remote_pressure_2, optional=True),
    _flow("remote_flow", lambda d: d.data.remote_flow, optional=True),
    _temperature(
        "remote_temperature_1", lambda d: d.data.remote_temperature_1, optional=True
    ),
    _temperature(
        "remote_temperature_2", lambda d: d.data.remote_temperature_2, optional=True
    ),
    _temperature(
        "ambient_temperature", lambda d: d.data.ambient_temperature, optional=True
    ),
    _temperature(
        "motor_temperature",
        lambda d: d.data.motor_temperature,
        optional=True,
        entity_category=_DIAGNOSTIC,
    ),
    _temperature(
        "power_electronics_temperature",
        lambda d: d.data.power_electronics_temperature,
        optional=True,
        entity_category=_DIAGNOSTIC,
    ),
    _data(
        "feed_tank_level",
        lambda d: d.data.feed_tank_level,
        optional=True,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        state_class=_MEASUREMENT,
    ),
    _data(
        "motor_voltage",
        lambda d: d.data.motor_voltage,
        optional=True,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=_MEASUREMENT,
        entity_category=_DIAGNOSTIC,
    ),
    _percent(
        "load",
        lambda d: d.data.load,
        exists_fn=lambda d: d.data.load is not None,
        entity_category=_DIAGNOSTIC,
    ),
    # The heat meter, when the pump has a second temperature to work from.
    GrundfosSensorDescription(
        key="heat_power",
        translation_key="heat_power",
        component="data",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=_MEASUREMENT,
        value_fn=lambda d: d.data.heat_power,
        exists_fn=_has_heat_meter,
    ),
    GrundfosSensorDescription(
        key="heat_energy",
        translation_key="heat_energy",
        component="data",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=_TOTAL_INCREASING,
        value_fn=lambda d: d.data.heat_energy_1,
        exists_fn=_has_heat_meter,
    ),
    GrundfosSensorDescription(
        key="heat_differential_temperature",
        translation_key="heat_differential_temperature",
        component="data",
        native_unit_of_measurement=UnitOfTemperature.KELVIN,
        state_class=_MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: d.data.heat_differential_temperature,
        exists_fn=_has_heat_meter,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrundfosConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Grundfos sensors."""
    device = entry.runtime_data.device
    async_add_entities(
        GrundfosSensor(entry, description)
        for description in SENSOR_DESCRIPTIONS
        if description.exists_fn(device)
    )


class GrundfosSensor(GrundfosEntity, SensorEntity):
    """A pump reading."""

    entity_description: GrundfosSensorDescription

    @property
    def native_value(self) -> StateType:
        """The value from the latest poll."""
        return self.entity_description.value_fn(self.coordinator.device)
