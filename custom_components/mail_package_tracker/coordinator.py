"""DataUpdateCoordinator for Mail Package Tracker."""
from __future__ import annotations

import copy
from datetime import date, datetime, timedelta
import json
import logging
from pathlib import Path
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CLEANUP_DAYS,
    CONF_DAYS_BACK,
    CONF_IMAP_FOLDER,
    CONF_IMAP_HOST,
    CONF_IMAP_PASSWORD,
    CONF_IMAP_PORT,
    CONF_IMAP_USER,
    CONF_MODE,
    CONF_SCAN_INTERVAL,
    DEFAULT_CARRIERS,
    DEFAULT_CLEANUP_DAYS,
    DEFAULT_DAYS_BACK,
    DEFAULT_IMAP_FOLDER,
    DEFAULT_IMAP_HOST,
    DEFAULT_IMAP_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODE_BOTH,
    MODE_IMAP,
    STATUS_DELIVERED,
    STATUS_ORDERED,
    STATUS_OUT_FOR_DELIVERY,
    STATUS_RANK,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .imap_client import fetch_recent_emails_sync
from .parser import clean_email_body, parse_email_date, parse_email_with_rules

_LOGGER = logging.getLogger(__name__)


def compute_display_timing(pkg: dict[str, Any]) -> str:
    """Compute human-friendly German delivery timing string dynamically based on status and current date."""
    status = pkg.get("status", "")
    zugestellt_am = pkg.get("zugestellt_am")
    erwartet_am = pkg.get("erwartet_am")
    today = date.today()

    if status == STATUS_DELIVERED:
        if zugestellt_am:
            try:
                deliv_date = date.fromisoformat(str(zugestellt_am)[:10])
                diff = (today - deliv_date).days
                if diff <= 0:
                    return "Heute zugestellt"
                if diff == 1:
                    return "Gestern zugestellt"
                return f"Geliefert am {deliv_date.strftime('%d.%m.')}"
            except ValueError:
                pass
        return "Zugestellt"

    if status == STATUS_OUT_FOR_DELIVERY:
        return "Ankunft heute"

    if erwartet_am:
        try:
            exp_date = date.fromisoformat(str(erwartet_am)[:10])
            diff = (exp_date - today).days
            if diff == 0:
                return "Ankunft heute"
            if diff == 1:
                return "Ankunft morgen"
            if diff == 2:
                return "Ankunft übermorgen"
            if diff > 2:
                wochentage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
                return f"Ankunft {wochentage[exp_date.weekday()]}, {exp_date.strftime('%d.%m.')}"
            if diff == -1:
                return "Gestern erwartet"
            return f"Seit {abs(diff)} Tagen überfällig"
        except ValueError:
            pass

    raw_timing = pkg.get("zustellung")
    if raw_timing and raw_timing not in ("Ankunft morgen", "Ankunft heute"):
        return raw_timing

    if status == STATUS_ORDERED:
        return "Warte auf Versand"

    return "In Kürze erwartet"


class MailPackageCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator managing carrier rules, email scanning, and active packages."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.store = Store[dict[str, Any]](hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")

        self.carriers: dict[str, dict[str, Any]] = copy.deepcopy(DEFAULT_CARRIERS)
        self.packages: dict[str, dict[str, Any]] = {}
        self.recent_emails: list[dict[str, Any]] = []
        self.show_in_sidebar: bool = True
        self._new_package_callbacks: list[Callable[[str], None]] = []
        self._new_carrier_callbacks: list[Callable[[str], None]] = []
        self._unsub_midnight: Callable[[], None] | None = async_track_time_change(
            hass,
            self._handle_midnight,
            hour=0,
            minute=0,
            second=5,
        )

        scan_min = self.get_config(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=max(1, int(scan_min))),
        )

    def get_config(self, key: str, default: Any = None) -> Any:
        """Read config value from options first, then data."""
        if key in self.entry.options:
            return self.entry.options[key]
        return self.entry.data.get(key, default)

    @staticmethod
    def _load_carrier_preset_files() -> dict[str, dict[str, Any]]:
        """Load carrier JSON files from the carriers/ directory."""
        presets = copy.deepcopy(DEFAULT_CARRIERS)
        carriers_dir = Path(__file__).parent / "carriers"
        if carriers_dir.is_dir():
            for json_file in sorted(carriers_dir.glob("*.json")):
                try:
                    raw = json.loads(json_file.read_text(encoding="utf-8"))
                    if isinstance(raw, dict) and raw.get("name"):
                        cid = str(raw.get("id") or json_file.stem).strip().lower()
                        raw["id"] = cid
                        raw["is_preset"] = True
                        lang = str(raw.get("language") or "de").strip().lower()
                        raw["language"] = lang if lang in ("de", "en") else "de"
                        raw.pop("languages", None)
                        presets[cid] = raw
                except Exception as err:  # noqa: BLE001
                    _LOGGER.warning("Skipping invalid carrier preset %s: %s", json_file.name, err)
        return presets

    async def async_load_storage(self) -> None:
        """Load persisted packages, custom carrier rules, and recent emails."""
        file_presets = await self.hass.async_add_executor_job(self._load_carrier_preset_files)
        self.carriers = copy.deepcopy(file_presets)

        stored = await self.store.async_load()
        if isinstance(stored, dict):
            stored_carriers = stored.get("carriers", {})
            for cid, cdata in stored_carriers.items():
                if cid in self.carriers and self.carriers[cid].get("is_preset"):
                    # Merge preset updates with user customizations
                    merged = copy.deepcopy(file_presets.get(cid, DEFAULT_CARRIERS.get(cid, {})))
                    merged.update(cdata)
                    merged.pop("languages", None)
                    if merged.get("language") not in ("de", "en"):
                        merged["language"] = file_presets.get(cid, {}).get("language", "de")
                    self.carriers[cid] = merged
                else:
                    cdata.pop("languages", None)
                    if cdata.get("language") not in ("de", "en"):
                        cdata["language"] = "de"
                    self.carriers[cid] = cdata

            self.packages = stored.get("packages", {})
            self.recent_emails = stored.get("recent_emails", [])
            self.show_in_sidebar = bool(stored.get("show_in_sidebar", True))

        # Refresh display timing on loaded packages
        for pkg in self.packages.values():
            pkg["zustellung"] = compute_display_timing(pkg)

    async def async_save_storage(self) -> None:
        """Save current state to Home Assistant storage."""
        await self.store.async_save(
            {
                "carriers": self.carriers,
                "packages": self.packages,
                "recent_emails": self.recent_emails[:35],
                "show_in_sidebar": self.show_in_sidebar,
            }
        )

    def register_new_package_callback(self, cb: Callable[[str], None]) -> None:
        """Register callback to spawn a dynamic sensor when a new package UID appears."""
        self._new_package_callbacks.append(cb)

    def register_new_carrier_callback(self, cb: Callable[[str], None]) -> None:
        """Register callback to spawn a carrier sensor when a new carrier rule is added."""
        self._new_carrier_callbacks.append(cb)

    def _notify_new_package(self, uid: str) -> None:
        for cb in self._new_package_callbacks:
            cb(uid)

    def _notify_new_carrier(self, carrier_id: str) -> None:
        for cb in self._new_carrier_callbacks:
            cb(carrier_id)

    async def async_upsert_carrier(self, carrier_id: str, rule_data: dict[str, Any]) -> None:
        """Add or update a carrier rule and re-evaluate cached recent emails."""
        is_new = carrier_id not in self.carriers
        self.carriers[carrier_id] = rule_data
        if is_new:
            self._notify_new_carrier(carrier_id)

        # Immediately re-process cached recent emails against the updated rules
        for mail in reversed(self.recent_emails):
            self._process_single_email(
                sender=mail.get("sender", ""),
                subject=mail.get("subject", ""),
                text=mail.get("text", ""),
                html_body=mail.get("html", ""),
                date_str=mail.get("date"),
            )

        await self.async_save_storage()
        self.async_set_updated_data(self._build_state_dict())

    async def async_delete_carrier(self, carrier_id: str) -> None:
        """Delete a custom carrier rule or disable a preset."""
        if carrier_id in self.carriers:
            if self.carriers[carrier_id].get("is_preset"):
                self.carriers[carrier_id]["enabled"] = False
            else:
                self.carriers.pop(carrier_id, None)
            await self.async_save_storage()
            self.async_set_updated_data(self._build_state_dict())

    def _record_recent_email(
        self,
        sender: str,
        subject: str,
        text: str,
        html_body: str = "",
        date_str: str | None = None,
        msg_id: str | None = None,
    ) -> None:
        """Store email in recent_emails cache (for UI Mail-Assistent preview)."""
        clean_text, _ = clean_email_body(text, html_body)
        key = msg_id or f"{sender}|{subject}|{date_str or ''}"
        for existing in self.recent_emails:
            if existing.get("key") == key or (
                existing.get("sender") == sender and existing.get("subject") == subject
            ):
                return

        self.recent_emails.insert(
            0,
            {
                "key": key,
                "sender": sender,
                "subject": subject,
                "date": date_str or datetime.now().strftime("%d.%m.%Y %H:%M"),
                "text": clean_text[:3000],
                "html": html_body[:6000] if html_body else "",
            },
        )
        self.recent_emails = self.recent_emails[:35]

    def _process_single_email(
        self,
        sender: str,
        subject: str,
        text: str,
        html_body: str = "",
        date_str: str | None = None,
    ) -> dict[str, Any]:
        """Parse an email and create/update package entry if matched."""
        parsed = parse_email_with_rules(
            sender=sender,
            subject=subject,
            body_text=text,
            carriers=self.carriers,
            body_html=html_body,
            email_date=date_str,
        )
        if not parsed.get("matched"):
            return parsed

        uid = parsed["uid"]
        tracking_id = (parsed.get("tracking_id") or "").strip()
        new_ids = {
            x.strip().lower()
            for x in ([tracking_id] + list(parsed.get("all_ids") or []))
            if x and x.strip()
        }

        # Deduplicate across all packages by any matching tracking_id or order_id
        matching_uids: list[str] = []
        if new_ids:
            for existing_uid, existing_pkg in list(self.packages.items()):
                ex_tid = (existing_pkg.get("tracking_id") or "").strip()
                ex_ids = {
                    x.strip().lower()
                    for x in ([ex_tid] + list(existing_pkg.get("all_ids") or []))
                    if x and x.strip()
                }
                if new_ids & ex_ids:
                    matching_uids.append(existing_uid)

        if matching_uids:
            # Prefer the matching UID that already has the highest status rank
            matching_uids.sort(
                key=lambda u: STATUS_RANK.get(self.packages[u].get("status", ""), 0),
                reverse=True,
            )
            uid = matching_uids[0]
            parsed["uid"] = uid
            merged_ids = list(parsed.get("all_ids") or [])
            for m_uid in matching_uids:
                m_pkg = self.packages[m_uid]
                ex_tid = (m_pkg.get("tracking_id") or "").strip()
                for old_id in m_pkg.get("all_ids") or ([ex_tid] if ex_tid else []):
                    if old_id and old_id not in merged_ids:
                        merged_ids.append(old_id)
            parsed["all_ids"] = merged_ids
            # Remove any secondary duplicate entries (e.g., an older 'Bestellt' entry now merged into 'Unterwegs')
            for extra_uid in matching_uids[1:]:
                self.packages.pop(extra_uid, None)

        existing = self.packages.get(uid)
        is_new = existing is None

        # Do not downgrade a package to a lower lifecycle stage (Bestellt -> Unterwegs -> In Zustellung -> Zugestellt)
        if existing:
            old_rank = STATUS_RANK.get(existing.get("status", ""), 0)
            new_rank = STATUS_RANK.get(parsed.get("status", ""), 0)
            if old_rank > new_rank:
                # Still keep merged all_ids on the existing higher-rank package
                existing["all_ids"] = parsed.get("all_ids") or existing.get("all_ids", [])
                return existing

        # Preserve original zugestellt_am if already delivered earlier
        if existing and existing.get("zugestellt_am") and parsed["status"] == STATUS_DELIVERED:
            parsed["zugestellt_am"] = existing["zugestellt_am"]

        # Preserve erwartet_am if existing had one and new email did not specify a new one
        if existing and existing.get("erwartet_am") and not parsed.get("erwartet_am"):
            parsed["erwartet_am"] = existing["erwartet_am"]

        # Preserve more descriptive content if new email only has generic subject
        if existing and existing.get("inhalt") and len(existing["inhalt"]) > len(parsed.get("inhalt", "")):
            if parsed["inhalt"].endswith("Sendung"):
                parsed["inhalt"] = existing["inhalt"]

        parsed["zustellung"] = compute_display_timing(parsed)
        self.packages[uid] = parsed

        if is_new:
            self._notify_new_package(uid)

        return parsed

    @callback
    def async_handle_imap_event(self, event: Event) -> None:
        """Handle Home Assistant's built-in `imap_content` event."""
        data = event.data or {}
        sender = str(data.get("sender") or "")
        subject = str(data.get("subject") or "")
        text = str(data.get("text") or "")
        html_body = str(data.get("html") or "")
        date_str = str(data.get("date") or datetime.now().strftime("%d.%m.%Y %H:%M"))
        uid = str(data.get("uid") or "")

        self._record_recent_email(sender, subject, text, html_body, date_str, msg_id=uid)
        result = self._process_single_email(sender, subject, text, html_body, date_str)
        if result.get("matched"):
            _LOGGER.info(
                "Package matched from imap_content event: %s (%s - %s)",
                result.get("uid"),
                result.get("zusteller"),
                result.get("zustellung"),
            )
        self.hass.async_create_task(self.async_save_storage())
        self.async_set_updated_data(self._build_state_dict())

    @callback
    def _handle_midnight(self, _now: datetime) -> None:
        """Recalculate package display timings and badge counts at midnight."""
        _LOGGER.debug("Midnight recalculation of package timings and badges")
        self._cleanup_old_packages()
        self.async_set_updated_data(self._build_state_dict())
        self.hass.async_create_task(self.async_save_storage())

    @callback
    def async_unload(self) -> None:
        """Clean up listeners when unloaded."""
        if self._unsub_midnight:
            self._unsub_midnight()
            self._unsub_midnight = None

    def _cleanup_old_packages(self) -> None:
        """Remove delivered packages older than cleanup_days and refresh display timing."""
        cleanup_days = int(self.get_config(CONF_CLEANUP_DAYS, DEFAULT_CLEANUP_DAYS))
        today = date.today()
        to_remove: list[str] = []

        for uid, pkg in self.packages.items():
            # If package had 'Ankunft morgen' from an older email but no erwartet_am stored yet,
            # infer erwartet_am from recent emails or mail_date or aktualisiert_am so it immediately corrects today!
            if not pkg.get("erwartet_am") and pkg.get("zustellung") in ("Ankunft morgen", "morgen"):
                ref_dt = None
                for m in self.recent_emails:
                    if pkg.get("tracking_id") and pkg.get("tracking_id") in m.get("text", ""):
                        ref_dt = parse_email_date(m.get("date"))
                        break
                if not ref_dt and pkg.get("mail_date"):
                    ref_dt = parse_email_date(pkg.get("mail_date"))
                if not ref_dt and pkg.get("aktualisiert_am"):
                    ref_dt = parse_email_date(pkg.get("aktualisiert_am"))
                if ref_dt:
                    pkg["erwartet_am"] = (ref_dt + timedelta(days=1)).isoformat()

            pkg["zustellung"] = compute_display_timing(pkg)
            tid = str(pkg.get("tracking_id") or "").strip()
            turl = str(pkg.get("tracking_url") or "").strip()
            if "logistics.dhl" in turl.lower() and tid.startswith("0034"):
                pkg["tracking_url"] = f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tid}"
            if pkg.get("status") == STATUS_DELIVERED and pkg.get("zugestellt_am"):
                try:
                    deliv_date = date.fromisoformat(str(pkg["zugestellt_am"])[:10])
                    if (today - deliv_date).days >= cleanup_days:
                        to_remove.append(uid)
                except ValueError:
                    pass

        for uid in to_remove:
            self.packages.pop(uid, None)

    async def async_remove_package(self, uid: str) -> None:
        """Remove a specific package by UID."""
        if uid in self.packages:
            self.packages.pop(uid, None)
            await self.async_save_storage()
            self.async_set_updated_data(self._build_state_dict())

    async def async_clear_delivered(self) -> None:
        """Remove all delivered packages immediately."""
        to_del = [uid for uid, p in self.packages.items() if p.get("status") == STATUS_DELIVERED]
        for uid in to_del:
            self.packages.pop(uid, None)
        await self.async_save_storage()
        self.async_set_updated_data(self._build_state_dict())

    async def async_fetch_imap_now(self) -> list[dict[str, Any]]:
        """Fetch recent emails directly from IMAP server if configured."""
        mode = self.get_config(CONF_MODE, MODE_BOTH)
        host = self.get_config(CONF_IMAP_HOST, DEFAULT_IMAP_HOST)
        port = int(self.get_config(CONF_IMAP_PORT, DEFAULT_IMAP_PORT))
        user = self.get_config(CONF_IMAP_USER, "")
        password = self.get_config(CONF_IMAP_PASSWORD, "")
        folder = self.get_config(CONF_IMAP_FOLDER, DEFAULT_IMAP_FOLDER)
        days_back = int(self.get_config(CONF_DAYS_BACK, DEFAULT_DAYS_BACK))

        if mode not in (MODE_BOTH, MODE_IMAP) or not user or not password:
            return self.recent_emails

        try:
            emails = await self.hass.async_add_executor_job(
                fetch_recent_emails_sync,
                host,
                port,
                user,
                password,
                folder,
                days_back,
                40,
            )
            # Process oldest to newest so status progressions (Versendet -> In Zustellung -> Zugestellt) apply in order
            for mail in reversed(emails):
                self._record_recent_email(
                    sender=mail.get("sender", ""),
                    subject=mail.get("subject", ""),
                    text=mail.get("text", ""),
                    html_body=mail.get("html", ""),
                    date_str=mail.get("date"),
                    msg_id=mail.get("message_id"),
                )
                self._process_single_email(
                    sender=mail.get("sender", ""),
                    subject=mail.get("subject", ""),
                    text=mail.get("text", ""),
                    html_body=mail.get("html", ""),
                    date_str=mail.get("date"),
                )
        except Exception as err:
            _LOGGER.warning("IMAP poll failed: %s", err)

        return self.recent_emails

    async def _async_update_data(self) -> dict[str, Any]:
        """Periodic coordinator update."""
        await self.async_fetch_imap_now()
        self._cleanup_old_packages()
        await self.async_save_storage()
        return self._build_state_dict()

    def _build_state_dict(self) -> dict[str, Any]:
        """Build summary state dictionary for sensors."""
        today_str = date.today().isoformat()
        ordered = [
            p for p in self.packages.values() if p.get("status") == STATUS_ORDERED
        ]
        in_transit = [
            p
            for p in self.packages.values()
            if p.get("status") not in (STATUS_ORDERED, STATUS_DELIVERED)
        ]
        expected = [
            p for p in self.packages.values() if p.get("status") != STATUS_DELIVERED
        ]
        delivered_today = [
            p
            for p in self.packages.values()
            if p.get("status") == STATUS_DELIVERED and p.get("zugestellt_am") == today_str
        ]
        delivered_all = [
            p for p in self.packages.values() if p.get("status") == STATUS_DELIVERED
        ]

        ordered_count = len(ordered)
        transit_count = len(in_transit)
        exp_count = len(expected)
        del_today_count = len(delivered_today)

        badge_state = f"Pakete {ordered_count}/{transit_count}/{del_today_count}"

        return {
            "badge_state": badge_state,
            "ordered_count": ordered_count,
            "in_transit_count": transit_count,
            "expected_count": exp_count,
            "delivered_today_count": del_today_count,
            "delivered_total_count": len(delivered_all),
            "packages": self.packages,
            "carriers": self.carriers,
        }
