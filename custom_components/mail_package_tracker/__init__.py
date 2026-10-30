"""The Mail Package Tracker integration."""
from __future__ import annotations

from datetime import timedelta
import importlib
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from . import (
    const as _const_mod,
    coordinator as _coord_mod,
    dhl_tracker as _dhl_mod,
    panel as _panel_mod,
    parser as _parser_mod,
    sensor as _sensor_mod,
    switch as _switch_mod,
    text as _text_mod,
)
from .const import (
    CONF_MODE,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODE_BOTH,
    MODE_EVENT,
)
from .coordinator import MailPackageCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.TEXT, Platform.SWITCH]

SERVICE_SCAN_NOW = "scan_now"
SERVICE_REMOVE_PACKAGE = "remove_package"
SERVICE_CLEAR_DELIVERED = "clear_delivered"
SERVICE_PROCESS_EMAIL = "process_email"
SERVICE_MARK_DELIVERED = "mark_delivered"
SERVICE_MERGE_PACKAGES = "merge_packages"

SCHEMA_REMOVE_PACKAGE = vol.Schema(
    {
        vol.Required("unique_id"): cv.string,
    }
)

SCHEMA_PROCESS_EMAIL = vol.Schema(
    {
        vol.Required("sender"): cv.string,
        vol.Required("subject"): cv.string,
        vol.Optional("text", default=""): cv.string,
        vol.Optional("html", default=""): cv.string,
    }
)

SCHEMA_MERGE_PACKAGES = vol.Schema(
    {
        vol.Required("source_package"): cv.string,
        vol.Required("target_package"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mail Package Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    importlib.reload(_const_mod)
    importlib.reload(_parser_mod)
    importlib.reload(_dhl_mod)
    importlib.reload(_coord_mod)
    importlib.reload(_panel_mod)
    importlib.reload(_sensor_mod)
    importlib.reload(_switch_mod)
    importlib.reload(_text_mod)

    coordinator = _coord_mod.MailPackageCoordinator(hass, entry)
    await coordinator.async_load_storage()
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await _panel_mod.async_setup_panel_and_ws(hass, coordinator)

    # Listen to HA's built-in `imap_content` event if mode allows it
    mode = coordinator.get_config(CONF_MODE, MODE_BOTH)
    if mode in (MODE_BOTH, MODE_EVENT):
        entry.async_on_unload(
            hass.bus.async_listen("imap_content", coordinator.async_handle_imap_event)
        )

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    entry.async_on_unload(coordinator.async_unload)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _register_services(hass)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: MailPackageCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator:
        scan_min = coordinator.get_config(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        coordinator.update_interval = timedelta(minutes=max(1, int(scan_min)))
        await coordinator.async_request_refresh()


def _register_services(hass: HomeAssistant) -> None:
    """Register integration services."""

    def _get_coordinators() -> list[Any]:
        return [
            c
            for c in hass.data.get(DOMAIN, {}).values()
            if hasattr(c, "carriers") and hasattr(c, "packages")
        ]

    async def handle_scan_now(call: ServiceCall) -> None:
        """Trigger immediate IMAP scan on all coordinators."""
        for coord in _get_coordinators():
            await coord.async_request_refresh()

    async def handle_remove_package(call: ServiceCall) -> None:
        """Remove a specific package by unique_id."""
        uid = call.data["unique_id"]
        if uid.startswith("sensor."):
            uid = uid.replace("sensor.", "", 1)
        for coord in _get_coordinators():
            await coord.async_remove_package(uid)

    async def handle_mark_delivered(call: ServiceCall) -> None:
        """Mark a specific package as delivered."""
        uid = call.data["unique_id"]
        if uid.startswith("sensor."):
            uid = uid.replace("sensor.", "", 1)
        for coord in _get_coordinators():
            await coord.async_mark_delivered(uid)

    async def handle_clear_delivered(call: ServiceCall) -> None:
        """Remove all delivered packages immediately."""
        for coord in _get_coordinators():
            await coord.async_clear_delivered()

    async def handle_process_email(call: ServiceCall) -> None:
        """Manually feed an email into the parser and coordinator."""
        sender = call.data["sender"]
        subject = call.data["subject"]
        text = call.data.get("text", "")
        html_body = call.data.get("html", "")
        for coord in _get_coordinators():
            coord._record_recent_email(sender, subject, text, html_body)
            coord._process_single_email(sender, subject, text, html_body)
            await coord.async_save_storage()
            coord.async_set_updated_data(coord._build_state_dict())

    async def handle_merge_packages(call: ServiceCall) -> None:
        """Manually merge two packages."""
        src = call.data["source_package"]
        tgt = call.data["target_package"]
        if src.startswith("sensor."):
            src = src.replace("sensor.", "", 1)
        if tgt.startswith("sensor."):
            tgt = tgt.replace("sensor.", "", 1)
        for coord in _get_coordinators():
            await coord.async_merge_packages(src, tgt)

    hass.services.async_register(DOMAIN, SERVICE_SCAN_NOW, handle_scan_now)
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_PACKAGE,
        handle_remove_package,
        schema=SCHEMA_REMOVE_PACKAGE,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_MARK_DELIVERED,
        handle_mark_delivered,
        schema=SCHEMA_REMOVE_PACKAGE,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLEAR_DELIVERED, handle_clear_delivered
    )
    if not hass.services.has_service(DOMAIN, SERVICE_PROCESS_EMAIL):
        hass.services.async_register(
            DOMAIN,
            SERVICE_PROCESS_EMAIL,
            handle_process_email,
            schema=SCHEMA_PROCESS_EMAIL,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_MERGE_PACKAGES):
        hass.services.async_register(
            DOMAIN,
            SERVICE_MERGE_PACKAGES,
            handle_merge_packages,
            schema=SCHEMA_MERGE_PACKAGES,
        )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
