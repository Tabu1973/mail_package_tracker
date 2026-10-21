"""Custom Sidebar Panel and WebSocket API for Mail Package Tracker."""
from __future__ import annotations

import copy
import logging
from pathlib import Path
import time
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.frontend import (
    async_register_built_in_panel,
    async_remove_panel,
)
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MailPackageCoordinator
from .parser import parse_email_with_rules as parse_email, slugify_id

_LOGGER = logging.getLogger(__name__)

PANEL_URL_PATH = "mail-package-tracker"
STATIC_URL_PREFIX = "/mail_package_tracker_static"
BRAND_URL_PREFIX = "/mail_package_tracker_brand"


def _get_coordinator(hass: HomeAssistant) -> Any:
    """Return the active MailPackageCoordinator instance."""
    for val in hass.data.get(DOMAIN, {}).values():
        if hasattr(val, "carriers") and hasattr(val, "packages"):
            return val
    return None


async def async_setup_panel_and_ws(hass: HomeAssistant, coordinator: MailPackageCoordinator) -> None:
    """Register static assets, WebSocket commands, and (if enabled) the sidebar panel."""
    base_dir = Path(__file__).parent
    frontend_dir = base_dir / "frontend"
    brand_dir = base_dir / "brand"

    if not hass.data.get(f"{DOMAIN}_static_registered"):
        paths = [
            StaticPathConfig(STATIC_URL_PREFIX, str(frontend_dir), cache_headers=False),
            StaticPathConfig(BRAND_URL_PREFIX, str(brand_dir), cache_headers=False),
        ]
        await hass.http.async_register_static_paths(paths)
        hass.data[f"{DOMAIN}_static_registered"] = True

    if not hass.data.get(f"{DOMAIN}_ws_cmds_registered"):
        _register_websocket_commands(hass)
        hass.data[f"{DOMAIN}_ws_cmds_registered"] = True

    await async_update_sidebar_panel(hass, coordinator.show_in_sidebar)


async def async_update_sidebar_panel(hass: HomeAssistant, show: bool) -> None:
    """Add or remove the Mail Package Tracker panel from the Home Assistant sidebar."""
    panels = hass.data.get("frontend_panels", {})
    if show:
        version = int(time.time())

        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title="Paket-Tracker",
            sidebar_icon="mdi:package-variant-closed-check",
            frontend_url_path=PANEL_URL_PATH,
            config={
                "_panel_custom": {
                    "name": "mail-package-tracker-panel",
                    "embed_iframe": False,
                    "trust_external": False,
                    "js_url": f"{STATIC_URL_PREFIX}/panel.js?v={version}",
                }
            },
            require_admin=False,
            update=True,
        )
    else:
        if PANEL_URL_PATH in panels:
            async_remove_panel(hass, PANEL_URL_PATH)


def _register_websocket_commands(hass: HomeAssistant) -> None:
    """Register WebSocket commands used by the sidebar configuration panel."""

    @websocket_api.websocket_command({vol.Required("type"): "mail_package_tracker/get_data"})
    @websocket_api.async_response
    async def ws_get_data(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        coord = _get_coordinator(hass)
        if not coord:
            connection.send_error(msg["id"], "not_loaded", "Coordinator not found")
            return
        connection.send_result(
            msg["id"],
            {
                "carriers": coord.carriers,
                "packages": list(coord.packages.values()),
                "recent_emails": coord.recent_emails[:40],
                "show_in_sidebar": coord.show_in_sidebar,
            },
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): "mail_package_tracker/save_carrier",
            vol.Required("carrier_id"): str,
            vol.Required("rule"): dict,
            vol.Optional("rescan", default=True): bool,
        }
    )
    @websocket_api.async_response
    async def ws_save_carrier(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        coord = _get_coordinator(hass)
        if not coord:
            connection.send_error(msg["id"], "not_loaded", "Coordinator not found")
            return

        cid = slugify_id(msg["carrier_id"], 20)
        rule_in = msg["rule"]
        existing = copy.deepcopy(coord.carriers.get(cid, {}))
        existing.update(rule_in)
        existing["id"] = cid
        coord.carriers[cid] = existing

        # Notify listeners if this is a brand new carrier
        coord._notify_new_carrier(cid)

        if msg.get("rescan", True):
            for mail in reversed(coord.recent_emails):
                coord._process_single_email(
                    sender=mail.get("sender", ""),
                    subject=mail.get("subject", ""),
                    text=mail.get("text", ""),
                    html_body=mail.get("html", ""),
                    date_str=mail.get("date", ""),
                )
            coord._cleanup_old_packages()

        await coord.async_save_storage()
        coord.async_set_updated_data(coord._build_state_dict())
        connection.send_result(
            msg["id"],
            {
                "carrier_id": cid,
                "carriers": coord.carriers,
                "packages": list(coord.packages.values()),
            },
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): "mail_package_tracker/delete_carrier",
            vol.Required("carrier_id"): str,
        }
    )
    @websocket_api.async_response
    async def ws_delete_carrier(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        coord = _get_coordinator(hass)
        if not coord:
            connection.send_error(msg["id"], "not_loaded", "Coordinator not found")
            return
        cid = msg["carrier_id"]
        coord.carriers.pop(cid, None)
        await coord.async_save_storage()
        coord.async_set_updated_data(coord._build_state_dict())
        connection.send_result(msg["id"], {"carriers": coord.carriers})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): "mail_package_tracker/test_email",
            vol.Required("sender"): str,
            vol.Required("subject"): str,
            vol.Optional("text", default=""): str,
            vol.Optional("html", default=""): str,
            vol.Optional("apply_package", default=False): bool,
        }
    )
    @websocket_api.async_response
    async def ws_test_email(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        coord = _get_coordinator(hass)
        if not coord:
            connection.send_error(msg["id"], "not_loaded", "Coordinator not found")
            return

        if msg.get("apply_package"):
            parsed = await coord.async_process_manual_email(
                sender=msg["sender"],
                subject=msg["subject"],
                text=msg.get("text", ""),
                html_body=msg.get("html", ""),
            )
        else:
            parsed = parse_email(
                sender=msg["sender"],
                subject=msg["subject"],
                body_text=msg.get("text", ""),
                carriers=coord.carriers,
                body_html=msg.get("html", ""),
            )

        connection.send_result(
            msg["id"],
            {
                "result": parsed,
                "packages": list(coord.packages.values()),
            },
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): "mail_package_tracker/remove_package",
            vol.Required("uid"): str,
        }
    )
    @websocket_api.async_response
    async def ws_remove_package(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        coord = _get_coordinator(hass)
        if not coord:
            connection.send_error(msg["id"], "not_loaded", "Coordinator not found")
            return
        await coord.async_remove_package(msg["uid"])
        connection.send_result(msg["id"], {"packages": list(coord.packages.values())})

    @websocket_api.websocket_command({vol.Required("type"): "mail_package_tracker/scan_now"})
    @websocket_api.async_response
    async def ws_scan_now(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        coord = _get_coordinator(hass)
        if not coord:
            connection.send_error(msg["id"], "not_loaded", "Coordinator not found")
            return
        await coord.async_request_refresh()
        connection.send_result(
            msg["id"],
            {
                "packages": list(coord.packages.values()),
                "recent_emails": coord.recent_emails[:40],
            },
        )

    for cmd in (
        ws_get_data,
        ws_save_carrier,
        ws_delete_carrier,
        ws_test_email,
        ws_remove_package,
        ws_scan_now,
    ):
        websocket_api.async_register_command(hass, cmd)
