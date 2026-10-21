"""Editable Text entities for Carrier Filter Rules on each Carrier Device."""
from __future__ import annotations

import copy
from typing import Any

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MailPackageCoordinator
from .sensor import _carrier_device_info

RULE_TEXT_FIELDS: list[tuple[str, str, str, bool]] = [
    ("sender_patterns", "Filter: Absender", "mdi:email-search-outline", True),
    ("subject_patterns", "Filter: Betreff (optional)", "mdi:format-title", True),
    ("ordered_patterns", "Filter: Bestellt (Warte auf Versand)", "mdi:cart-check", True),
    ("in_transit_patterns", "Filter: Unterwegs", "mdi:truck-outline", True),
    ("out_for_delivery_patterns", "Filter: In Zustellung", "mdi:truck-fast-outline", True),
    ("delivered_patterns", "Filter: Zugestellt", "mdi:package-variant-closed-check", True),
    ("tomorrow_patterns", "Filter: Ankunft morgen", "mdi:calendar-clock", True),
    ("exclude_patterns", "Filter: Ausschluss-Wörter", "mdi:filter-remove-outline", True),
    ("tracking_regex", "Filter: Tracking-Nummer (Text davor / Regex)", "mdi:barcode-scan", False),
    ("content_regex", "Filter: Paket-Inhalt (Überschrift / Regex)", "mdi:text-box-search-outline", False),
    ("tracking_url_regex", "Filter: Tracking-Link enthält", "mdi:link-variant", False),
    ("default_tracking_url", "Filter: Standard Tracking-URL ({tracking_id})", "mdi:web", False),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up editable filter rule text entities for each carrier device."""
    coordinator: MailPackageCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[TextEntity] = []
    created_carriers: set[str] = set()

    def _build_for_carrier(cid: str) -> list[TextEntity]:
        return [
            CarrierRuleTextEntity(coordinator, entry, cid, key, label, icon, is_list)
            for key, label, icon, is_list in RULE_TEXT_FIELDS
        ]

    for cid in coordinator.carriers:
        created_carriers.add(cid)
        entities.extend(_build_for_carrier(cid))

    async_add_entities(entities)

    @callback
    def _on_new_carrier(carrier_id: str) -> None:
        if carrier_id not in created_carriers and carrier_id in coordinator.carriers:
            created_carriers.add(carrier_id)
            async_add_entities(_build_for_carrier(carrier_id))

    coordinator.register_new_carrier_callback(_on_new_carrier)


class CarrierRuleTextEntity(CoordinatorEntity[MailPackageCoordinator], TextEntity):
    """Editable text entity representing one filter rule field of a Carrier device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_max = 255

    def __init__(
        self,
        coordinator: MailPackageCoordinator,
        entry: ConfigEntry,
        carrier_id: str,
        field_key: str,
        label: str,
        icon: str,
        is_list: bool,
    ) -> None:
        """Initialize the filter rule text entity."""
        super().__init__(coordinator)
        self.entry = entry
        self.carrier_id = carrier_id
        self.field_key = field_key
        self.is_list = is_list

        rule = coordinator.carriers.get(carrier_id, {})
        carrier_name = rule.get("name", carrier_id.capitalize())

        self._attr_unique_id = f"{entry.entry_id}_carrier_{carrier_id}_{field_key}"
        self._attr_name = label
        self._attr_icon = icon
        self._attr_device_info = _carrier_device_info(entry.entry_id, carrier_id, carrier_name)

    @property
    def available(self) -> bool:
        """Return True if carrier exists."""
        return self.carrier_id in self.coordinator.carriers

    @property
    def native_value(self) -> str:
        """Return current filter rule value (comma-separated if list), capped at 255 chars."""
        rule = self.coordinator.carriers.get(self.carrier_id, {})
        val: Any = rule.get(self.field_key, [] if self.is_list else "")
        if self.is_list:
            if isinstance(val, list):
                text = ", ".join(str(x) for x in val if str(x).strip())
            else:
                text = str(val or "")
        else:
            text = str(val or "")
        return text[:255]

    async def async_set_value(self, value: str) -> None:
        """Update the carrier rule when edited directly in the UI."""
        rule = copy.deepcopy(self.coordinator.carriers.get(self.carrier_id, {}))
        if not rule:
            return
        if self.is_list:
            items = [x.strip() for x in (value or "").split(",") if x.strip()]
            rule[self.field_key] = items
        else:
            rule[self.field_key] = (value or "").strip()
        await self.coordinator.async_upsert_carrier(self.carrier_id, rule)
