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
from .dhl_tracker import async_fetch_dhl_tracking
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

        # Reconcile duplicate merchant-carrier packages (e.g. Amazon order + DHL carrier notification)
        reconciled = self._reconcile_merchant_carrier_packages()
        if reconciled:
            await self.async_save_storage()

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

        # Smart merchant-carrier linking: If DHL/Hermes/DPD/UPS announces a package on behalf of a merchant
        # (e.g. DHL email: "Ihre Amazon Sendung ist unterwegs" -> inhalt: "Amazon")
        # and there is an active unlinked package for that merchant, link them!
        logistics_carriers = {"dhl", "dpd", "hermes", "gls", "ups"}
        if not matching_uids:
            p_carrier = parsed.get("carrier_id")
            p_content = (parsed.get("inhalt") or "").strip().lower()
            p_subj = (parsed.get("subject") or "").strip().lower()

            # Case A: Carrier email on behalf of a merchant (e.g. DHL for Amazon)
            if p_carrier in logistics_carriers:
                target_merchant = None
                if p_content == "amazon" or "amazon sendung" in p_subj:
                    target_merchant = "amazon"
                elif p_content in self.carriers and p_content not in logistics_carriers:
                    target_merchant = p_content

                if target_merchant:
                    unlinked = [
                        (u, p)
                        for u, p in self.packages.items()
                        if p.get("carrier_id") == target_merchant
                        and p.get("status") != STATUS_DELIVERED
                        and not any(
                            str(x).startswith("JJD") or str(x).startswith("0034") or str(x).startswith("1Z")
                            for x in ([p.get("tracking_id")] + list(p.get("all_ids") or []))
                        )
                    ]
                    if unlinked:
                        carrier_dt = parse_email_date(date_str) if date_str else date.today()

                        def _dist_to_carrier(item: tuple[str, dict[str, Any]]) -> float:
                            m_pkg = item[1]
                            d = parse_email_date(m_pkg.get("mail_date") or m_pkg.get("aktualisiert_am"))
                            diff = (carrier_dt - d).days
                            return float(diff) if diff >= 0 else float(abs(diff) * 3)

                        unlinked.sort(key=_dist_to_carrier)
                        matching_uids.append(unlinked[0][0])

            # Case B: Merchant email arrives after carrier email (e.g. Amazon email arrives, DHL already known)
            elif p_carrier not in logistics_carriers:
                carrier_candidates = [
                    (u, p)
                    for u, p in self.packages.items()
                    if p.get("carrier_id") in logistics_carriers
                    and p.get("status") != STATUS_DELIVERED
                    and (
                        (p.get("inhalt") or "").strip().lower() == p_carrier
                        or f"{p_carrier} sendung" in (p.get("subject") or "").strip().lower()
                    )
                    and not any(
                        "-" in str(x)
                        for x in ([p.get("tracking_id")] + list(p.get("all_ids") or []))
                    )
                ]
                if carrier_candidates:
                    carrier_candidates.sort(key=lambda x: x[1].get("mail_date", "") or x[1].get("aktualisiert_am", ""))
                    matching_uids.append(carrier_candidates[0][0])

        if matching_uids:
            # If linking a carrier email into an existing merchant package, keep the merchant UID and merchant items!
            target_uid = matching_uids[0]
            existing_target = self.packages[target_uid]
            is_carrier_incoming = parsed.get("carrier_id") in logistics_carriers
            is_target_merchant = existing_target.get("carrier_id") not in logistics_carriers

            # Merge all_ids
            merged_ids = list(parsed.get("all_ids") or [])
            for m_uid in matching_uids:
                m_pkg = self.packages[m_uid]
                ex_tid = (m_pkg.get("tracking_id") or "").strip()
                for old_id in m_pkg.get("all_ids") or ([ex_tid] if ex_tid else []):
                    if old_id and old_id not in merged_ids:
                        merged_ids.append(old_id)
            parsed["all_ids"] = merged_ids

            if is_carrier_incoming and is_target_merchant:
                # Merge incoming carrier details INTO existing merchant package
                uid = target_uid
                parsed["uid"] = uid
                parsed["carrier_id"] = existing_target.get("carrier_id")
                parsed["zusteller"] = existing_target.get("zusteller")
                parsed["icon"] = existing_target.get("icon")
                parsed["inhalt"] = existing_target.get("inhalt")
                parsed["artikel_liste"] = existing_target.get("artikel_liste")
                parsed["sender"] = existing_target.get("sender")
                parsed["subject"] = existing_target.get("subject")
                parsed["mail_date"] = existing_target.get("mail_date")
                parsed["merchant_tracking_url"] = existing_target.get("tracking_url")
            elif not is_carrier_incoming and not is_target_merchant:
                # Incoming merchant email matches an existing carrier placeholder
                uid = target_uid
                existing_target["inhalt"] = parsed.get("inhalt")
                existing_target["artikel_liste"] = parsed.get("artikel_liste")
                existing_target["carrier_id"] = parsed.get("carrier_id")
                existing_target["zusteller"] = parsed.get("zusteller")
                existing_target["icon"] = parsed.get("icon")
                existing_target["all_ids"] = merged_ids
                existing_target["merchant_tracking_url"] = parsed.get("tracking_url")
                return existing_target
            else:
                matching_uids.sort(
                    key=lambda u: STATUS_RANK.get(self.packages[u].get("status", ""), 0),
                    reverse=True,
                )
                uid = matching_uids[0]
                parsed["uid"] = uid

            # Remove secondary duplicate entries
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

        # Preserve more descriptive content and shop name if new email is from carrier / has generic subject
        if existing and existing.get("inhalt"):
            parsed_inhalt = parsed.get("inhalt", "")
            # If existing has real items or longer descriptive content, keep it!
            if existing.get("artikel_liste") and len(existing.get("artikel_liste", [])) > 1:
                parsed["inhalt"] = existing["inhalt"]
                parsed["artikel_liste"] = existing["artikel_liste"]
            elif any(k in parsed_inhalt.lower() for k in ("sendung", "paket", "ihre", "logistics", "express")):
                parsed["inhalt"] = existing["inhalt"]
                parsed["artikel_liste"] = existing.get("artikel_liste", [existing["inhalt"]])

        # Rule: Always keep the name of the shop from the order confirmation / shop email!
        logistics_carriers = {"dhl", "dpd", "hermes", "gls", "ups"}
        if existing:
            # If existing package is from a shop, keep the shop name, carrier_id, and shop icon!
            if existing.get("carrier_id") not in logistics_carriers:
                parsed["carrier_id"] = existing["carrier_id"]
                parsed["zusteller"] = existing["zusteller"]
                parsed["icon"] = existing.get("icon") or parsed.get("icon")
            elif parsed.get("carrier_id") in logistics_carriers and existing.get("zusteller") not in ("DHL", "DPD", "Hermes", "GLS", "UPS", "Paketdienst"):
                parsed["zusteller"] = existing["zusteller"]
                parsed["icon"] = existing.get("icon") or parsed.get("icon")

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

    def _reconcile_merchant_carrier_packages(self) -> list[str]:
        """Reconcile and merge duplicate carrier packages with active merchant packages."""
        merged_summary = []
        logistics_carriers = {"dhl", "dpd", "hermes", "gls", "ups"}

        # 1. Purge bogus parcel carrier entries without tracking ID (e.g. newsletters)
        for uid, pkg in list(self.packages.items()):
            cid = pkg.get("carrier_id")
            tid = (pkg.get("tracking_id") or "").strip()
            all_ids = pkg.get("all_ids") or []
            if cid in logistics_carriers and not tid and not all_ids:
                merged_summary.append(f"Entfernt (Newsletter ohne Tracking-ID): {uid}")
                self.packages.pop(uid, None)

        # 2. Find active carrier packages representing a merchant shipment (e.g. DHL 'Amazon')
        carrier_pkgs = []
        for uid, pkg in list(self.packages.items()):
            if pkg.get("status") == STATUS_DELIVERED:
                continue
            cid = pkg.get("carrier_id")
            if cid not in logistics_carriers:
                continue
            content = (pkg.get("inhalt") or "").strip().lower()
            subj = (pkg.get("subject") or "").strip().lower()
            if content == "amazon" or "amazon sendung" in subj:
                carrier_pkgs.append((uid, pkg))

        # Find active unlinked merchant (Amazon) packages
        merchant_pkgs = []
        for uid, pkg in list(self.packages.items()):
            if pkg.get("status") == STATUS_DELIVERED:
                continue
            if pkg.get("carrier_id") == "amazon":
                has_carrier_code = any(
                    str(x).startswith("JJD") or str(x).startswith("0034") or str(x).startswith("1Z")
                    for x in ([pkg.get("tracking_id")] + list(pkg.get("all_ids") or []))
                )
                if has_carrier_code:
                    continue

                m_items = {
                    item.strip().lower()
                    for item in (pkg.get("artikel_liste") or [pkg.get("inhalt")])
                    if item and len(item.strip()) >= 5
                }
                already_delivered = any(
                    m_items.issubset({
                        it.strip().lower()
                        for it in (p_other.get("artikel_liste") or [p_other.get("inhalt")])
                        if it and len(it.strip()) >= 5
                    })
                    for u_other, p_other in self.packages.items()
                    if u_other != uid
                    and p_other.get("carrier_id") == "amazon"
                    and p_other.get("status") == STATUS_DELIVERED
                )
                if not already_delivered:
                    merchant_pkgs.append((uid, pkg))

        # Sort both chronologically
        carrier_pkgs.sort(key=lambda x: x[1].get("mail_date", "") or x[1].get("aktualisiert_am", ""))
        merchant_pkgs.sort(key=lambda x: x[1].get("mail_date", "") or x[1].get("aktualisiert_am", ""))

        for (c_uid, c_pkg), (m_uid, m_pkg) in zip(carrier_pkgs, merchant_pkgs):
            c_tid = (c_pkg.get("tracking_id") or "").strip()
            m_ids = list(m_pkg.get("all_ids") or [])
            if c_tid and c_tid not in m_ids:
                m_ids.append(c_tid)
            for cid in c_pkg.get("all_ids") or []:
                if cid and cid not in m_ids:
                    m_ids.append(cid)
            m_pkg["all_ids"] = m_ids

            # Inherit carrier delivery details
            if c_pkg.get("tracking_url"):
                m_pkg["merchant_tracking_url"] = m_pkg.get("tracking_url")
                m_pkg["tracking_url"] = c_pkg["tracking_url"]
            if c_pkg.get("erwartet_am"):
                m_pkg["erwartet_am"] = c_pkg["erwartet_am"]
            if c_pkg.get("zustellung"):
                m_pkg["zustellung"] = c_pkg["zustellung"]
            for attr in ("dhl_status", "dhl_progress", "dhl_event"):
                if c_pkg.get(attr):
                    m_pkg[attr] = c_pkg[attr]

            self.packages.pop(c_uid, None)
            merged_summary.append(f"Zusammengeführt: {c_uid} ({c_tid}) -> {m_uid} ({m_pkg.get('inhalt')[:40]})")

        return merged_summary

    async def async_merge_packages(self, source_uid: str, target_uid: str) -> bool:
        """Manually merge source_uid package into target_uid package."""
        if source_uid not in self.packages or target_uid not in self.packages:
            return False
        s_pkg = self.packages[source_uid]
        t_pkg = self.packages[target_uid]

        merged_ids = list(t_pkg.get("all_ids") or [])
        s_tid = s_pkg.get("tracking_id")
        if s_tid and s_tid not in merged_ids:
            merged_ids.append(s_tid)
        for cid in s_pkg.get("all_ids") or []:
            if cid and cid not in merged_ids:
                merged_ids.append(cid)
        t_pkg["all_ids"] = merged_ids

        # If source is a parcel carrier, inherit live tracking details
        if s_pkg.get("carrier_id") in {"dhl", "dpd", "hermes", "gls", "ups"}:
            if s_pkg.get("tracking_url"):
                t_pkg["merchant_tracking_url"] = t_pkg.get("tracking_url")
                t_pkg["tracking_url"] = s_pkg["tracking_url"]
            if s_pkg.get("erwartet_am"):
                t_pkg["erwartet_am"] = s_pkg["erwartet_am"]
            if s_pkg.get("zustellung"):
                t_pkg["zustellung"] = s_pkg["zustellung"]
            for attr in ("dhl_status", "dhl_progress", "dhl_event"):
                if s_pkg.get(attr):
                    t_pkg[attr] = s_pkg[attr]

        self.packages.pop(source_uid, None)
        await self.async_save_storage()
        self.async_set_updated_data(self._build_state_dict())
        _LOGGER.info("Manually merged package %s into %s", source_uid, target_uid)
        return True

    def _cleanup_old_packages(self) -> None:
        """Remove delivered packages older than cleanup_days and refresh display timing."""
        self._reconcile_merchant_carrier_packages()
        cleanup_days = int(self.get_config(CONF_CLEANUP_DAYS, DEFAULT_CLEANUP_DAYS))
        today = date.today()
        to_remove: list[str] = []

        # Remove known artifact packages from image URLs if present
        if "paket_dhl_457717046790" in self.packages:
            self.packages.pop("paket_dhl_457717046790", None)

        # Cross-package deduplication across self.packages
        uids = list(self.packages.keys())
        for i in range(len(uids)):
            u1 = uids[i]
            if u1 not in self.packages:
                continue
            p1 = self.packages[u1]
            ids1 = {
                x.strip().lower()
                for x in ([p1.get("tracking_id")] + list(p1.get("all_ids") or []))
                if x and str(x).strip() and len(str(x).strip()) >= 5
            }
            for j in range(i + 1, len(uids)):
                u2 = uids[j]
                if u2 not in self.packages:
                    continue
                p2 = self.packages[u2]
                ids2 = {
                    x.strip().lower()
                    for x in ([p2.get("tracking_id")] + list(p2.get("all_ids") or []))
                    if x and str(x).strip() and len(str(x).strip()) >= 5
                }
                if ids1 & ids2:
                    p1_items = len(p1.get("artikel_liste") or [])
                    p2_items = len(p2.get("artikel_liste") or [])
                    p1_rank = STATUS_RANK.get(p1.get("status", ""), 0)
                    p2_rank = STATUS_RANK.get(p2.get("status", ""), 0)
                    logistics_carriers = {"dhl", "dpd", "hermes", "gls", "ups"}
                    p1_is_shop = p1.get("carrier_id") not in logistics_carriers
                    p2_is_shop = p2.get("carrier_id") not in logistics_carriers
                    if p1_is_shop and not p2_is_shop:
                        primary, dup = p1, p2
                        prim_uid, dup_uid = u1, u2
                    elif p2_is_shop and not p1_is_shop:
                        primary, dup = p2, p1
                        prim_uid, dup_uid = u2, u1
                    elif p1_items >= p2_items:
                        primary, dup = p1, p2
                        prim_uid, dup_uid = u1, u2
                    else:
                        primary, dup = p2, p1
                        prim_uid, dup_uid = u2, u1
                    merged = list(primary.get("all_ids") or [])
                    for did in ([dup.get("tracking_id")] + list(dup.get("all_ids") or [])):
                        if did and did not in merged:
                            merged.append(did)
                    primary["all_ids"] = merged
                    if p2_rank > p1_rank:
                        primary["status"] = dup["status"]
                        primary["zustellung"] = dup.get("zustellung") or primary.get("zustellung")
                    if dup.get("erwartet_am"):
                        primary["erwartet_am"] = dup["erwartet_am"]
                    if dup.get("tracking_url") and not primary.get("tracking_url"):
                        primary["tracking_url"] = dup["tracking_url"]
                    self.packages.pop(dup_uid, None)
                    _LOGGER.info("Merged duplicate package %s into %s", dup_uid, prim_uid)

        # Check for duplicate merchant packages where all items were already delivered in another package
        for u_active, p_active in list(self.packages.items()):
            if p_active.get("status") == STATUS_DELIVERED:
                continue
            c_active = p_active.get("carrier_id")
            if not c_active or c_active in logistics_carriers:
                continue
            active_items = {
                item.strip().lower()
                for item in (p_active.get("artikel_liste") or [p_active.get("inhalt")])
                if item and len(item.strip()) >= 5
            }
            if not active_items:
                continue
            for u_other, p_other in list(self.packages.items()):
                if u_other == u_active or p_other.get("carrier_id") != c_active:
                    continue
                if p_other.get("status") != STATUS_DELIVERED:
                    continue
                other_items = {
                    item.strip().lower()
                    for item in (p_other.get("artikel_liste") or [p_other.get("inhalt")])
                    if item and len(item.strip()) >= 5
                }
                if active_items.issubset(other_items):
                    _LOGGER.info(
                        "Cleaning up duplicate active package %s (%s) because items are already delivered in %s",
                        u_active,
                        p_active.get("inhalt", "")[:35],
                        u_other,
                    )
                    self.packages.pop(u_active, None)
                    break

        for uid, pkg in self.packages.items():
            # If package UID indicates a shop (e.g. 'paket_sunlu...') but carrier_id became 'dhl', restore the shop name!
            if uid.startswith("paket_sunlu_") and pkg.get("zusteller") in ("DHL", "DHL Paket", "Sunlu (via DHL)"):
                pkg["carrier_id"] = "sunlu"
                pkg["zusteller"] = "Sunlu"
                pkg["icon"] = "mdi:printer-3d-nozzle"
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
            turl = str(pkg.get("tracking_url") or "").strip().rstrip(")>.,;\"'")

            dhl_code = ""
            for cid in [tid] + list(pkg.get("all_ids") or []):
                cstr = str(cid or "").strip()
                if cstr.startswith("0034") or cstr.startswith("JJD"):
                    dhl_code = cstr
                    break
            is_dhl_redirect = any(
                d in turl.lower()
                for d in ("custcomm.dhl", "logistics.dhl", "paket.de")
            )
            if (dhl_code or is_dhl_redirect or pkg.get("carrier_id") == "dhl") and (dhl_code or tid):
                final_code = dhl_code or tid
                pkg["tracking_url"] = f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={final_code}"
            else:
                pkg["tracking_url"] = turl
            if pkg.get("status") == STATUS_DELIVERED and pkg.get("zugestellt_am"):
                try:
                    deliv_date = date.fromisoformat(str(pkg["zugestellt_am"])[:10])
                    if (today - deliv_date).days >= cleanup_days:
                        to_remove.append(uid)
                except ValueError:
                    pass

        for uid in to_remove:
            self.packages.pop(uid, None)

    async def async_mark_delivered(self, uid: str) -> None:
        """Mark a package as delivered manually."""
        if uid in self.packages:
            pkg = self.packages[uid]
            pkg["status"] = STATUS_DELIVERED
            pkg["zugestellt_am"] = date.today().isoformat()
            pkg["zustellung"] = compute_display_timing(pkg)
            pkg["aktualisiert_am"] = datetime.now().strftime("%d.%m.%Y %H:%M")
            await self.async_save_storage()
            self.async_set_updated_data(self._build_state_dict())
            _LOGGER.info("Manually marked package %s as delivered", uid)

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

    async def async_refresh_carrier_tracking(self) -> None:
        """Poll carrier public tracking API for active shipments."""
        for pkg in list(self.packages.values()):
            if pkg.get("status") == STATUS_DELIVERED:
                continue

            tid = str(pkg.get("tracking_id") or "").strip()
            dhl_code = ""
            for cid in [tid] + list(pkg.get("all_ids") or []):
                cstr = str(cid or "").strip()
                if cstr.startswith("0034") or cstr.startswith("JJD"):
                    dhl_code = cstr
                    break

            if not dhl_code and pkg.get("carrier_id") == "dhl" and tid:
                dhl_code = tid

            if dhl_code:
                try:
                    info = await async_fetch_dhl_tracking(self.hass, dhl_code)
                    if info:
                        if info.get("status_text"):
                            pkg["dhl_status"] = info["status_text"]
                        if info.get("progress"):
                            pkg["dhl_progress"] = info["progress"]
                        if info.get("last_event"):
                            pkg["dhl_event"] = info["last_event"]

                        if info["is_delivered"]:
                            pkg["status"] = STATUS_DELIVERED
                            deliv_d = info.get("current_status_date")
                            pkg["zugestellt_am"] = str(deliv_d)[:10] if deliv_d else date.today().isoformat()
                            pkg["zustellung"] = compute_display_timing(pkg)
                            _LOGGER.info("DHL live tracking marked package %s as delivered", pkg.get("uid"))
                        else:
                            if info.get("expected_date"):
                                pkg["erwartet_am"] = str(info["expected_date"])[:10]
                            step = info.get("progress_step", 0)
                            if step == 4 or "in zustellung" in (info.get("status_text") or "").lower():
                                pkg["status"] = STATUS_OUT_FOR_DELIVERY
                                pkg["zustellung"] = TIMING_TODAY
                            else:
                                if pkg.get("status") != STATUS_OUT_FOR_DELIVERY:
                                    pkg["status"] = STATUS_IN_TRANSIT
                                    pkg["zustellung"] = compute_display_timing(pkg)
                except Exception as err:
                    _LOGGER.debug("Error updating DHL tracking for %s: %s", dhl_code, err)

    async def _async_update_data(self) -> dict[str, Any]:
        """Periodic coordinator update."""
        await self.async_fetch_imap_now()
        await self.async_refresh_carrier_tracking()
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

        arriving_today = [
            p
            for p in in_transit
            if p.get("status") == STATUS_OUT_FOR_DELIVERY
            or p.get("erwartet_am") == today_str
            or p.get("zustellung") == "Ankunft heute"
        ]
        arriving_later = [
            p for p in in_transit if p not in arriving_today
        ]

        del_today_count = len(delivered_today)
        arr_today_count = len(arriving_today)
        arr_later_count = len(arriving_later)
        ordered_count = len(ordered)

        badge_state = f"Pakete {del_today_count}/{arr_today_count}/{arr_later_count}/{ordered_count}"

        return {
            "badge_state": badge_state,
            "delivered_today_count": del_today_count,
            "arriving_today_count": arr_today_count,
            "arriving_later_count": arr_later_count,
            "ordered_count": ordered_count,
            "in_transit_count": len(in_transit),
            "expected_count": len(expected),
            "delivered_total_count": len(delivered_all),
            "packages": self.packages,
            "carriers": self.carriers,
        }
