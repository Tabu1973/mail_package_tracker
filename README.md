# 📦 Mail Package Tracker for Home Assistant

<p align="center">
  <img src="custom_components/mail_package_tracker/brand/icon@2x.png" alt="Mail Package Tracker Logo" width="140" />
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/Tabu1973/mail_package_tracker/releases"><img src="https://img.shields.io/badge/version-1.1.0-blue.svg" alt="Version 1.1.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

**Mail Package Tracker** ist eine universelle, ressourcenschonende Home Assistant Custom Integration (HACS-kompatibel), die dein E-Mail-Postfach lokal per IMAP nach Bestell-, Versand- und Zustellbenachrichtigungen durchsucht, für jeden Paketdienst oder Online-Shop ein eigenes **Gerät** anlegt, ein eigenes **Seitenleisten-Panel (`📦 Paket-Tracker`)** mitbringt und dynamische Paket-Sensoren für dein Dashboard bereitstellt.

---

## ✨ Highlights & Features

- **🖥️ Eigenes Seitenleisten-Panel (`📦 Paket-Tracker`) mit Schalter:**
  - Über den Schalter **`In Seitenleiste einblenden`** (`switch.mail_package_tracker_ubersicht_in_seitenleiste_einblenden`) lässt sich das Konfigurations-Panel jederzeit live in der Home Assistant Seitenleiste ein- oder ausblenden.
  - Im Panel kannst du alle **Lieferanten & Filterregeln** bequem bearbeiten, neue Shops anlegen, im **🧪 Live E-Mail-Tester** echte E-Mails aus deinem Postfach mit einem Klick gegen die Regeln testen und erkannte Pakete verwalten.
- **🔄 Kompletter 4-Stufen-Lebenszyklus eines Pakets:**
  1. 🛒 **`Bestellt` (`Warte auf Versand`)** – direkt ab Bestellbestätigung sichtbar
  2. 🚚 **`Unterwegs` (`In Kürze erwartet` / `Ankunft morgen`)** – sobald die Versandmail eintrifft
  3. ⚡ **`In Zustellung` (`Ankunft heute`)** – am Tag der Lieferung
  4. ✅ **`Zugestellt` (`Heute zugestellt` $\rightarrow$ `Gestern zugestellt` $\rightarrow$ `Geliefert am DD.MM.`)**
- **🔗 Intelligente Deduplizierung über Bestell- & Sendungsnummern (`all_ids`):**
  - Verknüpft automatisch die Bestellnummer aus der Bestellbestätigung (z. B. `#SL145110DE26` oder Amazon `303-...`) mit der späteren Trackingnummer aus der Versandmail (z. B. `0034...`), sodass kein Paket doppelt angezeigt wird.
- **📋 Mehrere Artikel pro Paket & einfache Klartext-Filter (ohne Regex-Zwang):**
  - Extrahiert auf Wunsch alle Artikel einer Sendung (z. B. `3 Artikel: 1 PETG + 1 PLA+ ...` + vollständige Liste im Attribut `artikel_liste`).
  - Statt komplizierter regulärer Ausdrücke reichen einfache Suchbegriffe oder der Text vor der Nummer (z. B. `DHL Trackingnummer:, Bestellung` oder `*` für Aufzählungen). Fortgeschrittene können weiterhin optional Regex nutzen.
- **🚚 Vorbelegte Regeln (Out-of-the-Box):**
  - Direkt nach der Installation sind **Amazon, DHL, DPD, Hermes, GLS, UPS, AliExpress und Sunlu** fertig vorkonfiguriert.
- **📬 Ressourcenschonender & sicherer IMAP-Abruf:**
  - Erkennt **sowohl gelesene als auch ungelesene** E-Mails der letzten `N` Tage (Standard: **3 Tage**, einstellbar `1–14` Tage).
  - Nutzt `readonly=True` und `BODY.PEEK[]<0.300000>`: Ungelesene E-Mails bleiben im Postfach **unangetastet ungelesen**, und große E-Mail-Anhänge (PDFs, Bilder, ZIPs) werden **weder heruntergeladen noch in Home Assistant gespeichert**.
  - Zugestellte Pakete werden nach `N` Tagen (Standard: **7 Tage**, einstellbar `1–30` Tage) automatisch aufgeräumt.

---

## 🚀 Installation

### Option 1: Über HACS (Empfohlen)
1. Öffne **HACS** in Home Assistant.
2. Klicke oben rechts auf das **Drei-Punkte-Menü** $\rightarrow$ **Benutzerdefinierte Repositories**.
3. Füge die URL `https://github.com/Tabu1973/mail_package_tracker` hinzu und wähle als Kategorie **Integration**.
4. Suche nach **Mail Package Tracker** und klicke auf **Herunterladen**.
5. Starte Home Assistant neu.

### Option 2: Manuelle Installation
1. Kopiere den Ordner `custom_components/mail_package_tracker` in dein Home Assistant Verzeichnis unter `/config/custom_components/mail_package_tracker`.
2. Starte Home Assistant neu.

---

## ⚙️ Einrichtung

1. Gehe in Home Assistant auf **Einstellungen $\rightarrow$ Geräte & Dienste $\rightarrow$ Integration hinzufügen**.
2. Suche nach **Mail Package Tracker**.
3. Gib deine IMAP-Zugangsdaten ein (z. B. bei **Gmail**: `imap.gmail.com`, Port `993` und ein 16-stelliges Google **App-Passwort**).
4. Öffne danach links in der Seitenleiste **📦 Paket-Tracker**, um Filterregeln anzupassen, eigene Shops hinzuzufügen oder E-Mails live zu testen.

---

## 📊 Attribute jedes Paket-Sensors (`sensor.paket_<carrier>_<id>`)

| Attribut | Beispiel | Beschreibung |
| :--- | :--- | :--- |
| `unique_id` | `paket_sunlu_sl145110de26` | Eindeutige Paket-ID |
| `zusteller` | `Sunlu` / `Amazon` / `DHL` | Anzeigename des Händlers / Paketdienstes |
| `inhalt` | `3 Artikel: 1 PETG + 1 PLA+...` | Erkannter Inhalt / Artikel-Zusammenfassung |
| `artikel_liste` | `["1 PETG", "1 PLA+"]` | Liste aller erkannten Einzelartikel im Paket |
| `status` | `Bestellt` / `Unterwegs` / `In Zustellung` / `Zugestellt` | Aktuelle Versandstufe |
| `zustellung` | `Warte auf Versand` / `In Kürze erwartet` / `Ankunft morgen` / `Ankunft heute` / `Heute zugestellt` | Zeitliche Einordnung (auch Sensor-State) |
| `tracking_id` | `00340435072882616692` | Extrahierte Sendungs- oder Bestellnummer |
| `all_ids` | `["00340435072882616692", "SL145110DE26"]` | Alle verknüpften Bestell-/Sendungsnummern |
| `tracking_url` | `https://www.dhl.de/...` | Direkter Link zur Sendungsverfolgung |
| `aktualisiert_am` | `21.10.2026 15:01` | Zeitpunkt des letzten Updates |
| `zugestellt_am` | `2026-10-21` | ISO-Datum der Zustellung (für Auto-Cleanup) |

---

## 🎨 Beispiel-Dashboard (Mushroom + `auto-entities`)

Wenn du HACS-Karten wie `Mushroom` und `auto-entities` nutzt, kannst du mit folgendem YAML-Code sofort eine vollautomatische Paket-Übersicht anlegen:

```yaml
type: custom:auto-entities
card:
  type: grid
  columns: 1
  square: false
card_param: cards
filter:
  template: |
    {% set ns = namespace(cards=[]) %}
    {% set all_p = states.sensor | selectattr('attributes.zusteller', 'defined') | rejectattr('state', 'in', ['unavailable', 'unknown']) | list %}
    {% set transit = all_p | selectattr('attributes.status', 'in', ['Unterwegs', 'In Zustellung']) | list %}
    {% set ordered = all_p | selectattr('attributes.status', 'eq', 'Bestellt') | list %}
    {% set delivered = all_p | selectattr('attributes.status', 'eq', 'Zugestellt') | sort(attribute='attributes.zugestellt_am', reverse=true) | list %}
    {% set today_str = now().date().strftime('%Y-%m-%d') %}
    {% set delivered_today = delivered | selectattr('attributes.zugestellt_am', 'eq', today_str) | list %}
    {% set delivered_earlier = delivered | rejectattr('attributes.zugestellt_am', 'eq', today_str) | list %}

    {% if transit | length > 0 %}
      {% set ns.cards = ns.cards + [{'type': 'custom:mushroom-title-card', 'title': '🚚 Unterwegs & In Zustellung'}] %}
      {% for s in transit %}
        {% set ns.cards = ns.cards + [{
          'type': 'custom:mushroom-template-card',
          'entity': s.entity_id,
          'icon': s.attributes.icon | default('mdi:package-variant-closed'),
          'icon_color': 'blue',
          'primary': s.attributes.zusteller ~ ' • ' ~ s.state,
          'secondary': '📦 ' ~ (s.attributes.inhalt | default('Sendung')),
          'tap_action': {'action': 'url', 'url_path': s.attributes.tracking_url | default('https://www.dhl.de')}
        }] %}
      {% endfor %}
    {% endif %}

    {% if ordered | length > 0 %}
      {% set ns.cards = ns.cards + [{'type': 'custom:mushroom-title-card', 'title': '🛒 Bestellt – Warte auf Versand'}] %}
      {% for s in ordered %}
        {% set ns.cards = ns.cards + [{
          'type': 'custom:mushroom-template-card',
          'entity': s.entity_id,
          'icon': s.attributes.icon | default('mdi:cart-outline'),
          'icon_color': 'purple',
          'primary': s.attributes.zusteller ~ ' • ' ~ s.state,
          'secondary': '🛒 ' ~ (s.attributes.inhalt | default('Bestellung')),
          'tap_action': {'action': 'url', 'url_path': s.attributes.tracking_url | default('#')}
        }] %}
      {% endfor %}
    {% endif %}

    {% if delivered_today | length > 0 %}
      {% set ns.cards = ns.cards + [{'type': 'custom:mushroom-title-card', 'title': '✅ Heute geliefert'}] %}
      {% for s in delivered_today %}
        {% set ns.cards = ns.cards + [{
          'type': 'custom:mushroom-template-card',
          'entity': s.entity_id,
          'icon': s.attributes.icon | default('mdi:package-variant-closed'),
          'icon_color': 'green',
          'primary': s.attributes.zusteller ~ ' • Heute zugestellt',
          'secondary': '📦 ' ~ (s.attributes.inhalt | default('Sendung')),
          'tap_action': {'action': 'url', 'url_path': s.attributes.tracking_url | default('#')}
        }] %}
      {% endfor %}
    {% endif %}

    {{ ns.cards | to_json }}
```

---

## 🤝 Community & Weitere Shops hinzufügen

Da jeder Online-Shop und Paketdienst seine E-Mails etwas anders aufbaut, lebt dieses Projekt vom Mitmachen!
- Du hast eine funktionierende Filterregel für einen weiteren Shop (z. B. *Otto, Zalando, eBay, Mindfactory, Bambulab, Prusa, FedEx, Post AT / CH*) erstellt?
- Öffne gerne ein **Issue** oder einen **Pull Request** mit deinen Filter-Schlagwörtern (oder einer anonymisierten Beispiel-Mail), damit wir die Standard-Presets in [`const.py`](custom_components/mail_package_tracker/const.py) für alle erweitern können!

---

## 📄 Lizenz

MIT License – frei verwendbar und anpassbar für die Home Assistant Community.
