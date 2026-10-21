const I18N = {
  de: {
    subtitle: (c, p) => `${c} Lieferanten • ${p} gespeicherte Pakete`,
    tab_carriers: "⚙️ Lieferanten & Filterregeln",
    tab_tester: "🧪 Live E-Mail-Tester",
    tab_packages: (p) => `📦 Pakete (${p})`,
    btn_scan_now: "🔄 Jetzt E-Mails prüfen",
    carriers_title: "Lieferanten / Shops",
    btn_new: "➕ Neu",
    new_carrier_title: "➕ Neuen Lieferanten anlegen",
    edit_carrier_title: (n) => `✏️ Filterregel: ${n}`,
    btn_delete: "🗑️ Löschen",
    btn_save: "💾 Speichern & E-Mails neu prüfen",
    lbl_name: "Name des Lieferanten / Shops",
    ph_name: "z.B. Sunlu, Amazon, DHL...",
    lbl_id_icon: "Interne Kennung (ID) & Icon",
    lbl_enabled: "Regel ist aktiv",
    lbl_sender: "📧 Absender enthält (kommagetrennt)",
    hint_sender: "Mindestens einer dieser Begriffe muss in der Absender-Adresse stehen.",
    lbl_subject: "📌 Betreff muss enthalten (optional, kommagetrennt)",
    ph_subject: "Leer lassen = alle Betreffs erlauben",
    hint_subject: "Optionaler Vorfilter auf die Betreffzeile.",
    lbl_ordered: "🛒 Wörter für „Bestellt (Warte auf Versand)“",
    hint_ordered: "Erzeugt ein Paket unter „Warte auf Versand“, bis die Versandmail eintrifft.",
    lbl_transit: "🚚 Wörter für „Unterwegs (Versendet)“",
    hint_transit: "Stuft das Paket auf „Unterwegs“ hoch.",
    lbl_ofd: "⚡ Wörter für „In Zustellung (Kommt heute)“",
    lbl_delivered: "✅ Wörter für „Zugestellt (Geliefert)“",
    lbl_tomorrow: "📅 Wörter für „Ankunft morgen“",
    lbl_exclude: "🚫 Ausschluss-Wörter (Werbung / Storno ignorieren)",
    lbl_tregex: "🔢 Tracking- / Bestellnummer (Text davor oder Regex, kommagetrennt)",
    hint_tregex: "Einfach den Text vor der Nummer angeben (z.B. DHL Trackingnummer:, Bestellung). Alle gefundenen Nummern werden verknüpft, damit Bestellbestätigung & Versandmail automatisch zusammengeführt werden!",
    lbl_cregex: "📦 Paket-Inhalt / Artikel-Liste (Überschrift in der Mail, * für Aufzählung oder Regex)",
    hint_cregex: "Liest automatisch auch mehrere Artikel aus einer Lieferung aus (z.B. „3 Artikel: 1 PETG + 1 PLA+...“).",
    lbl_uregex: "🔗 Tracking-Link in der Mail enthält (kommagetrennt)",
    hint_uregex: "Suchbegriffe für den Tracking-Link im E-Mail-HTML.",
    lbl_defurl: "🌐 Standard Tracking-URL (mit {tracking_id} Platzhalter)",
    hint_defurl: "Wird für versendete Pakete genutzt, wenn die Mail keinen direkten Tracking-Link enthält (ersetzt {tracking_id} durch die Sendungsnummer).",
    tester_title: "🧪 Live E-Mail-Tester",
    tester_desc: "Wähle eine der letzten empfangenen E-Mails aus oder füge eigenen Text / HTML ein, um sofort zu sehen, wie deine Filterregeln die E-Mail auswerten.",
    lbl_recent_select: (n) => `📥 Aus letzten empfangenen E-Mails auswählen (${n} gespeichert)`,
    opt_recent_default: "— E-Mail aus dem Postfach auswählen, um Felder auszufüllen —",
    lbl_t_sender: "Absender (Von)",
    lbl_t_subject: "Betreff",
    lbl_t_body: "E-Mail-Inhalt (normaler Text oder HTML)",
    ph_t_body: "Kopiere hier den Text der E-Mail hinein oder wähle oben eine empfangene E-Mail aus...",
    btn_test_run: "🔍 Gegen Filterregeln testen",
    btn_test_apply: "📥 Als Paket übernehmen",
    res_no_match: "❌ Kein Treffer",
    res_reason: "Grund:",
    res_matched: "✅ Erkannt:",
    res_pkg_id: "Paket-ID:",
    res_tid: "Tracking-Nr.:",
    res_all_ids: "Alle erkannten IDs:",
    res_match_reason: "Treffer-Grund:",
    res_items: (n) => `Extrahierte Artikel (${n}):`,
    res_turl: "Tracking-Link:",
    pkgs_empty: "Aktuell sind keine Pakete gespeichert.",
    pkgs_title: (n) => `📦 Gespeicherte Pakete (${n})`,
    open_tracking: "Tracking öffnen ↗",
    btn_remove: "🗑️ Entfernen",
    toast_saved: (n) => `✅ Filterregel für "${n}" gespeichert & E-Mails geprüft!`,
    toast_scanning: "🔄 Suche nach neuen E-Mails...",
    toast_scanned: "✅ E-Mail-Postfach erfolgreich synchronisiert!",
    toast_applied: "✅ E-Mail als Paket übernommen!",
    toast_removed: "🗑️ Paket entfernt.",
    confirm_delete: (n) => `Lieferant "${n}" wirklich löschen?`,
    btn_import_new: "📥 Neu (JSON)",
    btn_import_overwrite: "📥 JSON Import (Überschreiben)",
    btn_export_json: "📤 JSON Export",
    lbl_language: "🌐 Sprache der Filterregel (im JSON)",
    empty_carriers_lang: "Für diese Sprache (🇩🇪 Deutsch) sind noch keine Lieferanten-Regeln angelegt.",
    json_new_title: "📥 Neuen Lieferanten per JSON anlegen",
    json_new_desc: "Wähle eine .json-Datei aus oder füge den JSON-Code unten ein. Syntax, Pflichtfelder und Sprache (de/en) werden sofort live geprüft und direkt in die Formularfelder übernommen.",
    json_overwrite_title: (n) => `📥 JSON für „${n}“ importieren / bearbeiten (Überschreiben)`,
    json_overwrite_desc: (n) => `Lade eine .json-Datei oder bearbeite den JSON-Code direkt, um den bestehenden Lieferanten „${n}“ zu aktualisieren.`,
    btn_upload_file: "📂 .json-Datei laden",
    btn_download_file: "💾 .json herunterladen",
    btn_copy_json: "📋 JSON kopieren",
    btn_validate_json: "🔍 Syntax prüfen",
    btn_apply_new_json: "📥 Neuen Lieferanten jetzt anlegen",
    btn_apply_overwrite_json: (n) => `💾 „${n}“ mit diesem JSON überschreiben`,
    btn_close: "✖ JSON-Ansicht schließen",
    val_ok_title: "✅ JSON-Syntax & Schema sind gültig!",
    val_err_title: "❌ Fehler im JSON:",
    toast_copied: "📋 JSON in die Zwischenablage kopiert!",
    toast_exported: (f) => `📤 ${f} heruntergeladen!`,
    toast_imported: (n) => `✅ Lieferant "${n}" erfolgreich aus JSON gespeichert!`,
  },
  en: {
    subtitle: (c, p) => `${c} Carriers • ${p} Stored Packages`,
    tab_carriers: "⚙️ Carriers & Filter Rules",
    tab_tester: "🧪 Live Email Tester",
    tab_packages: (p) => `📦 Packages (${p})`,
    btn_scan_now: "🔄 Scan Emails Now",
    carriers_title: "Carriers / Shops",
    btn_new: "➕ Add",
    new_carrier_title: "➕ Add New Carrier / Shop",
    edit_carrier_title: (n) => `✏️ Filter Rule: ${n}`,
    btn_delete: "🗑️ Delete",
    btn_save: "💾 Save & Re-scan Emails",
    lbl_name: "Carrier / Shop Name",
    ph_name: "e.g. Sunlu, Amazon, DHL...",
    lbl_id_icon: "Internal ID & Icon",
    lbl_enabled: "Rule is enabled",
    lbl_sender: "📧 Sender contains (comma-separated)",
    hint_sender: "At least one of these terms must appear in the sender email address.",
    lbl_subject: "📌 Subject must contain (optional, comma-separated)",
    ph_subject: "Leave empty = allow all subjects",
    hint_subject: "Optional pre-filter on the email subject line.",
    lbl_ordered: "🛒 Keywords for 'Ordered (Awaiting Shipment)'",
    hint_ordered: "Creates a package under 'Ordered / Awaiting Shipment' until the shipping email arrives.",
    lbl_transit: "🚚 Keywords for 'In Transit (Shipped)'",
    hint_transit: "Upgrades the package stage to 'In Transit'.",
    lbl_ofd: "⚡ Keywords for 'Out for Delivery (Arriving Today)'",
    lbl_delivered: "✅ Keywords for 'Delivered'",
    lbl_tomorrow: "📅 Keywords for 'Arriving Tomorrow'",
    lbl_exclude: "🚫 Exclude Keywords (Ignore Newsletters / Cancellations)",
    lbl_tregex: "🔢 Tracking / Order Number (Text prefix before number or Regex, comma-separated)",
    hint_tregex: "Simply enter the text appearing before the number (e.g. Tracking number:, Order #). All found IDs are linked so order confirmations & shipping emails merge automatically!",
    lbl_cregex: "📦 Package Content / Item List (Section header in email, * for bullet list, or Regex)",
    hint_cregex: "Automatically extracts multiple items from a shipment (e.g. '3 Artikel: 1 PETG + 1 PLA+...').",
    lbl_uregex: "🔗 Tracking Link in email contains (comma-separated)",
    hint_uregex: "Keywords to identify the tracking link inside the email HTML.",
    lbl_defurl: "🌐 Default Tracking URL (with {tracking_id} placeholder)",
    hint_defurl: "Used for shipped packages if no direct carrier link is found in the email (replaces {tracking_id} with the extracted tracking number).",
    tester_title: "🧪 Live Email Tester",
    tester_desc: "Select one of your recently received emails from the dropdown or paste custom text / HTML to immediately see how your filter rules evaluate it.",
    lbl_recent_select: (n) => `📥 Select from recently received emails (${n} stored)`,
    opt_recent_default: "— Select an email from your inbox to populate fields —",
    lbl_t_sender: "Sender (From)",
    lbl_t_subject: "Subject",
    lbl_t_body: "Email Body (Plain Text or HTML)",
    ph_t_body: "Paste the email text or HTML here, or select a received email from the dropdown above...",
    btn_test_run: "🔍 Test Against Filter Rules",
    btn_test_apply: "📥 Import as Package",
    res_no_match: "❌ No Match",
    res_reason: "Reason:",
    res_matched: "✅ Matched:",
    res_pkg_id: "Package ID:",
    res_tid: "Tracking ID:",
    res_all_ids: "All Linked IDs:",
    res_match_reason: "Match Reason:",
    res_items: (n) => `Extracted Items (${n}):`,
    res_turl: "Tracking URL:",
    pkgs_empty: "No packages currently stored.",
    pkgs_title: (n) => `📦 Stored Packages (${n})`,
    open_tracking: "Open Tracking ↗",
    btn_remove: "🗑️ Remove",
    toast_saved: (n) => `✅ Filter rule for "${n}" saved & emails re-scanned!`,
    toast_scanning: "🔄 Scanning inbox for new emails...",
    toast_scanned: "✅ Email inbox synchronized!",
    toast_applied: "✅ Email imported as package!",
    toast_removed: "🗑️ Package removed.",
    confirm_delete: (n) => `Really delete carrier "${n}"?`,
    btn_import_new: "📥 New (JSON)",
    btn_import_overwrite: "📥 JSON Import (Overwrite)",
    btn_export_json: "📤 JSON Export",
    lbl_language: "🌐 Rule Language (in JSON)",
    empty_carriers_lang: "No English (🇬🇧 EN) carrier filter rules configured yet. Create a new rule or import a community .json file below!",
    json_new_title: "📥 Create New Carrier from JSON",
    json_new_desc: "Choose a .json file or paste the JSON code below. Syntax, required fields, and language (de/en) are validated live and populated directly into the form fields.",
    json_overwrite_title: (n) => `📥 Import / Edit JSON for "${n}" (Overwrite)`,
    json_overwrite_desc: (n) => `Load a .json file or edit the JSON directly to overwrite the existing carrier "${n}".`,
    btn_upload_file: "📂 Load .json File",
    btn_download_file: "💾 Download .json",
    btn_copy_json: "📋 Copy JSON",
    btn_validate_json: "🔍 Check Syntax",
    btn_apply_new_json: "📥 Create & Save New Carrier",
    btn_apply_overwrite_json: (n) => `💾 Overwrite "${n}" with this JSON`,
    btn_close: "✖ Close JSON View",
    val_ok_title: "✅ JSON Syntax & Schema Valid!",
    val_err_title: "❌ JSON Validation Failed:",
    toast_copied: "📋 JSON copied to clipboard!",
    toast_exported: (f) => `📤 Downloaded ${f}!`,
    toast_imported: (n) => `✅ Carrier "${n}" successfully saved from JSON!`,
  },
};

class MailPackageTrackerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._narrow = false;
    this._lang = null;
    this._activeTab = "carriers";
    this._carriers = {};
    this._packages = [];
    this._recentEmails = [];
    this._selectedCarrierId = null;
    this._isNewCarrier = false;
    this._jsonModalOpen = false;
    this._jsonModalMode = "import";
    this._jsonModalText = "";
    this._jsonValidation = null;
    this._testResult = null;
    this._statusMsg = "";
    this._loading = false;
    this._loadedOnce = false;
  }

  _t() {
    const lang = this._lang || (this._hass?.language?.toLowerCase().startsWith("de") ? "de" : "en");
    return I18N[lang] || I18N.en;
  }

  _currentLang() {
    return this._lang || (this._hass?.language?.toLowerCase().startsWith("de") ? "de" : "en");
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._loadedOnce && hass) {
      this._loadedOnce = true;
      this._loadData();
    }
  }

  set narrow(narrow) {
    this._narrow = narrow;
    const menuBtn = this.shadowRoot?.querySelector("#menu-btn");
    if (menuBtn) {
      menuBtn.style.display = narrow ? "inline-flex" : "none";
    }
  }

  async _loadData() {
    if (!this._hass) return;
    this._loading = true;
    this._render();
    try {
      const res = await this._hass.callWS({ type: "mail_package_tracker/get_data" });
      this._carriers = res.carriers || {};
      this._packages = res.packages || [];
      this._recentEmails = res.recent_emails || [];
      const keys = Object.keys(this._carriers);
      if (!this._selectedCarrierId || (!this._carriers[this._selectedCarrierId] && !this._isNewCarrier)) {
        this._selectedCarrierId = keys[0] || null;
      }
    } catch (err) {
      this._statusMsg = "Error: " + (err.message || err);
    }
    this._loading = false;
    this._render();
  }

  _showToast(msg) {
    this._statusMsg = msg;
    const toast = this.shadowRoot?.querySelector("#toast");
    if (toast) {
      toast.textContent = msg;
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), 3500);
    }
  }

  _listToStr(val) {
    if (Array.isArray(val)) return val.join(", ");
    return val || "";
  }

  _strToList(str) {
    return (str || "")
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  }

  _escape(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  _readFormRule() {
    const root = this.shadowRoot;
    const name = root.querySelector("#f-name")?.value.trim() || "New Carrier";
    const idInput = root.querySelector("#f-id")?.value.trim() || name.toLowerCase().replace(/[^a-z0-9]+/g, "_");
    const lang = root.querySelector("#f-lang")?.value || this._currentLang();

    return {
      schema_version: 1,
      id: idInput,
      name,
      icon: root.querySelector("#f-icon")?.value.trim() || "mdi:package-variant-closed",
      language: lang === "en" ? "en" : "de",
      enabled: root.querySelector("#f-enabled")?.checked ?? true,
      sender_patterns: this._strToList(root.querySelector("#f-sender")?.value),
      subject_patterns: this._strToList(root.querySelector("#f-subject")?.value),
      ordered_patterns: this._strToList(root.querySelector("#f-ordered")?.value),
      in_transit_patterns: this._strToList(root.querySelector("#f-transit")?.value),
      out_for_delivery_patterns: this._strToList(root.querySelector("#f-ofd")?.value),
      delivered_patterns: this._strToList(root.querySelector("#f-delivered")?.value),
      tomorrow_patterns: this._strToList(root.querySelector("#f-tomorrow")?.value),
      exclude_patterns: this._strToList(root.querySelector("#f-exclude")?.value),
      tracking_regex: root.querySelector("#f-tregex")?.value.trim() || "",
      content_regex: root.querySelector("#f-cregex")?.value.trim() || "",
      tracking_url_regex: root.querySelector("#f-uregex")?.value.trim() || "",
      default_tracking_url: root.querySelector("#f-defurl")?.value.trim() || "",
    };
  }

  async _saveCarrier() {
    const t = this._t();
    const rule = this._readFormRule();
    try {
      const res = await this._hass.callWS({
        type: "mail_package_tracker/save_carrier",
        carrier_id: rule.id,
        rule,
        rescan: true,
      });
      this._carriers = res.carriers || this._carriers;
      this._packages = res.packages || this._packages;
      this._selectedCarrierId = res.carrier_id;
      this._isNewCarrier = false;
      this._render();
      this._showToast(t.toast_saved(rule.name));
    } catch (err) {
      this._showToast("❌ " + (err.message || err));
    }
  }

  _validateCarrierJsonLocal(rawJson, forceCarrierId = null) {
    const isDe = this._currentLang() === "de";
    const errors = [];
    let data = null;

    if (!rawJson || !rawJson.trim()) {
      return {
        valid: false,
        errors: [isDe ? "Bitte JSON-Code einfügen oder eine .json-Datei auswählen." : "Please paste JSON code or choose a .json file."],
        normalized: null,
      };
    }

    try {
      data = JSON.parse(rawJson);
    } catch (err) {
      return {
        valid: false,
        errors: [
          isDe
            ? `JSON-Syntaxfehler: ${err.message}`
            : `JSON Syntax Error: ${err.message}`,
        ],
        normalized: null,
      };
    }

    if (!data || typeof data !== "object" || Array.isArray(data)) {
      return {
        valid: false,
        errors: [isDe ? "Das JSON muss ein Objekt { ... } sein." : "Root JSON element must be an object { ... }."],
        normalized: null,
      };
    }

    const name = String(data.name || "").trim();
    if (!name) {
      errors.push(isDe ? "Pflichtfeld 'name' fehlt oder ist leer." : "Missing required field 'name'.");
    }

    const rawId = forceCarrierId || String(data.id || name).trim();
    const cid = rawId.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 20);
    if (!cid) {
      errors.push(isDe ? "Pflichtfeld 'id' / 'name' ungültig." : "Missing or invalid 'id' / 'name'.");
    }

    // Validate language ("de" or "en")
    let rawLang = data.language !== undefined ? data.language : data.languages;
    let lang = "";
    if (typeof rawLang === "string") {
      lang = rawLang.trim().toLowerCase();
    } else if (Array.isArray(rawLang) && rawLang.length > 0) {
      lang = String(rawLang[0]).trim().toLowerCase();
    }

    if (!lang) {
      errors.push(
        isDe
          ? 'Pflichtfeld \'language\' fehlt (muss "de" oder "en" sein).'
          : 'Missing required field \'language\' (must be "de" or "en").'
      );
    } else if (lang !== "de" && lang !== "en") {
      errors.push(
        isDe
          ? `Ungültige Sprache in 'language': "${lang}" (erlaubt: "de" oder "en").`
          : `Unsupported language code in 'language': "${lang}" (allowed: "de" or "en").`
      );
    }

    const listFields = [
      "sender_patterns",
      "subject_patterns",
      "ordered_patterns",
      "in_transit_patterns",
      "out_for_delivery_patterns",
      "delivered_patterns",
      "tomorrow_patterns",
      "exclude_patterns",
    ];
    const normLists = {};
    for (const lf of listFields) {
      const val = data[lf] === undefined ? [] : data[lf];
      if (!Array.isArray(val) || val.some((x) => typeof x !== "string")) {
        errors.push(
          isDe
            ? `Feld '${lf}' muss eine Liste von Texten sein (z. B. ["wort1", "wort2"]).`
            : `Field '${lf}' must be an array of strings.`
        );
        normLists[lf] = [];
      } else {
        normLists[lf] = val.map((x) => x.trim()).filter(Boolean);
      }
    }

    if (!normLists.sender_patterns || normLists.sender_patterns.length === 0) {
      errors.push(
        isDe
          ? "Feld 'sender_patterns' muss mindestens einen Absender enthalten (z. B. [\"sunlu.com\"])."
          : "Field 'sender_patterns' must contain at least one sender domain/address."
      );
    }

    const statusCount =
      (normLists.ordered_patterns?.length || 0) +
      (normLists.in_transit_patterns?.length || 0) +
      (normLists.out_for_delivery_patterns?.length || 0) +
      (normLists.delivered_patterns?.length || 0);
    if (statusCount === 0) {
      errors.push(
        isDe
          ? "Mindestens eine Status-Wortliste ('ordered_patterns', 'in_transit_patterns', 'out_for_delivery_patterns' oder 'delivered_patterns') muss gefüllt sein."
          : "At least one status pattern list ('ordered_patterns', 'in_transit_patterns', 'out_for_delivery_patterns', 'delivered_patterns') must contain keywords."
      );
    }

    for (const rf of ["tracking_regex", "content_regex", "tracking_url_regex"]) {
      const rval = String(data[rf] || "").trim();
      if (rval && (rval.startsWith("(") || rval.includes("[0-9]") || rval.includes("\\s") || rval.includes("[^"))) {
        try {
          new RegExp(rval);
        } catch (rerr) {
          errors.push(
            isDe
              ? `Ungültiger regulärer Ausdruck in '${rf}': ${rerr.message}`
              : `Invalid regular expression in '${rf}': ${rerr.message}`
          );
        }
      }
    }

    const normalized = {
      schema_version: 1,
      id: cid,
      name,
      icon: String(data.icon || "mdi:package-variant-closed").trim(),
      language: lang === "en" ? "en" : "de",
      enabled: data.enabled !== false,
      ...normLists,
      tracking_regex: String(data.tracking_regex || "").trim(),
      content_regex: String(data.content_regex || "").trim(),
      tracking_url_regex: String(data.tracking_url_regex || "").trim(),
      default_tracking_url: String(data.default_tracking_url || "").trim(),
    };

    return {
      valid: errors.length === 0,
      errors,
      normalized: errors.length === 0 ? normalized : null,
    };
  }

  _populateFormFromRule(r) {
    const root = this.shadowRoot;
    if (!root || !r) return;
    const setVal = (sel, val) => {
      const el = root.querySelector(sel);
      if (el) el.value = val ?? "";
    };
    setVal("#f-name", r.name || "");
    if (this._isNewCarrier) {
      setVal("#f-id", r.id || "");
    }
    setVal("#f-icon", r.icon || "mdi:package-variant-closed");
    const chkEnabled = root.querySelector("#f-enabled");
    if (chkEnabled) chkEnabled.checked = r.enabled !== false;
    setVal("#f-lang", r.language === "en" ? "en" : "de");

    setVal("#f-sender", this._listToStr(r.sender_patterns));
    setVal("#f-subject", this._listToStr(r.subject_patterns));
    setVal("#f-ordered", this._listToStr(r.ordered_patterns));
    setVal("#f-transit", this._listToStr(r.in_transit_patterns));
    setVal("#f-ofd", this._listToStr(r.out_for_delivery_patterns));
    setVal("#f-delivered", this._listToStr(r.delivered_patterns));
    setVal("#f-tomorrow", this._listToStr(r.tomorrow_patterns));
    setVal("#f-exclude", this._listToStr(r.exclude_patterns));
    setVal("#f-tregex", r.tracking_regex || "");
    setVal("#f-cregex", r.content_regex || "");
    setVal("#f-uregex", r.tracking_url_regex || "");
    setVal("#f-defurl", r.default_tracking_url || "");
  }

  _openImportNewCarrierJson() {
    const curLang = this._currentLang();
    const isDe = curLang === "de";
    const sample = isDe
      ? {
          schema_version: 1,
          id: "neuer_shop",
          name: "Neuer Shop",
          icon: "mdi:package-variant-closed",
          language: "de",
          enabled: true,
          sender_patterns: ["beispiel-shop.de"],
          subject_patterns: [],
          ordered_patterns: ["bestellbestätigung", "vielen dank für deine bestellung"],
          in_transit_patterns: ["wurde versandt", "unterwegs"],
          out_for_delivery_patterns: ["in zustellung", "kommt heute"],
          delivered_patterns: ["zugestellt", "geliefert"],
          tomorrow_patterns: ["morgen"],
          exclude_patterns: ["newsletter", "storniert"],
          tracking_regex: "Trackingnummer:, Bestellung",
          content_regex: "Artikel in dieser Lieferung, Bestellübersicht, *",
          tracking_url_regex: "dhl.de, tracking.dpd.de, myhermes.de",
          default_tracking_url: "https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tracking_id}",
        }
      : {
          schema_version: 1,
          id: "new_shop_en",
          name: "New Shop",
          icon: "mdi:package-variant-closed",
          language: "en",
          enabled: true,
          sender_patterns: ["example-shop.com"],
          subject_patterns: [],
          ordered_patterns: ["order confirmed", "thank you for your order"],
          in_transit_patterns: ["has shipped", "on the way", "in transit"],
          out_for_delivery_patterns: ["out for delivery", "arriving today"],
          delivered_patterns: ["has been delivered", "delivered"],
          tomorrow_patterns: ["arriving tomorrow", "tomorrow"],
          exclude_patterns: ["newsletter", "cancelled"],
          tracking_regex: "Tracking number:, Order #",
          content_regex: "Items in this shipment, Order summary, *",
          tracking_url_regex: "ups.com, fedex.com, dhl.com",
          default_tracking_url: "",
        };
    this._isNewCarrier = true;
    this._jsonModalMode = "new";
    this._jsonModalText = JSON.stringify(sample, null, 2);
    this._jsonValidation = this._validateCarrierJsonLocal(this._jsonModalText, null);
    this._jsonModalOpen = true;
    this._render();
  }

  _openOverwriteCarrierJson() {
    const rule = this._readFormRule();
    this._isNewCarrier = false;
    this._jsonModalMode = "overwrite";
    this._jsonModalText = JSON.stringify(rule, null, 2);
    this._jsonValidation = this._validateCarrierJsonLocal(this._jsonModalText, this._selectedCarrierId);
    this._jsonModalOpen = true;
    this._render();
  }

  _exportCarrierDirect() {
    const t = this._t();
    const rule = this._readFormRule();
    const raw = JSON.stringify(rule, null, 2) + "\n";
    const filename = `${rule.id || "carrier"}.json`;
    const blob = new Blob([raw], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    this._showToast(t.toast_exported(filename));
  }

  async _validateOrImportJson(apply = false) {
    const t = this._t();
    const ta = this.shadowRoot?.querySelector("#json-modal-textarea");
    if (ta) {
      this._jsonModalText = ta.value;
    }
    const forceId = this._jsonModalMode === "overwrite" && !this._isNewCarrier ? this._selectedCarrierId : null;
    const res = this._validateCarrierJsonLocal(this._jsonModalText, forceId);
    this._jsonValidation = res;
    this._renderJsonValidationOnly();

    if (res.valid && res.normalized) {
      // Immediately sync into form fields so user sees the imported values live
      this._populateFormFromRule(res.normalized);
    }

    if (!apply || !res.valid || !res.normalized) {
      return;
    }

    const norm = res.normalized;
    try {
      const wsRes = await this._hass.callWS({
        type: "mail_package_tracker/save_carrier",
        carrier_id: norm.id,
        rule: norm,
        rescan: true,
      });
      this._carriers = wsRes.carriers || this._carriers;
      this._packages = wsRes.packages || this._packages;
      this._selectedCarrierId = wsRes.carrier_id;
      this._isNewCarrier = false;
      this._jsonModalOpen = false;
      this._render();
      this._showToast(t.toast_imported(norm.name));
    } catch (err) {
      this._showToast("❌ " + (err.message || err));
    }
  }

  _downloadCurrentJson() {
    const ta = this.shadowRoot?.querySelector("#json-modal-textarea");
    const raw = ta ? ta.value : this._jsonModalText;
    let cid = this._selectedCarrierId || "carrier";
    try {
      const parsed = JSON.parse(raw);
      if (parsed.id) cid = parsed.id;
    } catch (_) {}
    const blob = new Blob([raw], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${cid}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async _copyCurrentJson() {
    const t = this._t();
    const ta = this.shadowRoot?.querySelector("#json-modal-textarea");
    const raw = ta ? ta.value : this._jsonModalText;
    try {
      await navigator.clipboard.writeText(raw);
      this._showToast(t.toast_copied);
    } catch (_) {
      if (ta) {
        ta.select();
        document.execCommand("copy");
        this._showToast(t.toast_copied);
      }
    }
  }

  _renderJsonValidationOnly() {
    const t = this._t();
    const box = this.shadowRoot?.querySelector("#json-val-box");
    if (!box || !this._jsonValidation) return;
    const v = this._jsonValidation;
    if (!v.valid) {
      const errs = (v.errors || []).map((e) => `<li>${this._escape(e)}</li>`).join("");
      box.innerHTML = `
        <div class="res-card res-fail" style="margin-top:10px;">
          <strong style="font-size:13px;">${t.val_err_title}</strong>
          <ul style="margin:6px 0 0 18px;font-size:12px;">${errs}</ul>
        </div>
      `;
      return;
    }
    const n = v.normalized || {};
    const langLabel = n.language === "en" ? "🇬🇧 EN" : "🇩🇪 DE";
    box.innerHTML = `
      <div class="res-card res-ok" style="margin-top:10px;">
        <strong style="font-size:13px;">${t.val_ok_title}</strong>
        <div style="font-size:12px;margin-top:6px;">
          ID: <code>${this._escape(n.id)}</code> •
          Name: <strong>${this._escape(n.name)}</strong> •
          Language: <strong>${langLabel}</strong> •
          Senders: <code>${this._escape((n.sender_patterns || []).join(", "))}</code>
        </div>
      </div>
    `;
  }

  async _toggleCarrierQuick(cid, enabled) {
    const rule = { ...(this._carriers[cid] || {}), enabled };
    try {
      const res = await this._hass.callWS({
        type: "mail_package_tracker/save_carrier",
        carrier_id: cid,
        rule,
        rescan: false,
      });
      this._carriers = res.carriers || this._carriers;
      this._render();
      this._showToast(`${enabled ? "🟢" : "⚪"} ${rule.name || cid}`);
    } catch (err) {
      this._showToast("❌ " + (err.message || err));
    }
  }

  async _deleteCarrier(cid) {
    const t = this._t();
    const cname = this._carriers[cid]?.name || cid;
    if (!confirm(t.confirm_delete(cname))) return;
    try {
      const res = await this._hass.callWS({
        type: "mail_package_tracker/delete_carrier",
        carrier_id: cid,
      });
      this._carriers = res.carriers || {};
      this._selectedCarrierId = Object.keys(this._carriers)[0] || null;
      this._isNewCarrier = false;
      this._render();
      this._showToast(`🗑️ "${cname}"`);
    } catch (err) {
      this._showToast("❌ " + (err.message || err));
    }
  }

  async _scanNow() {
    const t = this._t();
    this._showToast(t.toast_scanning);
    try {
      const res = await this._hass.callWS({ type: "mail_package_tracker/scan_now" });
      this._packages = res.packages || this._packages;
      this._recentEmails = res.recent_emails || this._recentEmails;
      this._render();
      this._showToast(t.toast_scanned);
    } catch (err) {
      this._showToast("❌ " + (err.message || err));
    }
  }

  async _runEmailTest(applyPackage = false) {
    const t = this._t();
    const root = this.shadowRoot;
    const sender = root.querySelector("#t-sender")?.value || "";
    const subject = root.querySelector("#t-subject")?.value || "";
    const body = root.querySelector("#t-body")?.value || "";
    const isHtml = /<[a-z][\s\S]*>/i.test(body);
    try {
      const res = await this._hass.callWS({
        type: "mail_package_tracker/test_email",
        sender,
        subject,
        text: isHtml ? "" : body,
        html: isHtml ? body : "",
        apply_package: applyPackage,
      });
      this._testResult = res.result;
      if (applyPackage && res.packages) {
        this._packages = res.packages;
        this._showToast(t.toast_applied);
      }
      this._renderTestResultOnly();
    } catch (err) {
      this._showToast("❌ " + (err.message || err));
    }
  }

  async _removePackage(uid) {
    const t = this._t();
    try {
      const res = await this._hass.callWS({
        type: "mail_package_tracker/remove_package",
        uid,
      });
      this._packages = res.packages || [];
      this._render();
      this._showToast(t.toast_removed);
    } catch (err) {
      this._showToast("❌ " + (err.message || err));
    }
  }

  _renderTestResultOnly() {
    const t = this._t();
    const box = this.shadowRoot?.querySelector("#test-result-box");
    if (!box || !this._testResult) return;
    const r = this._testResult;
    if (!r.matched) {
      box.innerHTML = `
        <div class="res-card res-fail">
          <h3>${t.res_no_match}</h3>
          <p><strong>${t.res_reason}</strong> ${this._escape(r.reason || r.matched_reason || "—")}</p>
        </div>
      `;
      return;
    }
    const items = (r.artikel_liste || [r.inhalt]).map((i) => `<li>${this._escape(i)}</li>`).join("");
    box.innerHTML = `
      <div class="res-card res-ok">
        <h3>${t.res_matched} ${this._escape(r.zusteller)} — <span class="badge">${this._escape(r.status)}</span> (${this._escape(r.zustellung)})</h3>
        <div class="res-grid">
          <div><strong>${t.res_pkg_id}</strong> <code>${this._escape(r.uid)}</code></div>
          <div><strong>${t.res_tid}</strong> <code>${this._escape(r.tracking_id || "—")}</code></div>
          <div><strong>${t.res_all_ids}</strong> <code>${this._escape((r.all_ids || []).join(", ") || "—")}</code></div>
          <div><strong>${t.res_match_reason}</strong> ${this._escape(r.matched_reason)}</div>
        </div>
        <div style="margin-top:10px;">
          <strong>${t.res_items((r.artikel_liste || []).length)}</strong>
          <ul style="margin:6px 0 10px 20px;">${items}</ul>
        </div>
        <div>
          <strong>${t.res_turl}</strong>
          <a href="${this._escape(r.tracking_url)}" target="_blank" rel="noopener">${this._escape(r.tracking_url)}</a>
        </div>
      </div>
    `;
  }

  _render() {
    const t = this._t();
    const curLang = this._currentLang();
    const cList = Object.entries(this._carriers)
      .filter(([, c]) => (c.language || "de") === curLang)
      .sort((a, b) => (a[1].name || a[0]).localeCompare(b[1].name || b[0]));

    if (!this._isNewCarrier) {
      const stillInLang = cList.some(([cid]) => cid === this._selectedCarrierId);
      if (!stillInLang) {
        this._selectedCarrierId = cList[0]?.[0] || null;
      }
    }

    const activeRule = this._isNewCarrier
      ? {
          id: "",
          name: "",
          icon: "mdi:package-variant-closed",
          language: curLang,
          enabled: true,
          sender_patterns: [],
          subject_patterns: [],
          ordered_patterns: curLang === "de" ? ["bestätigt", "bestellbestätigung"] : ["order confirmed", "thank you for your purchase"],
          in_transit_patterns: curLang === "de" ? ["versandt", "unterwegs", "auf dem weg"] : ["shipped", "in transit", "on the way"],
          out_for_delivery_patterns: curLang === "de" ? ["in zustellung", "kommt heute"] : ["out for delivery", "arriving today"],
          delivered_patterns: curLang === "de" ? ["zugestellt", "geliefert"] : ["delivered", "has been delivered"],
          tomorrow_patterns: curLang === "de" ? ["morgen"] : ["tomorrow", "arriving tomorrow"],
          exclude_patterns: curLang === "de" ? ["newsletter", "storniert"] : ["newsletter", "cancelled"],
          tracking_regex: curLang === "de" ? "DHL Trackingnummer:, Trackingnummer:, Bestellung" : "Tracking number:, Order #",
          content_regex: curLang === "de" ? "Artikel in dieser Lieferung, Bestellübersicht" : "Items in this shipment, *",
          tracking_url_regex: curLang === "de" ? "dhl.de, myhermes.de, tracking.dpd.de" : "ups.com, fedex.com, dhl.com",
          default_tracking_url: curLang === "de" ? "https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tracking_id}" : "",
        }
      : this._carriers[this._selectedCarrierId] || {};

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100vh;
          background: var(--primary-background-color, #111418);
          color: var(--primary-text-color, #e2e8f0);
          font-family: var(--paper-font-body1_-_font-family, Roboto, system-ui, sans-serif);
          box-sizing: border-box;
        }
        .topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 14px 24px;
          background: var(--app-header-background-color, var(--card-background-color, #1c2128));
          border-bottom: 1px solid var(--divider-color, rgba(255,255,255,0.08));
          gap: 14px;
          flex-wrap: wrap;
        }
        .brand {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .brand img {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          background: rgba(255,255,255,0.92);
          padding: 3px;
          box-sizing: border-box;
        }
        .brand h1 {
          margin: 0;
          font-size: 20px;
          font-weight: 600;
        }
        .brand p {
          margin: 2px 0 0 0;
          font-size: 12px;
          color: var(--secondary-text-color, #94a3b8);
        }
        .tabs {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          align-items: center;
        }
        .tab-btn {
          border: 1px solid var(--divider-color, rgba(255,255,255,0.12));
          background: transparent;
          color: var(--primary-text-color, #e2e8f0);
          padding: 8px 16px;
          border-radius: 20px;
          cursor: pointer;
          font-size: 13px;
          font-weight: 500;
          transition: all 0.15s;
        }
        .tab-btn.active {
          background: var(--primary-color, #03a9f4);
          color: #fff;
          border-color: var(--primary-color, #03a9f4);
        }
        .btn {
          border: none;
          background: var(--primary-color, #03a9f4);
          color: #fff;
          padding: 9px 16px;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          font-size: 13px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }
        .btn-sec {
          background: rgba(148, 163, 184, 0.16);
          color: var(--primary-text-color, #e2e8f0);
        }
        .btn-danger {
          background: rgba(239, 68, 68, 0.2);
          color: #f87171;
        }
        .container {
          max-width: 1320px;
          margin: 0 auto;
          padding: 20px 24px 60px;
        }
        .layout-split {
          display: grid;
          grid-template-columns: 310px 1fr;
          gap: 20px;
          align-items: start;
        }
        @media (max-width: 860px) {
          .layout-split {
            grid-template-columns: 1fr;
          }
        }
        .card {
          background: var(--card-background-color, #1c2128);
          border: 1px solid var(--divider-color, rgba(255,255,255,0.08));
          border-radius: 14px;
          padding: 18px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        }
        .carrier-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 10px 12px;
          border-radius: 10px;
          cursor: pointer;
          margin-bottom: 6px;
          border: 1px solid transparent;
          transition: all 0.12s;
        }
        .carrier-item:hover {
          background: rgba(148, 163, 184, 0.08);
        }
        .carrier-item.selected {
          background: rgba(3, 169, 244, 0.14);
          border-color: var(--primary-color, #03a9f4);
        }
        .carrier-name {
          font-weight: 500;
          font-size: 14px;
        }
        .carrier-sub {
          font-size: 11px;
          color: var(--secondary-text-color, #94a3b8);
        }
        .form-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 14px;
        }
        @media (max-width: 680px) {
          .form-grid {
            grid-template-columns: 1fr;
          }
        }
        .field {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        .field.full {
          grid-column: 1 / -1;
        }
        .field label {
          font-size: 12px;
          font-weight: 600;
          color: var(--secondary-text-color, #94a3b8);
        }
        .field small {
          font-size: 11px;
          color: var(--secondary-text-color, #94a3b8);
          opacity: 0.85;
        }
        input[type="text"], textarea, select {
          width: 100%;
          box-sizing: border-box;
          padding: 9px 12px;
          border-radius: 8px;
          border: 1px solid var(--divider-color, rgba(255,255,255,0.16));
          background: var(--primary-background-color, #111418);
          color: var(--primary-text-color, #e2e8f0);
          font-size: 13px;
          font-family: inherit;
        }
        textarea {
          min-height: 160px;
          resize: vertical;
        }
        .pkg-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 12px 14px;
          border-bottom: 1px solid var(--divider-color, rgba(255,255,255,0.08));
          flex-wrap: wrap;
        }
        .pkg-row:last-child {
          border-bottom: none;
        }
        .badge {
          display: inline-block;
          padding: 2px 9px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: 600;
          background: rgba(3, 169, 244, 0.2);
          color: #38bdf8;
        }
        .res-card {
          margin-top: 16px;
          padding: 16px;
          border-radius: 12px;
          border: 1px solid;
        }
        .res-ok {
          background: rgba(16, 185, 129, 0.1);
          border-color: rgba(16, 185, 129, 0.4);
        }
        .res-fail {
          background: rgba(239, 68, 68, 0.1);
          border-color: rgba(239, 68, 68, 0.4);
        }
        .res-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
          font-size: 13px;
        }
        a {
          color: var(--primary-color, #38bdf8);
        }
        #toast {
          position: fixed;
          bottom: 24px;
          right: 24px;
          background: #10b981;
          color: #fff;
          padding: 12px 20px;
          border-radius: 10px;
          font-weight: 500;
          font-size: 13px;
          box-shadow: 0 6px 20px rgba(0,0,0,0.3);
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.25s;
          z-index: 9999;
        }
        #toast.show {
          opacity: 1;
        }
      </style>

      <div class="topbar">
        <div class="brand">
          <button id="menu-btn" class="btn btn-sec" style="display:${this._narrow ? "inline-flex" : "none"};padding:8px 10px;">☰</button>
          <img src="/mail_package_tracker_brand/icon.png" alt="Logo" />
          <div>
            <h1>Mail Package Tracker</h1>
            <p>${t.subtitle(Object.keys(this._carriers).length, this._packages.length)}</p>
          </div>
        </div>
        <div class="tabs">
          <button class="tab-btn ${this._activeTab === "carriers" ? "active" : ""}" data-tab="carriers">${t.tab_carriers}</button>
          <button class="tab-btn ${this._activeTab === "tester" ? "active" : ""}" data-tab="tester">${t.tab_tester}</button>
          <button class="tab-btn ${this._activeTab === "packages" ? "active" : ""}" data-tab="packages">${t.tab_packages(this._packages.length)}</button>
          <button id="btn-scan-now" class="btn">${t.btn_scan_now}</button>
          <button id="btn-lang" class="btn btn-sec" title="DE / EN">${curLang === "de" ? "🇩🇪 DE" : "🇬🇧 EN"}</button>
        </div>
      </div>

      <div class="container">
        ${this._activeTab === "carriers" ? this._renderCarriersTab(cList, activeRule, t) : ""}
        ${this._activeTab === "tester" ? this._renderTesterTab(t) : ""}
        ${this._activeTab === "packages" ? this._renderPackagesTab(t) : ""}
      </div>

      <div id="toast"></div>
    `;

    this._bindEvents();
  }

  _renderCarriersTab(cList, r, t) {
    const curLang = this._currentLang();
    const rLang = r.language || curLang;
    const itemsHtml = cList.length
      ? cList
          .map(([cid, c]) => {
            const sel = !this._isNewCarrier && cid === this._selectedCarrierId ? "selected" : "";
            const senders = (c.sender_patterns || []).slice(0, 2).join(", ");
            const langBadge = `<span style="font-size:10px;opacity:0.85;margin-left:4px;">${(c.language || "de") === "de" ? "🇩🇪" : "🇬🇧"}</span>`;
            return `
              <div class="carrier-item ${sel}" data-cid="${this._escape(cid)}">
                <div>
                  <div class="carrier-name">${this._escape(c.name || cid)} ${langBadge}</div>
                  <div class="carrier-sub">${this._escape(senders)}</div>
                </div>
                <input type="checkbox" class="carrier-toggle" data-cid="${this._escape(cid)}" ${c.enabled !== false ? "checked" : ""} />
              </div>
            `;
          })
          .join("")
      : `<p style="font-size:12px;color:var(--secondary-text-color);margin:10px 0;">${t.empty_carriers_lang}</p>`;

    const carrierDisplayName = this._escape(r.name || this._selectedCarrierId || "");
    const jsonBoxHtml = this._jsonModalOpen
      ? `
        <div style="margin-bottom:18px;padding:14px;border-radius:10px;background:rgba(3,169,244,0.06);border:1px solid var(--primary-color, #03a9f4);">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px;">
            <strong style="font-size:15px;">
              ${this._jsonModalMode === "new" ? t.json_new_title : t.json_overwrite_title(carrierDisplayName)}
            </strong>
            <button id="btn-json-close" class="btn btn-sec" style="padding:5px 10px;font-size:12px;">${t.btn_close}</button>
          </div>
          <p style="margin:0 0 10px 0;font-size:12px;color:var(--secondary-text-color);">
            ${this._jsonModalMode === "new" ? t.json_new_desc : t.json_overwrite_desc(carrierDisplayName)}
          </p>
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;">
            <input id="json-file-input" type="file" accept=".json,application/json" style="display:none;" />
            <button id="btn-json-upload" class="btn btn-sec" style="padding:7px 12px;font-size:12px;">${t.btn_upload_file}</button>
            <button id="btn-json-download" class="btn btn-sec" style="padding:7px 12px;font-size:12px;">${t.btn_download_file}</button>
            <button id="btn-json-copy" class="btn btn-sec" style="padding:7px 12px;font-size:12px;">${t.btn_copy_json}</button>
            <button id="btn-json-validate" class="btn btn-sec" style="padding:7px 12px;font-size:12px;">${t.btn_validate_json}</button>
            <button id="btn-json-apply" class="btn" style="padding:7px 14px;font-size:12px;">
              ${this._jsonModalMode === "new" ? t.btn_apply_new_json : t.btn_apply_overwrite_json(carrierDisplayName)}
            </button>
          </div>
          <textarea id="json-modal-textarea" style="font-family:monospace;font-size:12px;min-height:200px;">${this._escape(this._jsonModalText)}</textarea>
          <div id="json-val-box"></div>
        </div>
      `
      : "";

    const rightCardHtml =
      !this._isNewCarrier && !this._selectedCarrierId
        ? `
          <div class="card">
            <h2 style="margin-top:0;font-size:18px;">${t.carriers_title} (${curLang === "de" ? "🇩🇪 DE" : "🇬🇧 EN"})</h2>
            <p style="font-size:13px;color:var(--secondary-text-color);margin-bottom:16px;">${t.empty_carriers_lang}</p>
            <div style="display:flex;gap:10px;flex-wrap:wrap;">
              <button id="btn-empty-new" class="btn">${t.btn_new}</button>
              <button id="btn-empty-import" class="btn btn-sec">${t.btn_import_new}</button>
            </div>
          </div>
        `
        : `
          <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px;">
              <h2 style="margin:0;font-size:18px;">
                ${this._isNewCarrier ? t.new_carrier_title : t.edit_carrier_title(carrierDisplayName)}
              </h2>
              <div style="display:flex;gap:8px;flex-wrap:wrap;">
                ${!this._isNewCarrier && this._selectedCarrierId ? `<button id="btn-import-overwrite-json" class="btn btn-sec">${t.btn_import_overwrite}</button>` : ""}
                <button id="btn-export-json" class="btn btn-sec">${t.btn_export_json}</button>
                ${!this._isNewCarrier && this._selectedCarrierId ? `<button id="btn-del-carrier" class="btn btn-danger">${t.btn_delete}</button>` : ""}
                <button id="btn-save-carrier" class="btn">${t.btn_save}</button>
              </div>
            </div>

            ${jsonBoxHtml}

            <div class="form-grid">
              <div class="field">
                <label>${t.lbl_name}</label>
                <input id="f-name" type="text" value="${this._escape(r.name || "")}" placeholder="${t.ph_name}" />
                <div style="display:flex;align-items:center;gap:10px;margin-top:6px;">
                  <label style="font-size:12px;color:var(--secondary-text-color);font-weight:600;white-space:nowrap;">${t.lbl_language}:</label>
                  <select id="f-lang" style="padding:5px 8px;font-size:12px;">
                    <option value="de" ${rLang === "de" ? "selected" : ""}>🇩🇪 Deutsch (de)</option>
                    <option value="en" ${rLang === "en" ? "selected" : ""}>🇬🇧 English (en)</option>
                  </select>
                </div>
              </div>
              <div class="field">
                <label>${t.lbl_id_icon}</label>
                <div style="display:flex;gap:8px;">
                  <input id="f-id" type="text" value="${this._escape(this._isNewCarrier ? "" : this._selectedCarrierId)}" ${this._isNewCarrier ? "" : "readonly"} placeholder="e.g. sunlu" style="flex:1;" />
                  <input id="f-icon" type="text" value="${this._escape(r.icon || "mdi:package-variant-closed")}" placeholder="mdi:package-variant" style="flex:1;" />
                </div>
                <label style="display:flex;align-items:center;gap:6px;margin-top:6px;cursor:pointer;">
                  <input id="f-enabled" type="checkbox" ${r.enabled !== false ? "checked" : ""} /> ${t.lbl_enabled}
                </label>
              </div>

              <div class="field">
                <label>${t.lbl_sender}</label>
                <input id="f-sender" type="text" value="${this._escape(this._listToStr(r.sender_patterns))}" placeholder="sunlu.com, dhl.de" />
                <small>${t.hint_sender}</small>
              </div>
              <div class="field">
                <label>${t.lbl_subject}</label>
                <input id="f-subject" type="text" value="${this._escape(this._listToStr(r.subject_patterns))}" placeholder="${t.ph_subject}" />
                <small>${t.hint_subject}</small>
              </div>

              <div class="field">
                <label>${t.lbl_ordered}</label>
                <input id="f-ordered" type="text" value="${this._escape(this._listToStr(r.ordered_patterns))}" />
                <small>${t.hint_ordered}</small>
              </div>
              <div class="field">
                <label>${t.lbl_transit}</label>
                <input id="f-transit" type="text" value="${this._escape(this._listToStr(r.in_transit_patterns))}" />
                <small>${t.hint_transit}</small>
              </div>

              <div class="field">
                <label>${t.lbl_ofd}</label>
                <input id="f-ofd" type="text" value="${this._escape(this._listToStr(r.out_for_delivery_patterns))}" />
              </div>
              <div class="field">
                <label>${t.lbl_delivered}</label>
                <input id="f-delivered" type="text" value="${this._escape(this._listToStr(r.delivered_patterns))}" />
              </div>

              <div class="field">
                <label>${t.lbl_tomorrow}</label>
                <input id="f-tomorrow" type="text" value="${this._escape(this._listToStr(r.tomorrow_patterns))}" />
              </div>
              <div class="field">
                <label>${t.lbl_exclude}</label>
                <input id="f-exclude" type="text" value="${this._escape(this._listToStr(r.exclude_patterns))}" />
              </div>

              <div class="field full">
                <label>${t.lbl_tregex}</label>
                <input id="f-tregex" type="text" value="${this._escape(r.tracking_regex || "")}" placeholder="DHL Trackingnummer:, Bestellung, Order #" />
                <small>${t.hint_tregex}</small>
              </div>

              <div class="field full">
                <label>${t.lbl_cregex}</label>
                <input id="f-cregex" type="text" value="${this._escape(r.content_regex || "")}" placeholder="Artikel in dieser Lieferung, Bestellübersicht, *" />
                <small>${t.hint_cregex}</small>
              </div>

              <div class="field">
                <label>${t.lbl_uregex}</label>
                <input id="f-uregex" type="text" value="${this._escape(r.tracking_url_regex || "")}" placeholder="dhl.de, myhermes.de, orders/" />
                <small>${t.hint_uregex}</small>
              </div>

              <div class="field">
                <label>${t.lbl_defurl}</label>
                <input id="f-defurl" type="text" value="${this._escape(r.default_tracking_url || "")}" placeholder="https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tracking_id}" />
                <small>${t.hint_defurl}</small>
              </div>
            </div>
          </div>
        `;

    return `
      <div class="layout-split">
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:6px;flex-wrap:wrap;">
            <strong style="font-size:15px;">${t.carriers_title} (${curLang === "de" ? "🇩🇪 DE" : "🇬🇧 EN"})</strong>
            <div style="display:flex;gap:6px;">
              <button id="btn-import-new-json" class="btn btn-sec" style="padding:6px 10px;font-size:12px;">${t.btn_import_new}</button>
              <button id="btn-new-carrier" class="btn" style="padding:6px 12px;font-size:12px;">${t.btn_new}</button>
            </div>
          </div>
          ${itemsHtml}
        </div>

        ${rightCardHtml}
      </div>
    `;
  }

  _renderTesterTab(t) {
    const emailOptions = this._recentEmails
      .map(
        (m, idx) =>
          `<option value="${idx}">[${this._escape(m.date || "")}] ${this._escape(m.sender || "")} — ${this._escape(m.subject || "")}</option>`
      )
      .join("");

    return `
      <div class="card">
        <h2 style="margin-top:0;font-size:18px;">${t.tester_title}</h2>
        <p style="font-size:13px;color:var(--secondary-text-color);">${t.tester_desc}</p>

        <div class="form-grid">
          <div class="field full">
            <label>${t.lbl_recent_select(this._recentEmails.length)}</label>
            <select id="t-select-recent">
              <option value="">${t.opt_recent_default}</option>
              ${emailOptions}
            </select>
          </div>
          <div class="field">
            <label>${t.lbl_t_sender}</label>
            <input id="t-sender" type="text" placeholder="SUNLU DE Store <sunlude@sunlu.com>" />
          </div>
          <div class="field">
            <label>${t.lbl_t_subject}</label>
            <input id="t-subject" type="text" placeholder="Shipment from order #SL123456DE is on the way" />
          </div>
          <div class="field full">
            <label>${t.lbl_t_body}</label>
            <textarea id="t-body" placeholder="${t.ph_t_body}"></textarea>
          </div>
        </div>

        <div style="display:flex;gap:10px;margin-top:14px;">
          <button id="btn-test-run" class="btn">${t.btn_test_run}</button>
          <button id="btn-test-apply" class="btn btn-sec">${t.btn_test_apply}</button>
        </div>

        <div id="test-result-box"></div>
      </div>
    `;
  }

  _renderPackagesTab(t) {
    if (!this._packages.length) {
      return `<div class="card"><p>${t.pkgs_empty}</p></div>`;
    }
    const rows = this._packages
      .map(
        (p) => `
        <div class="pkg-row">
          <div style="flex:1;min-width:240px;">
            <div style="font-weight:600;font-size:14px;">
              ${this._escape(p.zusteller)} • <span class="badge">${this._escape(p.status)}</span> (${this._escape(p.zustellung)})
            </div>
            <div style="font-size:13px;margin-top:4px;">📦 ${this._escape(p.inhalt)}</div>
            <div style="font-size:11px;color:var(--secondary-text-color);margin-top:4px;">
              ${t.res_tid} <code>${this._escape(p.tracking_id || "—")}</code> |
              ${t.res_all_ids} <code>${this._escape((p.all_ids || []).join(", ") || "—")}</code> |
              <a href="${this._escape(p.tracking_url || "#")}" target="_blank" rel="noopener">${t.open_tracking}</a>
            </div>
          </div>
          <button class="btn btn-danger btn-del-pkg" data-uid="${this._escape(p.uid)}">${t.btn_remove}</button>
        </div>
      `
      )
      .join("");

    return `
      <div class="card">
        <h2 style="margin-top:0;font-size:18px;">${t.pkgs_title(this._packages.length)}</h2>
        ${rows}
      </div>
    `;
  }

  _bindEvents() {
    const root = this.shadowRoot;
    root.querySelector("#menu-btn")?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
    });

    root.querySelector("#btn-lang")?.addEventListener("click", () => {
      this._lang = this._currentLang() === "de" ? "en" : "de";
      this._isNewCarrier = false;
      this._jsonModalOpen = false;
      this._render();
    });

    root.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._activeTab = btn.dataset.tab;
        this._render();
      });
    });

    root.querySelector("#btn-scan-now")?.addEventListener("click", () => this._scanNow());

    root.querySelectorAll(".carrier-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        if (e.target.classList.contains("carrier-toggle")) return;
        this._isNewCarrier = false;
        this._jsonModalOpen = false;
        this._selectedCarrierId = item.dataset.cid;
        this._render();
      });
    });

    root.querySelectorAll(".carrier-toggle").forEach((chk) => {
      chk.addEventListener("change", (e) => {
        e.stopPropagation();
        this._toggleCarrierQuick(chk.dataset.cid, chk.checked);
      });
    });

    root.querySelector("#btn-new-carrier")?.addEventListener("click", () => {
      this._isNewCarrier = true;
      this._jsonModalOpen = false;
      this._render();
    });
    root.querySelector("#btn-empty-new")?.addEventListener("click", () => {
      this._isNewCarrier = true;
      this._jsonModalOpen = false;
      this._render();
    });

    root.querySelector("#btn-import-new-json")?.addEventListener("click", () => this._openImportNewCarrierJson());
    root.querySelector("#btn-empty-import")?.addEventListener("click", () => this._openImportNewCarrierJson());
    root.querySelector("#btn-import-overwrite-json")?.addEventListener("click", () => this._openOverwriteCarrierJson());
    root.querySelector("#btn-export-json")?.addEventListener("click", () => this._exportCarrierDirect());
    root.querySelector("#btn-json-close")?.addEventListener("click", () => {
      this._jsonModalOpen = false;
      this._render();
    });
    root.querySelector("#btn-json-upload")?.addEventListener("click", () => {
      root.querySelector("#json-file-input")?.click();
    });
    root.querySelector("#json-file-input")?.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        this._jsonModalText = String(reader.result || "");
        const ta = root.querySelector("#json-modal-textarea");
        if (ta) ta.value = this._jsonModalText;
        this._validateOrImportJson(false);
      };
      reader.readAsText(file, "utf-8");
    });
    root.querySelector("#json-modal-textarea")?.addEventListener("input", () => {
      this._validateOrImportJson(false);
    });
    root.querySelector("#btn-json-download")?.addEventListener("click", () => this._downloadCurrentJson());
    root.querySelector("#btn-json-copy")?.addEventListener("click", () => this._copyCurrentJson());
    root.querySelector("#btn-json-validate")?.addEventListener("click", () => this._validateOrImportJson(false));
    root.querySelector("#btn-json-apply")?.addEventListener("click", () => this._validateOrImportJson(true));

    if (this._jsonModalOpen && this._jsonValidation) {
      this._renderJsonValidationOnly();
    }

    root.querySelector("#btn-save-carrier")?.addEventListener("click", () => this._saveCarrier());

    root.querySelector("#btn-del-carrier")?.addEventListener("click", () => {
      if (this._selectedCarrierId) this._deleteCarrier(this._selectedCarrierId);
    });

    root.querySelector("#t-select-recent")?.addEventListener("change", (e) => {
      const idx = parseInt(e.target.value, 10);
      if (!isNaN(idx) && this._recentEmails[idx]) {
        const m = this._recentEmails[idx];
        root.querySelector("#t-sender").value = m.sender || "";
        root.querySelector("#t-subject").value = m.subject || "";
        root.querySelector("#t-body").value = m.text || m.html || "";
        this._runEmailTest(false);
      }
    });

    root.querySelector("#btn-test-run")?.addEventListener("click", () => this._runEmailTest(false));
    root.querySelector("#btn-test-apply")?.addEventListener("click", () => this._runEmailTest(true));

    root.querySelectorAll(".btn-del-pkg").forEach((btn) => {
      btn.addEventListener("click", () => this._removePackage(btn.dataset.uid));
    });
  }
}

if (!customElements.get("mail-package-tracker-panel")) {
  customElements.define("mail-package-tracker-panel", MailPackageTrackerPanel);
}
