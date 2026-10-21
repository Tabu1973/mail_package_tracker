"""Switch platform to enable/disable each Carrier Device rule directly."""
from __future__ import annotations

import copy
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MailPackageCoordinator
from .panel import async_update_sidebar_panel
from .sensor import _carrier_device_info, _hub_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sidebar toggle switch and enable/disable switch for each carrier device."""
    coordinator: MailPackageCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SwitchEntity] = [
        SidebarPanelSwitch(coordinator, entry),
    ]
    created_carriers: set[str] = set()

    for cid in coordinator.carriers:
        created_carriers.add(cid)
        entities.append(CarrierEnableSwitch(coordinator, entry, cid))

    async_add_entities(entities)

    @callback
    def _on_new_carrier(carrier_id: str) -> None:
        if carrier_id not in created_carriers and carrier_id in coordinator.carriers:
            created_carriers.add(carrier_id)
            async_add_entities([CarrierEnableSwitch(coordinator, entry, carrier_id)])

    coordinator.register_new_carrier_callback(_on_new_carrier)


class SidebarPanelSwitch(CoordinatorEntity[MailPackageCoordinator], SwitchEntity):
    """Switch to show or hide the Mail Package Tracker panel in the Home Assistant sidebar."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "In Seitenleiste einblenden"
    _attr_icon = "mdi:dock-left"

    def __init__(
        self,
        coordinator: MailPackageCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sidebar panel switch."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_show_in_sidebar"
        self._attr_device_info = _hub_device_info(entry.entry_id)

    @property
    def is_on(self) -> bool:
        """Return True if panel is shown in sidebar."""
        return bool(self.coordinator.show_in_sidebar)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Show panel in sidebar."""
        self.coordinator.show_in_sidebar = True
        await async_update_sidebar_panel(self.hass, True)
        await self.coordinator.async_save_storage()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Hide panel from sidebar."""
        self.coordinator.show_in_sidebar = False
        await async_update_sidebar_panel(self.hass, False)
        await self.coordinator.async_save_storage()
        self.async_write_ha_state()


class CarrierEnableSwitch(CoordinatorEntity[MailPackageCoordinator], SwitchEntity):
    """Switch to enable or disable a Carrier filter rule directly on the device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Filterregel aktiv"
    _attr_icon = "mdi:filter-check"

    def __init__(
        self,
        coordinator: MailPackageCoordinator,
        entry: ConfigEntry,
        carrier_id: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entry = entry
        self.carrier_id = carrier_id
        rule = coordinator.carriers.get(carrier_id, {})
        carrier_name = rule.get("name", carrier_id.capitalize())

        self._attr_unique_id = f"{entry.entry_id}_carrier_{carrier_id}_enabled"
        self._attr_device_info = _carrier_device_info(entry.entry_id, carrier_id, carrier_name)

    @property
    def available(self) -> bool:
        """Return True if carrier exists."""
        return self.carrier_id in self.coordinator.carriers

    @property
    def is_on(self) -> bool:
        """Return True if carrier rule is enabled."""
        rule = self.coordinator.carriers.get(self.carrier_id, {})
        return bool(rule.get("enabled", True))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable carrier rule."""
        rule = copy.deepcopy(self.coordinator.carriers.get(self.carrier_id, {}))
        if rule:
            rule["enabled"] = True
            await self.coordinator.async_upsert_carrier(self.carrier_id, rule)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable carrier rule."""
        rule = copy.deepcopy(self.coordinator.carriers.get(self.carrier_id, {}))
        if rule:
            rule["enabled"] = False
            await self.coordinator.async_upsert_carrier(self.carrier_id, rule)
