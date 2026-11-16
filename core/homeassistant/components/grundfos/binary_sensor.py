"""Binary sensors for Grundfos pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from grundfos_modbus import GrundfosPump, PumpStatus

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GrundfosConfigEntry
from .entity import GrundfosEntity, GrundfosEntityDescription

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class GrundfosBinarySensorDescription(
    BinarySensorEntityDescription, GrundfosEntityDescription
):
    """Describe a Grundfos binary sensor."""

    value_fn: Callable[[GrundfosPump], bool | None]


def _flag(
    key: str,
    which: PumpStatus,
    *,
    device_class: BinarySensorDeviceClass | None = None,
    entity_category: EntityCategory | None = None,
) -> GrundfosBinarySensorDescription:
    """Describe one status bit of register 00201."""
    return GrundfosBinarySensorDescription(
        key=key,
        translation_key=key,
        component="status",
        device_class=device_class,
        entity_category=entity_category,
        value_fn=lambda d: d.status.flag(which),
    )


_DIAGNOSTIC = EntityCategory.DIAGNOSTIC
_PROBLEM = BinarySensorDeviceClass.PROBLEM

BINARY_SENSOR_DESCRIPTIONS: tuple[GrundfosBinarySensorDescription, ...] = (
    _flag("running", PumpStatus.ROTATING, device_class=BinarySensorDeviceClass.RUNNING),
    _flag("started", PumpStatus.ON),
    _flag("alarm_active", PumpStatus.ALARM, device_class=_PROBLEM),
    _flag("warning_active", PumpStatus.WARNING, device_class=_PROBLEM),
    _flag("remote_control", PumpStatus.REMOTE, entity_category=_DIAGNOSTIC),
    _flag("at_max_speed", PumpStatus.AT_MAX_SPEED, entity_category=_DIAGNOSTIC),
    _flag("at_min_speed", PumpStatus.AT_MIN_SPEED, entity_category=_DIAGNOSTIC),
    _flag("at_max_power", PumpStatus.AT_MAX_POWER, entity_category=_DIAGNOSTIC),
    _flag("low_flow_stop", PumpStatus.LOW_FLOW_STOP, entity_category=_DIAGNOSTIC),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrundfosConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Grundfos binary sensors."""
    async_add_entities(
        GrundfosBinarySensor(entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class GrundfosBinarySensor(GrundfosEntity, BinarySensorEntity):
    """A pump status bit."""

    entity_description: GrundfosBinarySensorDescription

    @property
    def is_on(self) -> bool | None:
        """The state from the latest poll."""
        return self.entity_description.value_fn(self.coordinator.device)
