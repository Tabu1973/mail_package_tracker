"""Constants and default carrier presets for Mail Package Tracker."""
from __future__ import annotations

from typing import Any

DOMAIN = "mail_package_tracker"
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_storage"

CONF_MODE = "mode"
MODE_BOTH = "both"
MODE_IMAP = "imap_only"
MODE_EVENT = "event_only"

CONF_IMAP_HOST = "imap_host"
CONF_IMAP_PORT = "imap_port"
CONF_IMAP_USER = "imap_user"
CONF_IMAP_PASSWORD = "imap_password"
CONF_IMAP_FOLDER = "imap_folder"
CONF_DAYS_BACK = "days_back"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CLEANUP_DAYS = "cleanup_days"

DEFAULT_IMAP_HOST = "imap.gmail.com"
DEFAULT_IMAP_PORT = 993
DEFAULT_IMAP_FOLDER = "INBOX"
DEFAULT_DAYS_BACK = 2
DEFAULT_SCAN_INTERVAL = 5  # minutes
DEFAULT_CLEANUP_DAYS = 7

STATUS_ORDERED = "Bestellt"
STATUS_IN_TRANSIT = "Unterwegs"
STATUS_OUT_FOR_DELIVERY = "In Zustellung"
STATUS_DELIVERED = "Zugestellt"

STATUS_RANK: dict[str, int] = {
    STATUS_ORDERED: 1,
    STATUS_IN_TRANSIT: 2,
    STATUS_OUT_FOR_DELIVERY: 3,
    STATUS_DELIVERED: 4,
}

TIMING_ORDERED = "Warte auf Versand"
TIMING_SOON = "In Kürze erwartet"
TIMING_TODAY = "Ankunft heute"
TIMING_TOMORROW = "Ankunft morgen"
TIMING_DELIVERED_TODAY = "Heute zugestellt"

# Default pre-configured carrier & shop rules (German presets)
DEFAULT_CARRIERS: dict[str, dict[str, Any]] = {
    "amazon": {
        "schema_version": 1,
        "id": "amazon",
        "name": "Amazon",
        "icon": "mdi:cart",
        "language": "de",
        "enabled": True,
        "is_preset": True,
        "sender_patterns": ["amazon.de", "amazon.com", "amazon.eu"],
        "subject_patterns": [],
        "exclude_patterns": [
            "customer-reviews",
            "amazonmusic",
            "audible",
            "kindle",
            "prime video",
            "storniert",
            "gutschrift",
            "rücksendung",
            "ersatzlieferung",
        ],
        "ordered_patterns": [
            "bestellt:",
            "bestellbestätigung",
            "vielen dank für deine bestellung",
            "vielen dank für ihre bestellung",
        ],
        "in_transit_patterns": [
            "versendet:",
            "dein paket wurde versendet",
            "wurde versandt",
            "wurde versendet",
            "unterwegs",
        ],
        "out_for_delivery_patterns": [
            "in zustellung:",
            "ankunft heute",
            "kommt heute",
            "wird heute zugestellt",
            "wird heute geliefert",
            "zustellung heute",
            "heute bis",
        ],
        "delivered_patterns": [
            "geliefert:",
            "zugestellt:",
            "wurde geliefert",
            "wurde zugestellt",
            "erfolgreich zugestellt",
            "wurde an ",
            "wurde übergeben",
            "liegt am ablageort",
        ],
        "tomorrow_patterns": [
            "ankunft morgen",
            "lieferung morgen",
            "lieferung: morgen",
            "zustellung morgen",
            "wird morgen",
            "kommt morgen",
        ],
        "tracking_regex": "Bestellnr., shipmentId=",
        "tracking_url_regex": r"(https://[^\s\"'<]+amazon\.[a-z.]+/(?:progress-tracker|gp/your-account|gp/css/shiptrack)[^\s\"'<]*)",
        "default_tracking_url": "https://www.amazon.de/gp/your-account/order-history",
        "content_regex": "*",
    },
    "dhl": {
        "schema_version": 1,
        "id": "dhl",
        "name": "DHL",
        "icon": "mdi:truck-delivery",
        "language": "de",
        "enabled": True,
        "is_preset": True,
        "sender_patterns": ["dhl.de", "dhl.com", "deutschepost.de", "paket.de", "dpdhl.com"],
        "subject_patterns": ["dhl paket", "dhl sendung"],
        "exclude_patterns": [
            "newsletter",
            "werbung",
            "kundenbefragung",
        ],
        "ordered_patterns": [],
        "in_transit_patterns": [
            "paketankündigung",
            "ist unterwegs",
            "auf dem weg",
            "wurde versandt",
            "in kürze",
            "kommt am",
        ],
        "out_for_delivery_patterns": [
            "in zustellung",
            "kommt heute",
            "wird heute zugestellt",
            "zustellung heute",
            "heute zwischen",
            "zur auslieferung",
        ],
        "delivered_patterns": [
            "wurde zugestellt",
            "erfolgreich zugestellt",
            "haben wir zugestellt",
            "liegt in der packstation",
            "abholbereit",
            "wurde geliefert",
            "am wunschort",
            "am ablageort",
        ],
        "tomorrow_patterns": [
            "kommt morgen",
            "voraussichtlich morgen",
            "zustellung morgen",
            "lieferung morgen",
        ],
        "tracking_regex": r"(0034[0-9]{16}|[0-9]{12,20}|JJD[0-9]{10,20})",
        "tracking_url_regex": r"(https://[^\s\"'<]+dhl\.[a-z.]+/[^\s\"'<]*)",
        "default_tracking_url": "https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tracking_id}",
        "content_regex": r"(?:Sendung von|Paket von)\s+([A-Za-z0-9ÄÖÜäöüß &._-]{2,35}?)(?:\s+(?:mit|ist|wird|kommt|wurde|an|in|[0-9]{8})|[,.!\n\r\"<>]|$)",
    },
    "dpd": {
        "schema_version": 1,
        "id": "dpd",
        "name": "DPD",
        "icon": "mdi:cube-send",
        "language": "de",
        "enabled": True,
        "is_preset": True,
        "sender_patterns": ["dpd.de", "dpd.com", "dpdgroup.com"],
        "subject_patterns": ["dpd paket", "ihr dpd"],
        "exclude_patterns": ["newsletter", "bewertung"],
        "ordered_patterns": [],
        "in_transit_patterns": [
            "baldige zustellung",
            "ist unterwegs",
            "auf dem weg",
            "paketankündigung",
        ],
        "out_for_delivery_patterns": [
            "heute zugestellt",
            "kommt heute",
            "in zustellung",
            "zustellung heute",
        ],
        "delivered_patterns": [
            "wurde zugestellt",
            "erfolgreich zugestellt",
            "abgestellt",
            "im pickup paketshop",
            "abholbereit",
        ],
        "tomorrow_patterns": ["kommt morgen", "zustellung morgen", "morgen zwischen"],
        "tracking_regex": r"([0-9]{14})",
        "tracking_url_regex": r"(https://[^\s\"'<]+dpd\.[a-z.]+/[^\s\"'<]*)",
        "default_tracking_url": "https://tracking.dpd.de/status/de_DE/parcel/{tracking_id}",
        "content_regex": r"(?:Sendung von|Paket von)\s+([A-Za-z0-9ÄÖÜäöüß &._-]{2,35}?)(?:\s+(?:mit|ist|wird|kommt|wurde|an|in|[0-9]{8})|[,.!\n\r\"<>]|$)",
    },
    "hermes": {
        "schema_version": 1,
        "id": "hermes",
        "name": "Hermes",
        "icon": "mdi:package-variant-closed",
        "language": "de",
        "enabled": True,
        "is_preset": True,
        "sender_patterns": ["myhermes.de", "hermesworld.com", "hermes-world.com", "hermes.de"],
        "subject_patterns": ["hermes sendung", "hermes paket"],
        "exclude_patterns": ["newsletter"],
        "ordered_patterns": [],
        "in_transit_patterns": [
            "ist unterwegs",
            "auf dem weg",
            "angekündigt",
            "sendungsstatus",
        ],
        "out_for_delivery_patterns": [
            "in zustellung",
            "kommt heute",
            "heute zugestellt",
            "zustellung heute",
        ],
        "delivered_patterns": [
            "wurde zugestellt",
            "erfolgreich zugestellt",
            "im paketshop",
            "abholbereit",
        ],
        "tomorrow_patterns": ["kommt morgen", "voraussichtlich morgen"],
        "tracking_regex": r"(H[0-9]{19}|[0-9]{14})",
        "tracking_url_regex": r"(https://[^\s\"'<]+myhermes\.de/[^\s\"'<]*)",
        "default_tracking_url": "https://www.myhermes.de/empfangen/sendungsverfolgung/suchen/sendungsinformation/{tracking_id}",
        "content_regex": r"(?:Sendung von|von)\s+([^\n\r\"<>]+)",
    },
    "gls": {
        "schema_version": 1,
        "id": "gls",
        "name": "GLS",
        "icon": "mdi:truck",
        "language": "de",
        "enabled": True,
        "is_preset": True,
        "sender_patterns": ["gls-group.com", "gls-germany.com", "gls-pakete.de", "gls-group.eu"],
        "subject_patterns": ["gls paket", "gls sendung"],
        "exclude_patterns": ["newsletter"],
        "ordered_patterns": [],
        "in_transit_patterns": ["ist unterwegs", "auf dem weg", "paketankündigung"],
        "out_for_delivery_patterns": ["in zustellung", "kommt heute", "heute zwischen"],
        "delivered_patterns": ["wurde zugestellt", "im gls paketshop", "zugestellt"],
        "tomorrow_patterns": ["kommt morgen", "voraussichtlich morgen"],
        "tracking_regex": r"([0-9]{11,12}|[A-Z0-9]{8})",
        "tracking_url_regex": r"(https://[^\s\"'<]+gls-[a-z.]+\.[a-z]+/[^\s\"'<]*)",
        "default_tracking_url": "https://www.gls-pakete.de/sendungsverfolgung?match={tracking_id}",
        "content_regex": "",
    },
    "ups": {
        "schema_version": 1,
        "id": "ups",
        "name": "UPS",
        "icon": "mdi:truck-fast",
        "language": "de",
        "enabled": True,
        "is_preset": True,
        "sender_patterns": ["ups.com"],
        "subject_patterns": ["ups sendung", "ups zustellung", "ups update"],
        "exclude_patterns": ["newsletter", "rechnung"],
        "ordered_patterns": [],
        "in_transit_patterns": ["unterwegs", "geplante zustellung"],
        "out_for_delivery_patterns": ["in zustellung", "heute"],
        "delivered_patterns": ["wurde zugestellt", "zugestellt"],
        "tomorrow_patterns": ["morgen"],
        "tracking_regex": r"(1Z[A-Z0-9]{16})",
        "tracking_url_regex": r"(https://[^\s\"'<]+ups\.com/[^\s\"'<]*)",
        "default_tracking_url": "https://www.ups.com/track?loc=de_DE&tracknum={tracking_id}",
        "content_regex": "",
    },
    "aliexpress": {
        "schema_version": 1,
        "id": "aliexpress",
        "name": "AliExpress",
        "icon": "mdi:shopping",
        "language": "de",
        "enabled": True,
        "is_preset": True,
        "sender_patterns": ["aliexpress.com"],
        "subject_patterns": ["aliexpress", "goodcang", "parel"],
        "exclude_patterns": [
            "promotion",
            "sale",
            "rabatt",
        ],
        "ordered_patterns": [
            "zahlung bestätigt",
            "bestellung bestätigt",
        ],
        "in_transit_patterns": [
            "wurde versandt",
            "unterwegs",
            "im zielland angekommen",
        ],
        "out_for_delivery_patterns": [
            "in zustellung",
            "zur auslieferung bereit",
        ],
        "delivered_patterns": [
            "wurde zugestellt",
            "wurde geliefert",
            "erfolgreich zugestellt",
        ],
        "tomorrow_patterns": ["morgen"],
        "tracking_regex": r"(0034[0-9]{16}|[A-Z]{2}[0-9]{9}[A-Z]{2}|[0-9]{12,16})",
        "tracking_url_regex": r"(https://[^\s\"'<]+(?:aliexpress\.com|cainiao\.com|dhl\.de)[^\s\"'<]*)",
        "default_tracking_url": "https://www.aliexpress.com/p/order/index.html",
        "content_regex": r"Bestellung\s+([0-9]+)",
    },
    "sunlu": {
        "schema_version": 1,
        "id": "sunlu",
        "name": "Sunlu",
        "icon": "mdi:printer-3d-nozzle",
        "language": "de",
        "enabled": True,
        "is_preset": True,
        "sender_patterns": ["sunlu.com", "sunlu.de"],
        "subject_patterns": ["sunlu"],
        "exclude_patterns": [
            "newsletter",
            "discount",
            "sale",
            "welcome to sunlu",
            "cart is ready",
            "dein code lautet",
            "is your code",
            "punkte verdient",
        ],
        "ordered_patterns": [
            "bestätigt",
            "vielen dank für deinen einkauf",
            "thank you for your purchase",
            "order confirmed",
            "bestellbestätigung",
        ],
        "in_transit_patterns": [
            "on the way",
            "has been shipped",
            "shipped",
            "fulfilled",
            "shipment from order",
            "auf dem weg",
            "wurde versandt",
            "wurde verschickt",
            "unterwegs",
            "tracking",
        ],
        "out_for_delivery_patterns": [
            "out for delivery",
            "in zustellung",
            "arriving today",
            "kommt heute",
        ],
        "delivered_patterns": [
            "has been delivered",
            "delivered",
            "wurde zugestellt",
            "wurde geliefert",
        ],
        "tomorrow_patterns": ["tomorrow", "morgen"],
        "tracking_regex": "DHL Trackingnummer:, Trackingnummer:, Bestellung",
        "tracking_url_regex": "dhl.de, tracking.dpd.de, myhermes.de, orders/",
        "default_tracking_url": "https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tracking_id}",
        "content_regex": "Artikel in dieser Lieferung, Bestellübersicht",
    },
}
