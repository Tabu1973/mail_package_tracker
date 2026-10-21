"""Email and rule parser for Mail Package Tracker."""
from __future__ import annotations

from datetime import datetime
import html
import re
from typing import Any

from .const import (
    STATUS_DELIVERED,
    STATUS_IN_TRANSIT,
    STATUS_ORDERED,
    STATUS_OUT_FOR_DELIVERY,
    TIMING_DELIVERED_TODAY,
    TIMING_ORDERED,
    TIMING_SOON,
    TIMING_TODAY,
    TIMING_TOMORROW,
)

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HREF_RE = re.compile(r'href=[\'"](https?://[^\'">\s]+)[\'"]', re.IGNORECASE)
_STYLE_SCRIPT_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_WHITESPACE_RE = re.compile(r"[ \t]+")
_NEWLINES_RE = re.compile(r"\n{3,}")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def clean_email_body(raw_text: str, raw_html: str = "") -> tuple[str, list[str]]:
    """Return cleaned plain text and list of extracted URLs from text + HTML."""
    urls: list[str] = []

    if raw_html:
        for match in _HREF_RE.findall(raw_html):
            unescaped = html.unescape(match).strip()
            if unescaped not in urls:
                urls.append(unescaped)

    source = raw_text.strip() if raw_text and raw_text.strip() else raw_html
    if not source:
        return "", urls

    # Strip script/style blocks and HTML tags if present
    cleaned = _STYLE_SCRIPT_RE.sub(" ", source)
    cleaned = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</li>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = _HTML_TAG_RE.sub(" ", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    cleaned = "\n".join(line.strip() for line in cleaned.splitlines())
    cleaned = _NEWLINES_RE.sub("\n\n", cleaned).strip()

    for match in re.findall(r"(https?://[^\s\"'<>]+)", cleaned):
        if match not in urls:
            urls.append(match)

    return cleaned, urls


def slugify_id(value: str, max_len: int = 28) -> str:
    """Create a safe Home Assistant slug from a string."""
    val = value.lower()
    for k, v in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        val = val.replace(k, v)
    slug = _SLUG_RE.sub("_", val).strip("_")
    return slug[:max_len].strip("_") or "paket"


def _split_top_level_pipes(regex_str: str) -> list[str]:
    """Split a regex string by '|' only at top-level (outside parentheses/brackets)."""
    parts: list[str] = []
    current: list[str] = []
    depth_paren = 0
    depth_bracket = 0
    escaped = False
    for ch in regex_str:
        if escaped:
            current.append(ch)
            escaped = False
            continue
        if ch == "\\":
            current.append(ch)
            escaped = True
            continue
        if ch == "[" and depth_bracket == 0:
            depth_bracket = 1
        elif ch == "]" and depth_bracket > 0:
            depth_bracket = 0
        elif depth_bracket == 0:
            if ch == "(":
                depth_paren += 1
            elif ch == ")" and depth_paren > 0:
                depth_paren -= 1
            elif ch == "|" and depth_paren == 0:
                part = "".join(current).strip()
                if part:
                    parts.append(part)
                current = []
                continue
        current.append(ch)
    last = "".join(current).strip()
    if last:
        parts.append(last)
    return parts


def _iter_pattern_candidates(pattern_str: str) -> list[str]:
    """Yield pattern candidates split by top-level '|', newlines, and (for non-regex) commas."""
    candidates: list[str] = []
    for sub_pat in _split_top_level_pipes(pattern_str):
        for line_pat in [p.strip() for p in sub_pat.splitlines() if p.strip()]:
            if "(" not in line_pat and "[" not in line_pat and "\\" not in line_pat and "," in line_pat:
                for chunk in line_pat.split(","):
                    if chunk.strip():
                        candidates.append(chunk.strip())
            else:
                candidates.append(line_pat)
    return candidates


def _extract_all_tracking_by_pattern(text: str, pattern_str: str) -> list[str]:
    """Extract all matching tracking/order numbers in priority order using plain-text labels or regex."""
    found: list[str] = []
    for line_pat in _iter_pattern_candidates(pattern_str):
        # 1. If the user pasted a plain-text prefix from the email (e.g. "DHL Trackingnummer:" or "Bestellnr.")
        if "(" not in line_pat and "[" not in line_pat and "\\" not in line_pat:
            prefix_escaped = re.escape(line_pat.rstrip(":= \t"))
            m = re.search(
                rf"{prefix_escaped}[:=\s\n\r]*#?([A-Za-z0-9][A-Za-z0-9_-]{{4,29}})",
                text,
                re.IGNORECASE,
            )
            if m:
                val = m.group(1).strip("#").strip()
                if val and val not in found:
                    found.append(val)
                continue

        # 2. Otherwise evaluate as regex
        try:
            m = re.search(line_pat, text, re.IGNORECASE)
            if m:
                groups = [g for g in m.groups() if g]
                val = groups[0] if groups else m.group(0)
                val = re.sub(r"^shipmentId=", "", val, flags=re.IGNORECASE)
                val = val.strip("#").strip()
                if val and val not in found:
                    found.append(val)
        except re.error:
            continue
    return found


def _extract_items_by_pattern(clean_body: str, pattern_str: str) -> list[str]:
    """Extract package item(s) using either a plain-text section header/bullet copied from the email or a regex."""
    items_found: list[str] = []
    for line_pat in _iter_pattern_candidates(pattern_str):
        # 1. Plain-text bullet or section header (e.g. "Artikel in dieser Lieferung" or "*")
        if "(" not in line_pat and "[" not in line_pat and "\\" not in line_pat:
            if line_pat in ("*", "-", "•"):
                bullet_esc = re.escape(line_pat)
                for m in re.finditer(rf"^{bullet_esc}\s+([^\n\r]{{4,}})", clean_body, re.MULTILINE):
                    it = m.group(1).strip()
                    if it and it not in items_found:
                        items_found.append(it)
            else:
                # Section header copied from email: grab non-empty lines following the header
                hdr_esc = re.escape(line_pat)
                m = re.search(rf"{hdr_esc}[ \t]*\r?\n(?:\s*[-=*_]+\s*\r?\n)?([\s\S]{{1,1200}})", clean_body, re.IGNORECASE)
                if m:
                    block = m.group(1)
                    # Check if block contains quantity markers like "× 1 ..."
                    qty_matches = re.findall(r"×\s*([0-9]+\s+[^\n\r]+)", block)
                    if qty_matches:
                        for qm in qty_matches:
                            if qm.strip() not in items_found:
                                items_found.append(qm.strip())
                    else:
                        for raw_line in block.splitlines():
                            ln = raw_line.strip()
                            if not ln or set(ln) <= {"-", "=", "*", "_"}:
                                continue
                            if any(stop in ln.lower() for stop in ("falls du fragen hast", "summe", "vielen dank", "http://", "https://")):
                                break
                            if ln not in items_found:
                                items_found.append(ln)
                            if len(items_found) >= 5:
                                break
            if items_found:
                return items_found

        # 2. Otherwise evaluate as regex
        try:
            for m in re.finditer(line_pat, clean_body, re.IGNORECASE | re.MULTILINE):
                groups = [g for g in m.groups() if g]
                item_str = (groups[0] if groups else m.group(0)).strip()
                if item_str and item_str not in items_found:
                    items_found.append(item_str)
            if items_found:
                return items_found
        except re.error:
            continue
    return items_found


def _matches_any(text_lower: str, patterns: list[str]) -> str | None:
    """Return the first matching pattern (case-insensitive substring or regex) or None."""
    for pat in patterns:
        p = pat.strip()
        if not p:
            continue
        p_low = p.lower()
        if p_low in text_lower:
            return p
        try:
            if re.search(p, text_lower, re.IGNORECASE):
                return p
        except re.error:
            pass
    return None


def parse_email_with_rules(
    sender: str,
    subject: str,
    body_text: str,
    carriers: dict[str, dict[str, Any]],
    body_html: str = "",
    email_date: str | None = None,
) -> dict[str, Any]:
    """Evaluate an email against all enabled carrier rules and return structured result."""
    clean_body, extracted_urls = clean_email_body(body_text, body_html)
    urls_text = " ".join(extracted_urls)

    sender_clean = (sender or "").strip()
    subject_clean = " ".join((subject or "").splitlines()).strip()
    sender_lower = sender_clean.lower()
    subject_lower = subject_clean.lower()
    body_lower = clean_body.lower()
    combined_raw = f"{subject_clean}\n{clean_body}\n{urls_text}"
    combined_lower = combined_raw.lower()

    matched_carrier: dict[str, Any] | None = None
    matched_reason = ""

    # 1. Find matching carrier by sender_patterns or subject_patterns
    for carrier_id, rule in carriers.items():
        if not rule.get("enabled", True):
            continue
        sender_pats = rule.get("sender_patterns", [])
        subject_pats = rule.get("subject_patterns", [])

        s_match = _matches_any(sender_lower, sender_pats)
        if s_match:
            matched_carrier = rule
            matched_reason = f"Absender-Treffer: '{s_match}'"
            break

        subj_match = _matches_any(subject_lower, subject_pats)
        if subj_match:
            matched_carrier = rule
            matched_reason = f"Betreff-Treffer: '{subj_match}'"
            break

    if not matched_carrier:
        return {
            "matched": False,
            "reason": "Kein passender Händler/Paketdienst für Absender oder Betreff gefunden.",
            "sender": sender_clean,
            "subject": subject_clean,
        }

    carrier_id = matched_carrier.get("id", "paket")
    carrier_name = matched_carrier.get("name", "Paketdienst")

    # 2. Check exclude patterns
    exclude_pats = matched_carrier.get("exclude_patterns", [])
    excl_hit = _matches_any(f"{sender_lower} {subject_lower}", exclude_pats)
    if excl_hit:
        return {
            "matched": False,
            "carrier_id": carrier_id,
            "carrier_name": carrier_name,
            "reason": f"Ausgeschlossen durch Ausschluss-Regel: '{excl_hit}'",
            "sender": sender_clean,
            "subject": subject_clean,
        }

    # 3. Determine delivery status & timing
    delivered_pats = matched_carrier.get("delivered_patterns", [])
    ofd_pats = matched_carrier.get("out_for_delivery_patterns", [])
    transit_pats = matched_carrier.get("in_transit_patterns", [])
    ordered_pats = matched_carrier.get("ordered_patterns", [])
    tomorrow_pats = matched_carrier.get("tomorrow_patterns", [])

    deliv_hit = _matches_any(combined_lower, delivered_pats)
    ofd_hit = _matches_any(combined_lower, ofd_pats)
    transit_hit = _matches_any(combined_lower, transit_pats)
    ordered_hit = _matches_any(combined_lower, ordered_pats)
    ordered_subj_hit = _matches_any(subject_lower, ordered_pats)
    tomorrow_hit = _matches_any(combined_lower, tomorrow_pats)

    # Guard against progress-bar or boilerplate keywords in body when subject explicitly states status
    if subject_lower.startswith(("bestellt:", "bestellbestätigung", "order confirmed")) or ordered_subj_hit:
        deliv_hit = None
        ofd_hit = None
        transit_hit = None
    elif subject_lower.startswith(("versendet:", "shipped:")):
        deliv_hit = None
        ofd_hit = None
    elif subject_lower.startswith(("in zustellung:", "out for delivery:")):
        deliv_hit = None

    if not (deliv_hit or ofd_hit or transit_hit or ordered_hit):
        return {
            "matched": False,
            "carrier_id": carrier_id,
            "carrier_name": carrier_name,
            "reason": (
                f"Händler '{carrier_name}' erkannt ({matched_reason}), aber kein Status-Schlagwort "
                "(Bestellt / Unterwegs / In Zustellung / Zugestellt) gefunden."
            ),
            "sender": sender_clean,
            "subject": subject_clean,
        }

    if deliv_hit:
        status = STATUS_DELIVERED
        timing = TIMING_DELIVERED_TODAY
        status_keyword = deliv_hit
    elif ofd_hit:
        status = STATUS_OUT_FOR_DELIVERY
        timing = TIMING_TODAY
        status_keyword = ofd_hit
    elif transit_hit:
        status = STATUS_IN_TRANSIT
        if tomorrow_hit:
            timing = TIMING_TOMORROW
        elif _matches_any(
            combined_lower,
            ["ankunft heute", "lieferung heute", "zustellung heute", "kommt heute", "arriving today"],
        ):
            timing = TIMING_TODAY
        else:
            timing = TIMING_SOON
        status_keyword = transit_hit
    else:
        status = STATUS_ORDERED
        timing = TIMING_ORDERED
        status_keyword = ordered_hit or ""

    # 4. Extract Tracking Number / Order ID (supports plain-text prefixes like 'DHL Trackingnummer:' or Regex)
    all_ids: list[str] = []
    tracking_regex = (matched_carrier.get("tracking_regex") or "").strip()
    if tracking_regex:
        all_ids = _extract_all_tracking_by_pattern(combined_raw, tracking_regex)
    tracking_id = all_ids[0] if all_ids else ""

    # 5. Extract Content / Product Name (supports section headers like 'Artikel in dieser Lieferung', bullets '*', or Regex)
    content = ""
    items_found: list[str] = []
    content_regex = (matched_carrier.get("content_regex") or "").strip()
    if content_regex:
        items_found = _extract_items_by_pattern(clean_body, content_regex)

    if len(items_found) == 1:
        content = items_found[0]
    elif len(items_found) > 1:
        short_items = [
            (it[:28].rstrip(" ,;-") + "…" if len(it) > 30 else it)
            for it in items_found
        ]
        content = f"{len(items_found)} Artikel: " + " + ".join(short_items)

    if not content:
        # Clean up subject as fallback content description
        raw_subj = re.sub(
            r"^(?:Bestellt|Versendet|In Zustellung|Geliefert|Zugestellt|Shipped|Delivered|Fulfilled|Fwd|AW|WG):\s*",
            "",
            subject_clean,
            flags=re.IGNORECASE,
        )
        for q in ('"', "„", "“", "”", "'"):
            raw_subj = raw_subj.replace(q, "")
        content = raw_subj.strip() or f"{carrier_name} Sendung"

    if len(content) > 85:
        content = content[:82].rstrip() + "..."

    # 6. Extract Tracking URL (supports plain-text URL keywords like 'dhl.de, orders/' or Regex)
    tracking_url = ""
    default_url = (matched_carrier.get("default_tracking_url") or "").strip()
    url_regex = (matched_carrier.get("tracking_url_regex") or "").strip()
    if url_regex:
        for sub_upat in _iter_pattern_candidates(url_regex):
            # When package is already shipped (not STATUS_ORDERED) and default_tracking_url has {tracking_id},
            # skip shop order-status links ('orders/') so the carrier tracking URL with {tracking_id} is used.
            if (
                status != STATUS_ORDERED
                and tracking_id
                and "{tracking_id}" in default_url
                and sub_upat.lower() in ("orders/", "order")
            ):
                continue
            if "(" not in sub_upat and "[" not in sub_upat and "\\" not in sub_upat:
                for u in extracted_urls:
                    if sub_upat.lower() in u.lower():
                        tracking_url = u
                        break
                if tracking_url:
                    break
            try:
                m = re.search(sub_upat, combined_raw, re.IGNORECASE)
                if m:
                    groups = [g for g in m.groups() if g]
                    cand = groups[0] if groups else m.group(0)
                    if cand.startswith("http"):
                        tracking_url = cand
                        break
            except re.error:
                continue

    # If shipped and default_tracking_url uses {tracking_id}, prefer it over broken logistics.dhl or missing links
    if (
        status != STATUS_ORDERED
        and tracking_id
        and "{tracking_id}" in default_url
        and (not tracking_url or "logistics.dhl" in tracking_url.lower() or "orders/" in tracking_url.lower())
    ):
        tracking_url = default_url.replace("{tracking_id}", tracking_id)
    elif tracking_url and "logistics.dhl" in tracking_url.lower() and tracking_id and tracking_id.startswith("0034"):
        tracking_url = f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tracking_id}"

    if not tracking_url and extracted_urls:
        for u in extracted_urls:
            if "logistics.dhl" in u.lower() and tracking_id and tracking_id.startswith("0034"):
                tracking_url = f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tracking_id}"
                break
            if any(k in u.lower() for k in ("track", "shiptrack", "verfolgen", "parcel", "sendung", "order")):
                tracking_url = u
                break

    if not tracking_url:
        fallback_url = default_url or "https://www.google.com/search?q=sendungsverfolgung"
        tracking_url = fallback_url.replace("{tracking_id}", tracking_id)

    # 7. Construct unique package UID
    if tracking_id:
        uid = f"paket_{slugify_id(carrier_id, 12)}_{slugify_id(tracking_id, 20)}"
    else:
        uid = f"paket_{slugify_id(carrier_id, 12)}_{slugify_id(content, 20)}"

    now_dt = datetime.now()
    return {
        "matched": True,
        "uid": uid,
        "carrier_id": carrier_id,
        "zusteller": carrier_name,
        "icon": matched_carrier.get("icon", "mdi:package-variant"),
        "tracking_id": tracking_id,
        "all_ids": all_ids,
        "inhalt": content,
        "artikel_liste": items_found if items_found else [content],
        "status": status,
        "zustellung": timing,
        "tracking_url": tracking_url,
        "matched_reason": f"{matched_reason} | Status-Treffer: '{status_keyword}'",
        "aktualisiert_am": now_dt.strftime("%d.%m.%Y %H:%M"),
        "zugestellt_am": now_dt.strftime("%Y-%m-%d") if status == STATUS_DELIVERED else None,
        "sender": sender_clean,
        "subject": subject_clean,
    }
