"""Custom Sidebar Panel and WebSocket API for Mail Package Tracker."""
from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
import re
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


def validate_carrier_json(raw_json: str) -> dict[str, Any]:
    """Validate carrier JSON syntax, schema, languages, and regex patterns."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as err:
        return {
            "valid": False,
            "errors": [f"JSON Syntax Error (Line {err.lineno}, Col {err.colno}): {err.msg}"],
            "warnings": [],
            "normalized": None,
        }

    if not isinstance(data, dict):
        return {
            "valid": False,
            "errors": ["Root JSON element must be an object ({ ... })."],
            "warnings": [],
            "normalized": None,
        }

    name = str(data.get("name") or "").strip()
    if not name:
        errors.append("Missing required field 'name' (non-empty string).")

    raw_id = str(data.get("id") or name).strip()
    cid = slugify_id(raw_id, 20) if raw_id else ""
    if not cid:
        errors.append("Missing or invalid 'id' / 'name'.")

    # Validate languages ("de", "en")
    raw_langs = data.get("languages", data.get("language"))
    langs: list[str] = []
    if isinstance(raw_langs, str):
        langs = [x.strip().lower() for x in raw_langs.split(",") if x.strip()]
    elif isinstance(raw_langs, list):
        langs = [str(x).strip().lower() for x in raw_langs if str(x).strip()]

    valid_lang_codes = {"de", "en"}
    if not langs:
        errors.append("Missing required field 'languages' (e.g. [\"de\", \"en\"], [\"de\"], or [\"en\"]).")
    else:
        invalid_langs = [l for l in langs if l not in valid_lang_codes]
        if invalid_langs:
            errors.append(f"Unsupported language code(s) in 'languages': {invalid_langs}. Allowed: ['de', 'en'].")
        langs = [l for l in ["de", "en"] if l in langs]

    list_fields = [
        "sender_patterns",
        "subject_patterns",
        "ordered_patterns",
        "in_transit_patterns",
        "out_for_delivery_patterns",
        "delivered_patterns",
        "tomorrow_patterns",
        "exclude_patterns",
    ]
    normalized_lists: dict[str, list[str]] = {}
    for lf in list_fields:
        val = data.get(lf, [])
        if not isinstance(val, list) or any(not isinstance(item, str) for item in val):
            errors.append(f"Field '{lf}' must be a JSON array of strings (list[str]).")
            normalized_lists[lf] = []
        else:
            normalized_lists[lf] = [item.strip() for item in val if item.strip()]

    if not normalized_lists.get("sender_patterns"):
        errors.append("Field 'sender_patterns' must contain at least one sender domain or email pattern.")

    status_count = sum(
        len(normalized_lists.get(k, []))
        for k in ("ordered_patterns", "in_transit_patterns", "out_for_delivery_patterns", "delivered_patterns")
    )
    if status_count == 0:
        errors.append(
            "At least one status keyword list ('ordered_patterns', 'in_transit_patterns', "
            "'out_for_delivery_patterns', or 'delivered_patterns') must contain keywords."
        )

    str_fields = ["tracking_regex", "content_regex", "tracking_url_regex", "default_tracking_url", "icon"]
    for sf in str_fields:
        val = data.get(sf, "")
        if val is not None and not isinstance(val, str):
            errors.append(f"Field '{sf}' must be a string.")

    # Validate regex syntax if field uses explicit regex syntax
    for rf in ("tracking_regex", "content_regex", "tracking_url_regex"):
        rval = str(data.get(rf) or "").strip()
        if rval and (rval.startswith("(") or "[0-9]" in rval or "\\s" in rval or "[^" in rval):
            try:
                re.compile(rval)
            except re.error as rerr:
                errors.append(f"Invalid regular expression in '{rf}': {rerr}")

    normalized = {
        "schema_version": 1,
        "id": cid,
        "name": name,
        "icon": str(data.get("icon") or "mdi:package-variant-closed").strip(),
        "languages": langs or ["de", "en"],
        "enabled": bool(data.get("enabled", True)),
        **normalized_lists,
        "tracking_regex": str(data.get("tracking_regex") or "").strip(),
        "content_regex": str(data.get("content_regex") or "").strip(),
        "tracking_url_regex": str(data.get("tracking_url_regex") or "").strip(),
        "default_tracking_url": str(data.get("default_tracking_url") or "").strip(),
    }

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "normalized": normalized if len(errors) == 0 else None,
    }


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

    _register_websocket_commands(hass)
    await async_update_sidebar_panel(hass, coordinator.show_in_sidebar)


async def async_update_sidebar_panel(hass: HomeAssistant, show: bool) -> None:
    """Add or remove the Mail Package Tracker panel from the Home Assistant sidebar."""
    panels = hass.data.get("frontend_panels", {})
    if show:
        version = int(time.time())
        is_de = str(getattr(hass.config, "language", "de") or "de").lower().startswith("de")
        sidebar_title = "Paket-Tracker" if is_de else "Package Tracker"

        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title=sidebar_title,
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
        existing["schema_version"] = 1
        if not existing.get("languages") or not isinstance(existing.get("languages"), list):
            existing["languages"] = ["de", "en"]
        coord.carriers[cid] = existing

        def _sync_carrier_json_file() -> None:
            carriers_dir = Path(__file__).parent / "carriers"
            carriers_dir.mkdir(parents=True, exist_ok=True)
            export_obj = {k: v for k, v in existing.items() if k != "is_preset"}
            (carriers_dir / f"{cid}.json").write_text(
                json.dumps(export_obj, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        await hass.async_add_executor_job(_sync_carrier_json_file)

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

    @websocket_api.websocket_command(
        {
            vol.Required("type"): "mail_package_tracker/import_carrier_json",
            vol.Required("raw_json"): str,
            vol.Optional("apply", default=False): bool,
        }
    )
    @websocket_api.async_response
    async def ws_import_carrier_json(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        coord = _get_coordinator(hass)
        if not coord:
            connection.send_error(msg["id"], "not_loaded", "Coordinator not found")
            return

        validation = validate_carrier_json(msg["raw_json"])
        if not validation["valid"] or not msg.get("apply", False):
            connection.send_result(msg["id"], validation)
            return

        norm = validation["normalized"]
        cid = norm["id"]
        existing = copy.deepcopy(coord.carriers.get(cid, {}))
        existing.update(norm)
        existing["id"] = cid
        coord.carriers[cid] = existing

        # Also save as JSON file in carriers/ directory so it's persisted cleanly
        def _write_preset_file() -> None:
            carriers_dir = Path(__file__).parent / "carriers"
            carriers_dir.mkdir(parents=True, exist_ok=True)
            export_obj = {k: v for k, v in norm.items() if k != "is_preset"}
            (carriers_dir / f"{cid}.json").write_text(
                json.dumps(export_obj, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        await hass.async_add_executor_job(_write_preset_file)
        coord._notify_new_carrier(cid)

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
                **validation,
                "imported": True,
                "carrier_id": cid,
                "carriers": coord.carriers,
                "packages": list(coord.packages.values()),
            },
        )

    ws_handlers = hass.data.get("websocket_api")
    for cmd in (
        ws_get_data,
        ws_save_carrier,
        ws_delete_carrier,
        ws_test_email,
        ws_remove_package,
        ws_scan_now,
        ws_import_carrier_json,
    ):
        cmd_type = getattr(cmd, "_ws_command", None)
        if isinstance(ws_handlers, dict) and cmd_type in ws_handlers:
            ws_handlers.pop(cmd_type, None)
        try:
            websocket_api.async_register_command(hass, cmd)
        except Exception:  # noqa: BLE001
            pass
