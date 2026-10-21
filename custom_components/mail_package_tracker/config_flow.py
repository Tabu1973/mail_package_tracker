"""Config flow and interactive Mail-Assistant Options flow for Mail Package Tracker."""
from __future__ import annotations

import copy
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    BooleanSelector,
    IconSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

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
    MODE_EVENT,
    MODE_IMAP,
)
from .imap_client import test_imap_connection_sync
from .parser import parse_email_with_rules, slugify_id


def _list_to_multiline(items: list[str] | None) -> str:
    """Convert list of strings to comma/newline-separated string for UI."""
    if not items:
        return ""
    return "\n".join(str(x).strip() for x in items if str(x).strip())


def _multiline_to_list(raw: str | None) -> list[str]:
    """Convert comma or newline separated string from UI into clean list."""
    if not raw:
        return []
    parts: list[str] = []
    for line in str(raw).splitlines():
        for chunk in line.split(","):
            val = chunk.strip()
            if val and val not in parts:
                parts.append(val)
    return parts


def _extract_domain_and_name(sender: str) -> tuple[str, str]:
    """Guess sender domain pattern and carrier display name from From header."""
    m = re.search(r"@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", sender or "")
    if m:
        full_dom = m.group(1).lower()
        parts = full_dom.split(".")
        if len(parts) >= 2:
            main_name = parts[-2]
            if main_name in ("co", "com", "mail", "order", "notice", "service", "info") and len(parts) >= 3:
                main_name = parts[-3]
            return f"{main_name}.{parts[-1]}", main_name.capitalize()
        return full_dom, full_dom.capitalize()
    return sender.strip(), "Neuer Händler"


class MailPackageTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mail Package Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            mode = user_input.get(CONF_MODE, MODE_BOTH)
            host = user_input.get(CONF_IMAP_HOST, DEFAULT_IMAP_HOST)
            port = int(user_input.get(CONF_IMAP_PORT, DEFAULT_IMAP_PORT))
            user = (user_input.get(CONF_IMAP_USER) or "").strip()
            password = user_input.get(CONF_IMAP_PASSWORD) or ""
            folder = (user_input.get(CONF_IMAP_FOLDER) or DEFAULT_IMAP_FOLDER).strip()

            if mode in (MODE_BOTH, MODE_IMAP) and user and password:
                try:
                    ok = await self.hass.async_add_executor_job(
                        test_imap_connection_sync, host, port, user, password, folder
                    )
                    if not ok:
                        errors["base"] = "cannot_connect"
                except Exception:
                    errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title="Mail Package Tracker",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_MODE, default=MODE_BOTH): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(
                                value=MODE_BOTH,
                                label="Beides (Eigener IMAP-Abruf + HA imap_content Event-Listener)",
                            ),
                            SelectOptionDict(
                                value=MODE_IMAP,
                                label="Nur eigener IMAP-Abruf (direktes Postfach-Scanning)",
                            ),
                            SelectOptionDict(
                                value=MODE_EVENT,
                                label="Nur HA imap_content Events (bestehende IMAP-Integration nutzen)",
                            ),
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_IMAP_HOST, default=DEFAULT_IMAP_HOST): TextSelector(),
                vol.Optional(CONF_IMAP_PORT, default=DEFAULT_IMAP_PORT): NumberSelector(
                    NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_IMAP_USER, default=""): TextSelector(),
                vol.Optional(CONF_IMAP_PASSWORD, default=""): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Optional(CONF_IMAP_FOLDER, default=DEFAULT_IMAP_FOLDER): TextSelector(),
                vol.Optional(CONF_DAYS_BACK, default=DEFAULT_DAYS_BACK): NumberSelector(
                    NumberSelectorConfig(min=1, max=14, step=1, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): NumberSelector(
                    NumberSelectorConfig(min=1, max=60, step=1, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_CLEANUP_DAYS, default=DEFAULT_CLEANUP_DAYS): NumberSelector(
                    NumberSelectorConfig(min=1, max=30, step=1, mode=NumberSelectorMode.BOX)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return MailPackageTrackerOptionsFlow(config_entry)


class MailPackageTrackerOptionsFlow(config_entries.OptionsFlow):
    """Options flow for managing carrier rules, email assistant, and settings."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.entry = config_entry
        self._selected_email: dict[str, Any] | None = None
        self._selected_carrier_id: str | None = None
        self._test_result_text: str = ""

    def _get_coordinator(self):
        return self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show main configuration menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "rule_from_email",
                "manage_carriers",
                "add_carrier",
                "test_email",
                "general_settings",
            ],
        )

    # -------------------------------------------------------------------------
    # 1. Interactive Mail-Assistant: Create/Update Rule by viewing an Email
    # -------------------------------------------------------------------------
    async def async_step_rule_from_email(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let the user pick one of the recent emails from the inbox to inspect and build a rule."""
        coord = self._get_coordinator()
        if coord:
            await coord.async_fetch_imap_now()
            emails = coord.recent_emails
        else:
            emails = []

        if user_input is not None:
            selected_idx = int(user_input.get("email_index", 0))
            if 0 <= selected_idx < len(emails):
                self._selected_email = emails[selected_idx]
                return await self.async_step_configure_rule_from_email()

        if not emails:
            return self.async_show_form(
                step_id="no_emails_found",
                data_schema=vol.Schema({}),
            )

        options: list[SelectOptionDict] = []
        for idx, mail in enumerate(emails[:30]):
            subj = (mail.get("subject") or "(Kein Betreff)")[:55]
            snd = (mail.get("sender") or "")[:35]
            dt = (mail.get("date") or "")[:16]
            options.append(
                SelectOptionDict(
                    value=str(idx),
                    label=f"[{dt}] {snd} — {subj}",
                )
            )

        schema = vol.Schema(
            {
                vol.Required("email_index", default="0"): SelectSelector(
                    SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
                )
            }
        )
        return self.async_show_form(step_id="rule_from_email", data_schema=schema)

    async def async_step_no_emails_found(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Fallback when no recent emails are in cache yet."""
        return await self.async_step_add_carrier()

    async def async_step_configure_rule_from_email(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Display the full email content so user can copy passages and save carrier rule."""
        mail = self._selected_email or {}
        sender = mail.get("sender", "")
        subject = mail.get("subject", "")
        body = mail.get("text", "")

        if user_input is not None:
            name = (user_input.get("name") or "Neuer Händler").strip()
            carrier_id = slugify_id(name, 20)
            coord = self._get_coordinator()
            existing = coord.carriers.get(carrier_id, {}) if coord else {}

            rule_data = {
                "id": carrier_id,
                "name": name,
                "icon": user_input.get("icon", "mdi:package-variant"),
                "enabled": True,
                "is_preset": existing.get("is_preset", False),
                "sender_patterns": _multiline_to_list(user_input.get("sender_patterns")),
                "subject_patterns": _multiline_to_list(user_input.get("subject_patterns")),
                "ordered_patterns": _multiline_to_list(user_input.get("ordered_patterns")),
                "in_transit_patterns": _multiline_to_list(user_input.get("in_transit_patterns")),
                "out_for_delivery_patterns": _multiline_to_list(user_input.get("out_for_delivery_patterns")),
                "delivered_patterns": _multiline_to_list(user_input.get("delivered_patterns")),
                "tomorrow_patterns": _multiline_to_list(user_input.get("tomorrow_patterns")),
                "exclude_patterns": _multiline_to_list(user_input.get("exclude_patterns")),
                "tracking_regex": (user_input.get("tracking_regex") or "").strip(),
                "tracking_url_regex": (user_input.get("tracking_url_regex") or existing.get("tracking_url_regex", "")).strip(),
                "default_tracking_url": (user_input.get("default_tracking_url") or "").strip(),
                "content_regex": (user_input.get("content_regex") or "").strip(),
            }
            if coord:
                await coord.async_upsert_carrier(carrier_id, rule_data)
            return self.async_create_entry(title="", data=dict(self.entry.options))

        guessed_domain, guessed_name = _extract_domain_and_name(sender)
        coord = self._get_coordinator()
        existing_rule = None
        if coord:
            for r in coord.carriers.values():
                if any(p.lower() in sender.lower() for p in r.get("sender_patterns", [])):
                    existing_rule = r
                    break

        mail_display = (
            f"ABSENDER: {sender}\n"
            f"BETREFF: {subject}\n"
            f"{'-' * 50}\n"
            f"{body[:2500]}"
        )

        schema = self._build_carrier_form_schema(
            default_name=existing_rule["name"] if existing_rule else guessed_name,
            default_icon=existing_rule.get("icon", "mdi:package-variant") if existing_rule else "mdi:package-variant",
            default_enabled=True,
            default_sender=_list_to_multiline(existing_rule["sender_patterns"]) if existing_rule else guessed_domain,
            default_subject=_list_to_multiline(existing_rule.get("subject_patterns")) if existing_rule else "",
            default_ordered=_list_to_multiline(existing_rule.get("ordered_patterns"))
            if existing_rule
            else "bestellbestätigung\nvielen dank für deine bestellung\nbestätigt\norder confirmed",
            default_transit=_list_to_multiline(existing_rule.get("in_transit_patterns"))
            if existing_rule
            else "versandt\nversendet\nunterwegs\nauf dem weg\non the way\nshipped",
            default_ofd=_list_to_multiline(existing_rule.get("out_for_delivery_patterns"))
            if existing_rule
            else "in zustellung\nkommt heute\nout for delivery",
            default_delivered=_list_to_multiline(existing_rule.get("delivered_patterns"))
            if existing_rule
            else "wurde zugestellt\nwurde geliefert\ndelivered",
            default_tomorrow=_list_to_multiline(existing_rule.get("tomorrow_patterns"))
            if existing_rule
            else "morgen\ntomorrow",
            default_exclude=_list_to_multiline(existing_rule.get("exclude_patterns"))
            if existing_rule
            else "newsletter\nstorniert",
            default_tracking_regex=existing_rule.get("tracking_regex", "") if existing_rule else "Sendungsnummer:, Trackingnummer:, Bestellung",
            default_url_regex=existing_rule.get("tracking_url_regex", "") if existing_rule else "dhl, dpd, hermes, gls, ups, tracking",
            default_url=existing_rule.get("default_tracking_url", "") if existing_rule else "",
            default_content_regex=existing_rule.get("content_regex", "") if existing_rule else "",
            mail_preview=mail_display,
        )

        return self.async_show_form(
            step_id="configure_rule_from_email",
            data_schema=schema,
        )

    # -------------------------------------------------------------------------
    # 2. Manage Existing Carriers (Edit / Enable / Disable / Delete)
    # -------------------------------------------------------------------------
    async def async_step_manage_carriers(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select an existing carrier rule to edit or delete."""
        coord = self._get_coordinator()
        carriers = coord.carriers if coord else DEFAULT_CARRIERS

        if user_input is not None:
            self._selected_carrier_id = user_input.get("carrier_id")
            if user_input.get("delete_carrier"):
                if coord and self._selected_carrier_id:
                    await coord.async_delete_carrier(self._selected_carrier_id)
                return self.async_create_entry(title="", data=dict(self.entry.options))
            return await self.async_step_edit_carrier()

        options = [
            SelectOptionDict(
                value=cid,
                label=f"{c.get('name', cid)} ({'Aktiv' if c.get('enabled', True) else 'Deaktiviert'})",
            )
            for cid, c in carriers.items()
        ]

        schema = vol.Schema(
            {
                vol.Required("carrier_id", default=next(iter(carriers.keys()), "amazon")): SelectSelector(
                    SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
                ),
                vol.Optional("delete_carrier", default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="manage_carriers", data_schema=schema)

    async def async_step_edit_carrier(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit the selected carrier's rules."""
        coord = self._get_coordinator()
        carriers = coord.carriers if coord else copy.deepcopy(DEFAULT_CARRIERS)
        cid = self._selected_carrier_id or "amazon"
        rule = carriers.get(cid, DEFAULT_CARRIERS.get("amazon", {}))

        if user_input is not None:
            updated = {
                "id": cid,
                "name": (user_input.get("name") or rule.get("name", cid)).strip(),
                "icon": user_input.get("icon", rule.get("icon", "mdi:package-variant")),
                "enabled": bool(user_input.get("enabled", True)),
                "is_preset": rule.get("is_preset", False),
                "sender_patterns": _multiline_to_list(user_input.get("sender_patterns")),
                "subject_patterns": _multiline_to_list(user_input.get("subject_patterns")),
                "ordered_patterns": _multiline_to_list(user_input.get("ordered_patterns")),
                "in_transit_patterns": _multiline_to_list(user_input.get("in_transit_patterns")),
                "out_for_delivery_patterns": _multiline_to_list(user_input.get("out_for_delivery_patterns")),
                "delivered_patterns": _multiline_to_list(user_input.get("delivered_patterns")),
                "tomorrow_patterns": _multiline_to_list(user_input.get("tomorrow_patterns")),
                "exclude_patterns": _multiline_to_list(user_input.get("exclude_patterns")),
                "tracking_regex": (user_input.get("tracking_regex") or "").strip(),
                "tracking_url_regex": (user_input.get("tracking_url_regex") or "").strip(),
                "default_tracking_url": (user_input.get("default_tracking_url") or "").strip(),
                "content_regex": (user_input.get("content_regex") or "").strip(),
            }
            if coord:
                await coord.async_upsert_carrier(cid, updated)
            return self.async_create_entry(title="", data=dict(self.entry.options))

        schema = self._build_carrier_form_schema(
            default_name=rule.get("name", cid),
            default_icon=rule.get("icon", "mdi:package-variant"),
            default_enabled=rule.get("enabled", True),
            default_sender=_list_to_multiline(rule.get("sender_patterns")),
            default_subject=_list_to_multiline(rule.get("subject_patterns")),
            default_ordered=_list_to_multiline(rule.get("ordered_patterns")),
            default_transit=_list_to_multiline(rule.get("in_transit_patterns")),
            default_ofd=_list_to_multiline(rule.get("out_for_delivery_patterns")),
            default_delivered=_list_to_multiline(rule.get("delivered_patterns")),
            default_tomorrow=_list_to_multiline(rule.get("tomorrow_patterns")),
            default_exclude=_list_to_multiline(rule.get("exclude_patterns")),
            default_tracking_regex=rule.get("tracking_regex", ""),
            default_url_regex=rule.get("tracking_url_regex", ""),
            default_url=rule.get("default_tracking_url", ""),
            default_content_regex=rule.get("content_regex", ""),
        )
        return self.async_show_form(step_id="edit_carrier", data_schema=schema)

    # -------------------------------------------------------------------------
    # 3. Manually Add a New Carrier
    # -------------------------------------------------------------------------
    async def async_step_add_carrier(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Create a new custom carrier rule."""
        if user_input is not None:
            name = (user_input.get("name") or "Neuer Händler").strip()
            cid = slugify_id(name, 20)
            new_rule = {
                "id": cid,
                "name": name,
                "icon": user_input.get("icon", "mdi:package-variant"),
                "enabled": bool(user_input.get("enabled", True)),
                "is_preset": False,
                "sender_patterns": _multiline_to_list(user_input.get("sender_patterns")),
                "subject_patterns": _multiline_to_list(user_input.get("subject_patterns")),
                "ordered_patterns": _multiline_to_list(user_input.get("ordered_patterns")),
                "in_transit_patterns": _multiline_to_list(user_input.get("in_transit_patterns")),
                "out_for_delivery_patterns": _multiline_to_list(user_input.get("out_for_delivery_patterns")),
                "delivered_patterns": _multiline_to_list(user_input.get("delivered_patterns")),
                "tomorrow_patterns": _multiline_to_list(user_input.get("tomorrow_patterns")),
                "exclude_patterns": _multiline_to_list(user_input.get("exclude_patterns")),
                "tracking_regex": (user_input.get("tracking_regex") or "").strip(),
                "tracking_url_regex": (user_input.get("tracking_url_regex") or "").strip(),
                "default_tracking_url": (user_input.get("default_tracking_url") or "").strip(),
                "content_regex": (user_input.get("content_regex") or "").strip(),
            }
            coord = self._get_coordinator()
            if coord:
                await coord.async_upsert_carrier(cid, new_rule)
            return self.async_create_entry(title="", data=dict(self.entry.options))

        schema = self._build_carrier_form_schema(
            default_name="",
            default_icon="mdi:package-variant",
            default_enabled=True,
            default_sender="",
            default_subject="",
            default_ordered="bestellbestätigung\nvielen dank für deine bestellung\nbestätigt\norder confirmed",
            default_transit="versandt\nversendet\nunterwegs\nauf dem weg\non the way\nshipped",
            default_ofd="in zustellung\nkommt heute\nout for delivery",
            default_delivered="wurde zugestellt\nwurde geliefert\ndelivered",
            default_tomorrow="morgen\ntomorrow",
            default_exclude="newsletter\nstorniert",
            default_tracking_regex="Sendungsnummer:, Trackingnummer:, Bestellung",
            default_url_regex="dhl, dpd, hermes, gls, ups, tracking",
            default_url="",
            default_content_regex="",
        )
        return self.async_show_form(step_id="add_carrier", data_schema=schema)

    # -------------------------------------------------------------------------
    # 4. Live Email Tester
    # -------------------------------------------------------------------------
    async def async_step_test_email(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Test rules against pasted email text and view parsed result."""
        coord = self._get_coordinator()
        carriers = coord.carriers if coord else DEFAULT_CARRIERS

        if user_input is not None:
            if user_input.get("finish"):
                return self.async_create_entry(title="", data=dict(self.entry.options))

            sender = user_input.get("test_sender", "")
            subject = user_input.get("test_subject", "")
            body = user_input.get("test_body", "")
            res = parse_email_with_rules(sender, subject, body, carriers)

            if res.get("matched"):
                self._test_result_text = (
                    f"✅ TREFFER!\n"
                    f"• Händler/Dienst: {res.get('zusteller')} ({res.get('carrier_id')})\n"
                    f"• Status: {res.get('status')} ({res.get('zustellung')})\n"
                    f"• Inhalt: {res.get('inhalt')}\n"
                    f"• Tracking-ID: {res.get('tracking_id') or '(keine, Fallback über Betreff)'}\n"
                    f"• Sensor-ID: sensor.{res.get('uid')}\n"
                    f"• Tracking-URL: {res.get('tracking_url')}\n"
                    f"• Grund: {res.get('matched_reason')}"
                )
            else:
                self._test_result_text = (
                    f"❌ KEIN TREFFER\n"
                    f"• Grund: {res.get('reason')}"
                )

        fields: dict[Any, Any] = {}
        if self._test_result_text:
            fields[vol.Optional("test_result", default=self._test_result_text)] = TextSelector(
                TextSelectorConfig(multiline=True)
            )
        fields.update(
            {
                vol.Optional("test_sender", default="service@sunlu.com"): TextSelector(),
                vol.Optional(
                    "test_subject",
                    default="A shipment from order #DE12345 is on the way",
                ): TextSelector(),
                vol.Optional(
                    "test_body",
                    default="Your order is on the way. Tracking number: 00340434123456789012",
                ): TextSelector(TextSelectorConfig(multiline=True)),
                vol.Optional("finish", default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="test_email", data_schema=vol.Schema(fields))

    # -------------------------------------------------------------------------
    # 5. General & IMAP Settings
    # -------------------------------------------------------------------------
    async def async_step_general_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Update IMAP connection and cleanup settings."""
        coord = self._get_coordinator()

        def _val(key: str, default: Any) -> Any:
            return coord.get_config(key, default) if coord else self.entry.data.get(key, default)

        if user_input is not None:
            new_options = dict(self.entry.options)
            new_options.update(user_input)
            return self.async_create_entry(title="", data=new_options)

        schema = vol.Schema(
            {
                vol.Required(CONF_MODE, default=_val(CONF_MODE, MODE_BOTH)): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(
                                value=MODE_BOTH,
                                label="Beides (Eigener IMAP-Abruf + HA imap_content Event-Listener)",
                            ),
                            SelectOptionDict(
                                value=MODE_IMAP,
                                label="Nur eigener IMAP-Abruf",
                            ),
                            SelectOptionDict(
                                value=MODE_EVENT,
                                label="Nur HA imap_content Events",
                            ),
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_IMAP_HOST, default=_val(CONF_IMAP_HOST, DEFAULT_IMAP_HOST)): TextSelector(),
                vol.Optional(CONF_IMAP_PORT, default=_val(CONF_IMAP_PORT, DEFAULT_IMAP_PORT)): NumberSelector(
                    NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_IMAP_USER, default=_val(CONF_IMAP_USER, "")): TextSelector(),
                vol.Optional(CONF_IMAP_PASSWORD, default=_val(CONF_IMAP_PASSWORD, "")): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Optional(CONF_IMAP_FOLDER, default=_val(CONF_IMAP_FOLDER, DEFAULT_IMAP_FOLDER)): TextSelector(),
                vol.Optional(CONF_DAYS_BACK, default=_val(CONF_DAYS_BACK, DEFAULT_DAYS_BACK)): NumberSelector(
                    NumberSelectorConfig(min=1, max=14, step=1, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=_val(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): NumberSelector(
                    NumberSelectorConfig(min=1, max=60, step=1, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_CLEANUP_DAYS, default=_val(CONF_CLEANUP_DAYS, DEFAULT_CLEANUP_DAYS)): NumberSelector(
                    NumberSelectorConfig(min=1, max=30, step=1, mode=NumberSelectorMode.BOX)
                ),
            }
        )
        return self.async_show_form(step_id="general_settings", data_schema=schema)

    def _build_carrier_form_schema(
        self,
        default_name: str,
        default_icon: str,
        default_enabled: bool,
        default_sender: str,
        default_subject: str,
        default_ordered: str,
        default_transit: str,
        default_ofd: str,
        default_delivered: str,
        default_tomorrow: str,
        default_exclude: str,
        default_tracking_regex: str,
        default_url_regex: str,
        default_url: str,
        default_content_regex: str,
        mail_preview: str | None = None,
    ) -> vol.Schema:
        """Build schema for adding/editing a carrier rule."""
        fields: dict[Any, Any] = {}
        if mail_preview is not None:
            fields[vol.Optional("mail_preview", default=mail_preview)] = TextSelector(
                TextSelectorConfig(multiline=True)
            )

        fields.update(
            {
                vol.Required("name", default=default_name): TextSelector(),
                vol.Optional("icon", default=default_icon): IconSelector(),
                vol.Optional("enabled", default=default_enabled): BooleanSelector(),
                vol.Optional("sender_patterns", default=default_sender): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
                vol.Optional("subject_patterns", default=default_subject): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
                vol.Optional("ordered_patterns", default=default_ordered): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
                vol.Optional("in_transit_patterns", default=default_transit): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
                vol.Optional("out_for_delivery_patterns", default=default_ofd): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
                vol.Optional("delivered_patterns", default=default_delivered): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
                vol.Optional("tomorrow_patterns", default=default_tomorrow): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
                vol.Optional("exclude_patterns", default=default_exclude): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
                vol.Optional("tracking_regex", default=default_tracking_regex): TextSelector(),
                vol.Optional("content_regex", default=default_content_regex): TextSelector(),
                vol.Optional("tracking_url_regex", default=default_url_regex): TextSelector(),
                vol.Optional("default_tracking_url", default=default_url): TextSelector(),
            }
        )
        return vol.Schema(fields)
