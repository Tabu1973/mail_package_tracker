"""DHL public parcel tracking API client for live delivery status."""
from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def fetch_dhl_tracking_sync(piececode: str) -> dict[str, Any] | None:
    """Fetch structured live tracking data from DHL's public web tracking endpoint."""
    clean_code = str(piececode or "").strip()
    if not clean_code:
        return None

    url = f"https://www.dhl.de/int-verfolgen/data/search?piececode={clean_code}&language=de"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={clean_code}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("rateLimited"):
                _LOGGER.debug("DHL tracking rate limited for %s", clean_code)
                return None
            sendungen = data.get("sendungen", [])
            if not sendungen:
                return None
            shipment = sendungen[0]
            if shipment.get("sendungNichtGefunden", {}).get("keineDatenVerfuegbar"):
                return None
            details = shipment.get("sendungsdetails", {})
            verlauf = details.get("sendungsverlauf", {})
            zustellung = details.get("zustellung", {})
            is_delivered = bool(details.get("istZugestellt"))
            status_text = verlauf.get("status") or ""
            fortschritt = verlauf.get("fortschritt", 0)
            max_fortschritt = verlauf.get("maximalFortschritt", 5)
            date_status = verlauf.get("datumAktuellerStatus") or ""
            expected_date = (
                zustellung.get("zustellzeitfensterVon")
                or zustellung.get("zustellzeitfensterBis")
                or None
            )
            events = verlauf.get("events", [])
            last_event = events[-1].get("status") if events else None

            return {
                "is_delivered": is_delivered,
                "status_text": status_text,
                "progress": f"{fortschritt}/{max_fortschritt}",
                "progress_step": fortschritt,
                "current_status_date": date_status,
                "expected_date": expected_date,
                "last_event": last_event,
            }
    except Exception as err:
        _LOGGER.debug("DHL live tracking query failed for %s: %s", clean_code, err)
        return None


async def async_fetch_dhl_tracking(hass: HomeAssistant, piececode: str) -> dict[str, Any] | None:
    """Async wrapper to query DHL tracking in executor."""
    return await hass.async_add_executor_job(fetch_dhl_tracking_sync, piececode)
