"""Base entity for Grundfos pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import GrundfosConfigEntry, GrundfosCoordinator


@dataclass(frozen=True, kw_only=True)
class GrundfosEntityDescription(EntityDescription):
    """Describe a Grundfos entity."""

    component: str
    """The register block on GrundfosPump this entity reads from."""


class GrundfosEntity(CoordinatorEntity[GrundfosCoordinator]):
    """An entity on one pump, reading one of its register blocks."""

    _attr_has_entity_name = True
    entity_description: GrundfosEntityDescription

    def __init__(
        self, entry: GrundfosConfigEntry, description: GrundfosEntityDescription
    ) -> None:
        """Initialize the entity."""
        super().__init__(entry.runtime_data)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Whether this entity's register block answered the latest poll."""
        return (
            super().available
            and self.entity_description.component not in self.coordinator.data.failed
        )
