"""Sensor platform for Mail Package Tracker (Carrier Devices + Dynamic Package Sensors)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATUS_DELIVERED
from .coordinator import MailPackageCoordinator, compute_display_timing

_LOGGER = logging.getLogger(__name__)


def _hub_device_info(entry_id: str) -> DeviceInfo:
    """Return DeviceInfo for the central Mail Package Tracker hub."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_hub")},
        name="Mail Package Tracker (Übersicht)",
        manufacturer="Mail Package Tracker",
        model="Package Hub",
        entry_type=DeviceEntryType.SERVICE,
    )


def _carrier_device_info(entry_id: str, carrier_id: str, carrier_name: str) -> DeviceInfo:
    """Return DeviceInfo for an individual Carrier / Shop device."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_carrier_{carrier_id}")},
        name=f"Paketdienst / Händler: {carrier_name}",
        manufacturer="Mail Package Tracker",
        model="Carrier Filter Rule",
        via_device=(DOMAIN, f"{entry_id}_hub"),
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mail Package Tracker sensors from a config entry."""
    coordinator: MailPackageCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        MailPackageSummarySensor(coordinator, entry),
    ]

    created_carriers: set[str] = set()
    created_packages: set[str] = set()

    for cid in coordinator.carriers:
        created_carriers.add(cid)
        entities.append(CarrierDeviceSensor(coordinator, entry, cid))

    for uid in coordinator.packages:
        created_packages.add(uid)
        entities.append(DynamicPackageSensor(coordinator, entry, uid))

    async_add_entities(entities)

    @callback
    def _on_new_carrier(carrier_id: str) -> None:
        if carrier_id not in created_carriers and carrier_id in coordinator.carriers:
            created_carriers.add(carrier_id)
            async_add_entities([CarrierDeviceSensor(coordinator, entry, carrier_id)])

    @callback
    def _on_new_package(uid: str) -> None:
        if uid not in created_packages and uid in coordinator.packages:
            created_packages.add(uid)
            async_add_entities([DynamicPackageSensor(coordinator, entry, uid)])

    coordinator.register_new_carrier_callback(_on_new_carrier)
    coordinator.register_new_package_callback(_on_new_package)


class MailPackageSummarySensor(CoordinatorEntity[MailPackageCoordinator], SensorEntity):
    """Central overview badge sensor showing expected and delivered packages."""

    _attr_has_entity_name = True
    _attr_name = "Pakete Status"
    _attr_icon = "mdi:package-variant"

    def __init__(self, coordinator: MailPackageCoordinator, entry: ConfigEntry) -> None:
        """Initialize the overview sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_overview_status"
        self._attr_device_info = _hub_device_info(entry.entry_id)

    @property
    def native_value(self) -> str:
        """Return badge status text (e.g., '2 erwartet', '1 geliefert', 'Keine')."""
        data = self.coordinator.data or {}
        return data.get("badge_state", "Keine")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed package counts and lists."""
        data = self.coordinator.data or {}
        pkgs = list((data.get("packages") or {}).values())
        return {
            "erwartet_anzahl": data.get("expected_count", 0),
            "heute_geliefert_anzahl": data.get("delivered_today_count", 0),
            "gesamt_geliefert_anzahl": data.get("delivered_total_count", 0),
            "aktive_haendler": len(self.coordinator.carriers),
            "pakete": pkgs,
        }


class CarrierDeviceSensor(CoordinatorEntity[MailPackageCoordinator], SensorEntity):
    """Sensor representing a specific Carrier / Shop device and its active shipments."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "Pakete"

    def __init__(
        self,
        coordinator: MailPackageCoordinator,
        entry: ConfigEntry,
        carrier_id: str,
    ) -> None:
        """Initialize the carrier device sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.carrier_id = carrier_id
        rule = coordinator.carriers.get(carrier_id, {})
        carrier_name = rule.get("name", carrier_id.capitalize())

        self._attr_unique_id = f"{entry.entry_id}_carrier_{carrier_id}_active"
        self._attr_name = "Pakete unterwegs"
        self._attr_icon = rule.get("icon", "mdi:package-variant")
        self._attr_device_info = _carrier_device_info(entry.entry_id, carrier_id, carrier_name)

    @property
    def available(self) -> bool:
        """Return True if carrier still exists."""
        return self.carrier_id in self.coordinator.carriers

    @property
    def native_value(self) -> int:
        """Return number of active (non-delivered) packages for this carrier."""
        count = 0
        for pkg in self.coordinator.packages.values():
            if pkg.get("carrier_id") == self.carrier_id and pkg.get("status") != STATUS_DELIVERED:
                count += 1
        return count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return rule configuration and packages for this carrier."""
        rule = self.coordinator.carriers.get(self.carrier_id, {})
        carrier_pkgs = [
            p for p in self.coordinator.packages.values() if p.get("carrier_id") == self.carrier_id
        ]
        return {
            "carrier_id": self.carrier_id,
            "name": rule.get("name", self.carrier_id),
            "enabled": rule.get("enabled", True),
            "sender_patterns": rule.get("sender_patterns", []),
            "subject_patterns": rule.get("subject_patterns", []),
            "in_transit_patterns": rule.get("in_transit_patterns", []),
            "out_for_delivery_patterns": rule.get("out_for_delivery_patterns", []),
            "delivered_patterns": rule.get("delivered_patterns", []),
            "tracking_regex": rule.get("tracking_regex", ""),
            "pakete_gesamt": len(carrier_pkgs),
        }


class DynamicPackageSensor(CoordinatorEntity[MailPackageCoordinator], SensorEntity):
    """Individual package sensor compatible with the Pakete dashboard and attached to its Carrier device."""

    def __init__(
        self,
        coordinator: MailPackageCoordinator,
        entry: ConfigEntry,
        uid: str,
    ) -> None:
        """Initialize the dynamic package sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.uid = uid
        pkg = coordinator.packages.get(uid, {})
        carrier_id = pkg.get("carrier_id", "paket")
        carrier_name = pkg.get("zusteller", "Paketdienst")

        self._attr_unique_id = uid
        self.entity_id = f"sensor.{uid}"
        self._attr_device_info = _carrier_device_info(entry.entry_id, carrier_id, carrier_name)

    @property
    def _pkg(self) -> dict[str, Any]:
        return self.coordinator.packages.get(self.uid, {})

    @property
    def available(self) -> bool:
        """Return True while the package exists in the coordinator."""
        return self.uid in self.coordinator.packages

    @property
    def name(self) -> str:
        """Return friendly name of the package sensor."""
        pkg = self._pkg
        carrier = pkg.get("zusteller", "Paket")
        inhalt = (pkg.get("inhalt") or "")[:30]
        return f"Paket {carrier} {inhalt}".strip()

    @property
    def icon(self) -> str:
        """Return carrier icon."""
        return self._pkg.get("icon", "mdi:package-variant")

    @property
    def native_value(self) -> str:
        """Return current delivery timing text."""
        pkg = self._pkg
        if not pkg:
            return "Unbekannt"
        return compute_display_timing(pkg)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return attributes required by the Pakete dashboard."""
        pkg = self._pkg
        if not pkg:
            return {}
        timing = compute_display_timing(pkg)
        return {
            "unique_id": self.uid,
            "carrier_id": pkg.get("carrier_id", ""),
            "zusteller": pkg.get("zusteller", "Paketdienst"),
            "inhalt": pkg.get("inhalt", "Bestellung"),
            "artikel_liste": pkg.get("artikel_liste", [pkg.get("inhalt", "Bestellung")]),
            "status": pkg.get("status", "Unterwegs"),
            "zustellung": timing,
            "tracking_id": pkg.get("tracking_id", ""),
            "tracking_url": pkg.get("tracking_url", ""),
            "aktualisiert_am": pkg.get("aktualisiert_am", ""),
            "zugestellt_am": pkg.get("zugestellt_am"),
            "sender": pkg.get("sender", ""),
            "subject": pkg.get("subject", ""),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Remove entity from registry if package was cleaned up."""
        if self.uid not in self.coordinator.packages:
            ent_reg = er.async_get(self.hass)
            if self.entity_id and ent_reg.async_get(self.entity_id):
                ent_reg.async_remove(self.entity_id)
            self.hass.async_create_task(self.async_remove())
            return
        super()._handle_coordinator_update()
