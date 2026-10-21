class MailPackageTrackerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._narrow = false;
    this._activeTab = "carriers";
    this._carriers = {};
    this._packages = [];
    this._recentEmails = [];
    this._selectedCarrierId = null;
    this._isNewCarrier = false;
    this._testResult = null;
    this._statusMsg = "";
    this._loading = false;
    this._loadedOnce = false;
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
      this._statusMsg = "Fehler beim Laden: " + (err.message || err);
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

  async _saveCarrier() {
    const root = this.shadowRoot;
    const name = root.querySelector("#f-name")?.value.trim() || "Neuer Lieferant";
    const idInput = root.querySelector("#f-id")?.value.trim() || name.toLowerCase().replace(/[^a-z0-9]+/g, "_");
    const rule = {
      name,
      icon: root.querySelector("#f-icon")?.value.trim() || "mdi:package-variant-closed",
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

    try {
      const res = await this._hass.callWS({
        type: "mail_package_tracker/save_carrier",
        carrier_id: idInput,
        rule,
        rescan: true,
      });
      this._carriers = res.carriers || this._carriers;
      this._packages = res.packages || this._packages;
      this._selectedCarrierId = res.carrier_id;
      this._isNewCarrier = false;
      this._render();
      this._showToast(`✅ Filterregel für "${name}" gespeichert & E-Mails geprüft!`);
    } catch (err) {
      this._showToast("❌ Fehler beim Speichern: " + (err.message || err));
    }
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
      this._showToast(`${enabled ? "🟢 Aktiviert" : "⚪ Pausiert"}: ${rule.name || cid}`);
    } catch (err) {
      this._showToast("❌ Fehler: " + (err.message || err));
    }
  }

  async _deleteCarrier(cid) {
    const cname = this._carriers[cid]?.name || cid;
    if (!confirm(`Lieferant "${cname}" wirklich löschen?`)) return;
    try {
      const res = await this._hass.callWS({
        type: "mail_package_tracker/delete_carrier",
        carrier_id: cid,
      });
      this._carriers = res.carriers || {};
      this._selectedCarrierId = Object.keys(this._carriers)[0] || null;
      this._isNewCarrier = false;
      this._render();
      this._showToast(`🗑️ "${cname}" gelöscht.`);
    } catch (err) {
      this._showToast("❌ Fehler: " + (err.message || err));
    }
  }

  async _scanNow() {
    this._showToast("🔄 Suche nach neuen E-Mails...");
    try {
      const res = await this._hass.callWS({ type: "mail_package_tracker/scan_now" });
      this._packages = res.packages || this._packages;
      this._recentEmails = res.recent_emails || this._recentEmails;
      this._render();
      this._showToast("✅ E-Mail-Postfach erfolgreich synchronisiert!");
    } catch (err) {
      this._showToast("❌ Scan-Fehler: " + (err.message || err));
    }
  }

  async _runEmailTest(applyPackage = false) {
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
        this._showToast("✅ E-Mail als Paket übernommen!");
      }
      this._renderTestResultOnly();
    } catch (err) {
      this._showToast("❌ Fehler beim Testen: " + (err.message || err));
    }
  }

  async _removePackage(uid) {
    try {
      const res = await this._hass.callWS({
        type: "mail_package_tracker/remove_package",
        uid,
      });
      this._packages = res.packages || [];
      this._render();
      this._showToast("🗑️ Paket entfernt.");
    } catch (err) {
      this._showToast("❌ Fehler: " + (err.message || err));
    }
  }

  _renderTestResultOnly() {
    const box = this.shadowRoot?.querySelector("#test-result-box");
    if (!box || !this._testResult) return;
    const r = this._testResult;
    if (!r.matched) {
      box.innerHTML = `
        <div class="res-card res-fail">
          <h3>❌ Kein Treffer</h3>
          <p><strong>Grund:</strong> ${this._escape(r.matched_reason || "Keine passende Regel gefunden")}</p>
        </div>
      `;
      return;
    }
    const items = (r.artikel_liste || [r.inhalt]).map((i) => `<li>${this._escape(i)}</li>`).join("");
    box.innerHTML = `
      <div class="res-card res-ok">
        <h3>✅ Erkannt: ${this._escape(r.zusteller)} — <span class="badge">${this._escape(r.status)}</span> (${this._escape(r.zustellung)})</h3>
        <div class="res-grid">
          <div><strong>Paket-ID:</strong> <code>${this._escape(r.uid)}</code></div>
          <div><strong>Tracking-Nr.:</strong> <code>${this._escape(r.tracking_id || "—")}</code></div>
          <div><strong>Alle erkannten IDs:</strong> <code>${this._escape((r.all_ids || []).join(", ") || "—")}</code></div>
          <div><strong>Treffer-Grund:</strong> ${this._escape(r.matched_reason)}</div>
        </div>
        <div style="margin-top:10px;">
          <strong>Extrahierte Artikel (${(r.artikel_liste || []).length}):</strong>
          <ul style="margin:6px 0 10px 20px;">${items}</ul>
        </div>
        <div>
          <strong>Tracking-Link:</strong>
          <a href="${this._escape(r.tracking_url)}" target="_blank" rel="noopener">${this._escape(r.tracking_url)}</a>
        </div>
      </div>
    `;
  }

  _render() {
    const cList = Object.entries(this._carriers).sort((a, b) =>
      (a[1].name || a[0]).localeCompare(b[1].name || b[0])
    );
    const activeRule = this._isNewCarrier
      ? {
          id: "",
          name: "",
          icon: "mdi:package-variant-closed",
          enabled: true,
          sender_patterns: [],
          subject_patterns: [],
          ordered_patterns: ["bestätigt", "bestellbestätigung", "vielen dank für deinen einkauf"],
          in_transit_patterns: ["versandt", "unterwegs", "auf dem weg", "shipped"],
          out_for_delivery_patterns: ["in zustellung", "kommt heute"],
          delivered_patterns: ["zugestellt", "geliefert", "delivered"],
          tomorrow_patterns: ["morgen", "tomorrow"],
          exclude_patterns: ["newsletter", "storniert"],
          tracking_regex: "Trackingnummer:, Sendungsnummer:, Bestellung",
          content_regex: "Artikel in dieser Lieferung, Bestellübersicht",
          tracking_url_regex: "dhl.de, myhermes.de, tracking.dpd.de, orders/",
          default_tracking_url: "https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tracking_id}",
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
            <p>${Object.keys(this._carriers).length} Lieferanten • ${this._packages.length} gespeicherte Pakete</p>
          </div>
        </div>
        <div class="tabs">
          <button class="tab-btn ${this._activeTab === "carriers" ? "active" : ""}" data-tab="carriers">⚙️ Lieferanten & Filterregeln</button>
          <button class="tab-btn ${this._activeTab === "tester" ? "active" : ""}" data-tab="tester">🧪 Live E-Mail-Tester</button>
          <button class="tab-btn ${this._activeTab === "packages" ? "active" : ""}" data-tab="packages">📦 Pakete (${this._packages.length})</button>
          <button id="btn-scan-now" class="btn">🔄 Jetzt E-Mails prüfen</button>
        </div>
      </div>

      <div class="container">
        ${this._activeTab === "carriers" ? this._renderCarriersTab(cList, activeRule) : ""}
        ${this._activeTab === "tester" ? this._renderTesterTab() : ""}
        ${this._activeTab === "packages" ? this._renderPackagesTab() : ""}
      </div>

      <div id="toast"></div>
    `;

    this._bindEvents();
  }

  _renderCarriersTab(cList, r) {
    const itemsHtml = cList
      .map(([cid, c]) => {
        const sel = !this._isNewCarrier && cid === this._selectedCarrierId ? "selected" : "";
        const senders = (c.sender_patterns || []).slice(0, 2).join(", ");
        return `
          <div class="carrier-item ${sel}" data-cid="${this._escape(cid)}">
            <div>
              <div class="carrier-name">${this._escape(c.name || cid)}</div>
              <div class="carrier-sub">${this._escape(senders)}</div>
            </div>
            <input type="checkbox" class="carrier-toggle" data-cid="${this._escape(cid)}" ${c.enabled !== false ? "checked" : ""} title="Filterregel aktiv" />
          </div>
        `;
      })
      .join("");

    return `
      <div class="layout-split">
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <strong style="font-size:15px;">Lieferanten / Shops</strong>
            <button id="btn-new-carrier" class="btn" style="padding:6px 12px;font-size:12px;">➕ Neu</button>
          </div>
          ${itemsHtml}
        </div>

        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px;">
            <h2 style="margin:0;font-size:18px;">
              ${this._isNewCarrier ? "➕ Neuen Lieferanten anlegen" : `✏️ Filterregel: ${this._escape(r.name || this._selectedCarrierId)}`}
            </h2>
            <div style="display:flex;gap:8px;">
              ${!this._isNewCarrier && this._selectedCarrierId ? `<button id="btn-del-carrier" class="btn btn-danger">🗑️ Löschen</button>` : ""}
              <button id="btn-save-carrier" class="btn">💾 Speichern & E-Mails neu prüfen</button>
            </div>
          </div>

          <div class="form-grid">
            <div class="field">
              <label>Name des Lieferanten / Shops</label>
              <input id="f-name" type="text" value="${this._escape(r.name || "")}" placeholder="z.B. Sunlu, Amazon, DHL..." />
            </div>
            <div class="field">
              <label>Interne Kennung (ID) & Icon</label>
              <div style="display:flex;gap:8px;">
                <input id="f-id" type="text" value="${this._escape(this._isNewCarrier ? "" : this._selectedCarrierId)}" ${this._isNewCarrier ? "" : "readonly"} placeholder="z.B. sunlu" style="flex:1;" />
                <input id="f-icon" type="text" value="${this._escape(r.icon || "mdi:package-variant-closed")}" placeholder="mdi:package-variant" style="flex:1;" />
              </div>
              <label style="display:flex;align-items:center;gap:6px;margin-top:4px;cursor:pointer;">
                <input id="f-enabled" type="checkbox" ${r.enabled !== false ? "checked" : ""} /> Regel ist aktiv
              </label>
            </div>

            <div class="field">
              <label>📧 Absender enthält (kommagetrennt)</label>
              <input id="f-sender" type="text" value="${this._escape(this._listToStr(r.sender_patterns))}" placeholder="z.B. sunlu.com, dhl.de" />
              <small>Mindestens einer dieser Begriffe muss in der Absender-Adresse stehen.</small>
            </div>
            <div class="field">
              <label>📌 Betreff muss enthalten (optional, kommagetrennt)</label>
              <input id="f-subject" type="text" value="${this._escape(this._listToStr(r.subject_patterns))}" placeholder="Leer lassen = alle Betreffs erlauben" />
              <small>Optionaler Vorfilter auf die Betreffzeile.</small>
            </div>

            <div class="field">
              <label>🛒 Wörter für „Bestellt (Warte auf Versand)“</label>
              <input id="f-ordered" type="text" value="${this._escape(this._listToStr(r.ordered_patterns))}" />
              <small>Erzeugt ein Paket unter „Warte auf Versand“, bis die Versandmail eintrifft.</small>
            </div>
            <div class="field">
              <label>🚚 Wörter für „Unterwegs (Versendet)“</label>
              <input id="f-transit" type="text" value="${this._escape(this._listToStr(r.in_transit_patterns))}" />
              <small>Stuft das Paket auf „Unterwegs“ hoch.</small>
            </div>

            <div class="field">
              <label>⚡ Wörter für „In Zustellung (Kommt heute)“</label>
              <input id="f-ofd" type="text" value="${this._escape(this._listToStr(r.out_for_delivery_patterns))}" />
            </div>
            <div class="field">
              <label>✅ Wörter für „Zugestellt (Geliefert)“</label>
              <input id="f-delivered" type="text" value="${this._escape(this._listToStr(r.delivered_patterns))}" />
            </div>

            <div class="field">
              <label>📅 Wörter für „Ankunft morgen“</label>
              <input id="f-tomorrow" type="text" value="${this._escape(this._listToStr(r.tomorrow_patterns))}" />
            </div>
            <div class="field">
              <label>🚫 Ausschluss-Wörter (Werbung / Storno ignorieren)</label>
              <input id="f-exclude" type="text" value="${this._escape(this._listToStr(r.exclude_patterns))}" />
            </div>

            <div class="field full">
              <label>🔢 Tracking- / Bestellnummer (Text davor oder Regex, kommagetrennt)</label>
              <input id="f-tregex" type="text" value="${this._escape(r.tracking_regex || "")}" placeholder="z.B. DHL Trackingnummer:, Bestellung" />
              <small>Einfach den Text vor der Nummer angeben (z.B. <code>DHL Trackingnummer:, Bestellung</code>). Alle gefundenen Nummern werden verknüpft, damit Bestellbestätigung & Versandmail automatisch zusammengeführt werden!</small>
            </div>

            <div class="field full">
              <label>📦 Paket-Inhalt / Artikel-Liste (Überschrift in der Mail, * für Aufzählung oder Regex)</label>
              <input id="f-cregex" type="text" value="${this._escape(r.content_regex || "")}" placeholder="z.B. Artikel in dieser Lieferung, Bestellübersicht oder *" />
              <small>Liest automatisch auch mehrere Artikel aus einer Lieferung aus (z.B. „3 Artikel: 1 PETG + 1 PLA+...“).</small>
            </div>

            <div class="field">
              <label>🔗 Tracking-Link in der Mail enthält (kommagetrennt)</label>
              <input id="f-uregex" type="text" value="${this._escape(r.tracking_url_regex || "")}" placeholder="z.B. dhl.de, myhermes.de, orders/" />
              <small>Suchbegriffe für den Tracking-Link im E-Mail-HTML.</small>
            </div>

            <div class="field">
              <label>🌐 Standard Tracking-URL (mit {tracking_id} Platzhalter)</label>
              <input id="f-defurl" type="text" value="${this._escape(r.default_tracking_url || "")}" placeholder="https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tracking_id}" />
              <small>Wird für versendete Pakete genutzt, wenn die Mail keinen direkten deutschen Tracking-Link enthält (ersetzt <code>{tracking_id}</code> durch die Sendungsnummer).</small>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  _renderTesterTab() {
    const emailOptions = this._recentEmails
      .map(
        (m, idx) =>
          `<option value="${idx}">[${this._escape(m.date || "")}] ${this._escape(m.sender || "")} — ${this._escape(m.subject || "")}</option>`
      )
      .join("");

    return `
      <div class="card">
        <h2 style="margin-top:0;font-size:18px;">🧪 Live E-Mail-Tester</h2>
        <p style="font-size:13px;color:var(--secondary-text-color);">
          Wähle eine der letzten empfangenen E-Mails aus oder füge eigenen Text / HTML ein, um sofort zu sehen, wie deine Filterregeln die E-Mail auswerten.
        </p>

        <div class="form-grid">
          <div class="field full">
            <label>📥 Aus letzten empfangenen E-Mails auswählen (${this._recentEmails.length} gespeichert)</label>
            <select id="t-select-recent">
              <option value="">— E-Mail aus dem Postfach auswählen, um Felder auszufüllen —</option>
              ${emailOptions}
            </select>
          </div>
          <div class="field">
            <label>Absender (Von)</label>
            <input id="t-sender" type="text" placeholder="z.B. SUNLU DE Store <sunlude@sunlu.com>" />
          </div>
          <div class="field">
            <label>Betreff</label>
            <input id="t-subject" type="text" placeholder="z.B. Eine Sendung aus der Bestellung #SL145110DE26 ist unterwegs" />
          </div>
          <div class="field full">
            <label>E-Mail-Inhalt (normaler Text oder HTML)</label>
            <textarea id="t-body" placeholder="Kopiere hier den Text der E-Mail hinein oder wähle oben eine empfangene E-Mail aus..."></textarea>
          </div>
        </div>

        <div style="display:flex;gap:10px;margin-top:14px;">
          <button id="btn-test-run" class="btn">🔍 Gegen Filterregeln testen</button>
          <button id="btn-test-apply" class="btn btn-sec">📥 Als Paket übernehmen</button>
        </div>

        <div id="test-result-box"></div>
      </div>
    `;
  }

  _renderPackagesTab() {
    if (!this._packages.length) {
      return `<div class="card"><p>Aktuell sind keine Pakete gespeichert.</p></div>`;
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
              Tracking-Nr.: <code>${this._escape(p.tracking_id || "—")}</code> |
              Alle IDs: <code>${this._escape((p.all_ids || []).join(", ") || "—")}</code> |
              <a href="${this._escape(p.tracking_url || "#")}" target="_blank" rel="noopener">Tracking öffnen ↗</a>
            </div>
          </div>
          <button class="btn btn-danger btn-del-pkg" data-uid="${this._escape(p.uid)}">🗑️ Entfernen</button>
        </div>
      `
      )
      .join("");

    return `
      <div class="card">
        <h2 style="margin-top:0;font-size:18px;">📦 Gespeicherte Pakete (${this._packages.length})</h2>
        ${rows}
      </div>
    `;
  }

  _bindEvents() {
    const root = this.shadowRoot;
    root.querySelector("#menu-btn")?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
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
      this._render();
    });

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
