class ChildDosageCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("child-dosage-card-editor");
  }

  static getStubConfig() {
    return {
      title: "Medication dosage",
      child_name: "Child Name",
      show_paracetamol: true,
      show_ibuprofen: true,
      show_last_dose_time: true,
      show_time_since_last_dose: true,
      show_amount_in_last24h: true,
      show_dose_button: true,
      show_reset_button: true,
      show_child_name: true,
      show_child_age_weight: true,
      custom_medications: [],
      paracetamol_dose_size: "auto",
      ibuprofen_dose_size: "auto",
    };
  }

  setConfig(config) {
    if (!config.child_id && !config.child_name) {
      throw new Error("child_id or child_name is required");
    }

    this.config = {
      title: "Medication dosage",
      show_paracetamol: true,
      show_ibuprofen: true,
      show_last_dose_time: true,
      show_time_since_last_dose: true,
      show_amount_in_last24h: true,
      show_dose_button: true,
      show_reset_button: true,
      show_child_name: true,
      show_child_age_weight: true,
      custom_medications: [],
      paracetamol_dose_size: "auto",
      ibuprofen_dose_size: "auto",
      ...config,
    };
    this._root = this.attachShadow({ mode: "open" });
    this._root.innerHTML = `
      <style>
        .content { padding: 16px; display: grid; gap: 14px; }
        .title { font-size: 20px; font-weight: 600; }
        .child { color: var(--secondary-text-color); font-size: 14px; }
        .row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; border-top: 1px solid var(--divider-color); padding-top: 10px; }
        .details { display: grid; gap: 8px; min-width: 0; }
        .top { display: flex; justify-content: space-between; gap: 10px; }
        .dose-size { color: var(--secondary-text-color); font-size: 12px; }
        .meta { color: var(--secondary-text-color); font-size: 12px; display: grid; gap: 4px; }
        .actions { display: grid; gap: 8px; justify-items: stretch; align-content: center; }
        button { border: 0; border-radius: 8px; min-height: 36px; padding: 8px 10px; font: inherit; font-weight: 600; color: #fff; background: var(--primary-color); }
        button.dose { width: 88px; height: 88px; padding: 8px; }
        button.dose.ready { background: var(--success-color, #2e7d32); }
        button.dose.soon { background: var(--warning-color, #f57c00); }
        button.reset { min-height: 32px; padding: 6px 8px; font-size: 12px; color: #fff; background: #111; border: 1px solid var(--error-color, #d32f2f); }
        button.icon { width: 36px; min-height: 36px; padding: 6px; border-radius: 50%; color: var(--primary-text-color); background: transparent; }
        .bar { position: relative; height: 12px; border-radius: 6px; overflow: hidden; background: var(--divider-color); cursor: pointer; }
        .fill { position: absolute; inset: 0 auto 0 0; width: var(--fill-width); background: var(--bar-color); }
        .warning { color: var(--error-color, #d32f2f); font-size: 16px; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 36px; }
        .label { font-weight: 700; color: var(--primary-text-color); }
        .overlay { position: fixed; inset: 0; z-index: 1000; display: grid; place-items: center; padding: 18px; background: rgba(0, 0, 0, 0.42); }
        .dialog { width: min(420px, 100%); max-height: min(620px, calc(100vh - 36px)); display: grid; grid-template-rows: auto minmax(0, 1fr); border-radius: 8px; overflow: hidden; color: var(--primary-text-color); background: var(--card-background-color, #fff); box-shadow: 0 12px 36px rgba(0, 0, 0, 0.28); }
        .dialog-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 16px; border-bottom: 1px solid var(--divider-color); }
        .dialog-title { min-width: 0; display: grid; gap: 2px; }
        .dialog-title b { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .dialog-title span { color: var(--secondary-text-color); font-size: 12px; }
        .log { overflow: auto; padding: 8px 16px 16px; }
        .log-row { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 12px; align-items: center; padding: 11px 0; border-bottom: 1px solid var(--divider-color); }
        .log-row:last-child { border-bottom: 0; }
        .log-time { min-width: 0; display: grid; gap: 2px; }
        .log-date { color: var(--primary-text-color); font-weight: 600; overflow-wrap: anywhere; }
        .log-since { color: var(--secondary-text-color); font-size: 12px; }
        .log-dose { font-weight: 700; text-align: right; white-space: nowrap; }
        button.remove-dose { width: 32px; min-height: 32px; padding: 5px; color: #fff; background: #111; border: 1px solid var(--error-color, #d32f2f); }
        .empty { padding: 22px 16px 24px; color: var(--secondary-text-color); text-align: center; }
        @media (max-width: 520px) {
          .row { grid-template-columns: 1fr; }
          .actions { grid-template-columns: 88px max-content; justify-content: end; align-items: center; }
        }
      </style>
      <ha-card><div class="content"></div></ha-card>`;
    this._content = this._root.querySelector('.content');
  }

  set hass(hass) { this._hass = hass; if (this._content) this._render(); }
  getCardSize() { return 4; }

  _findStates() {
    const states = Object.entries(this._hass.states)
      .map(([entityId, state]) => ({ entityId, state }))
      .filter(({ state }) =>
        (state.attributes.child_id === this.config.child_id || state.attributes.child_name === this.config.child_name) &&
        state.attributes.medicine
      );
    const byMedicine = Object.fromEntries(states.map((item) => [item.state.attributes.medicine, item]));
    return byMedicine;
  }

  _render() {
    const states = this._findStates();
    const firstState = Object.values(states)[0];
    const attrs = firstState?.state.attributes || {};
    const childName = attrs.child_name || this.config.child_id || "Child";
    const ageWeight = this._childAgeWeight(attrs.date_of_birth, attrs.weight_kg);
    const meds = [];
    if (this.config.show_paracetamol) meds.push(["paracetamol", states.paracetamol]);
    if (this.config.show_ibuprofen) meds.push(["ibuprofen", states.ibuprofen]);
    for (const medicine of this._customMedicationNames(states)) {
      meds.push([medicine, states[medicine]]);
    }

    this._content.innerHTML = `
      <div class="title">${this._escape(this.config.title)}</div>
      ${this.config.show_child_name ? `<div class="child">${this._escape(childName)}</div>` : ""}
      ${this.config.show_child_age_weight ? `<div class="child">${this._escape(ageWeight)}</div>` : ""}
      ${meds.map(([name, item]) => this._medicineTemplate(name, item)).join("")}
    `;

    this._content.querySelectorAll("button[data-dose]").forEach((b) => b.addEventListener("click", () => this._giveDose(b.dataset.dose, b)));
    this._content.querySelectorAll("button[data-reset]").forEach((b) => b.addEventListener("click", () => this._resetDose(b.dataset.reset, b)));
    this._content.querySelectorAll(".bar[data-log]").forEach((bar) => bar.addEventListener("click", () => this._showDoseLog(bar.dataset.log, bar.dataset.medicine)));
  }

  _medicineTemplate(medicine, item) {
    const label = this._medicineLabel(medicine);
    if (!item) return `<div class="row"><div class="details"><div class="top"><b>${this._escape(label)}</b><span>sensor not found</span></div></div></div>`;
    const a = item.state.attributes;
    const total = Number(a.total_24h_mg || 0);
    const max = Number(a.max_24h_mg || 0);
    const percent = max > 0 ? Math.round((total / max) * 100) : 0;
    const fillWidth = Math.min(100, percent);
    const barColor = this._barColor(percent);
    const last = a.last_dose_at ? this._formatDateTime(a.last_dose_at) : "No doses recorded";
    const doseSize = this._doseSize(medicine, a);
    const consultWarning = a.consult_warning;
    return `
      <div class="row">
        <div class="details">
          <div class="top"><b>${this._escape(label)}</b><span>${a.doses_24h || 0}/${a.max_doses_24h || 0} doses</span></div>
          <div class="dose-size">Dose size: ${this._escape(doseSize.label)}</div>
          ${consultWarning ? `<div class="warning"><ha-icon icon="mdi:alert"></ha-icon><span>${this._escape(consultWarning)}</span></div>` : `<div class="bar" data-medicine="${this._escape(medicine)}" data-log='${this._escape(JSON.stringify(a.dose_log_48h || []))}' title="Show last 48h dose log"><div class="fill" style="--fill-width:${fillWidth}%; --bar-color:${barColor}"></div></div>`}
          ${!consultWarning && percent > 100 ? `<div class="warning"><ha-icon icon="mdi:alert"></ha-icon><span>24h Dose Exceeded</span></div>` : ""}
          <div class="meta">
            ${this.config.show_amount_in_last24h ? `<span><span class="label">Amount 24h:</span> ${this._formatMg(total)} / ${this._formatMg(max)}</span>` : ""}
            ${this.config.show_last_dose_time ? `<span><span class="label">Last dose:</span> ${last}</span>` : ""}
            ${this.config.show_time_since_last_dose ? `<span><span class="label">Since last:</span> ${this._timeSince(a.last_dose_at)}</span>` : ""}
          </div>
        </div>
        ${consultWarning ? "" : `<div class="actions">
          ${this.config.show_dose_button ? `<button class="dose ${this._doseButtonClass(a.last_dose_at)}" data-dose="${this._escape(medicine)}" data-dose-mg="${this._escape(doseSize.mg)}" data-last-dose-at="${this._escape(a.last_dose_at || "")}">Record ${this._escape(label)}</button>` : ""}
          ${this.config.show_reset_button ? `<button class="reset" data-reset="${this._escape(medicine)}">Reset</button>` : ""}
        </div>`}
      </div>`;
  }

  async _giveDose(medicine, button) {
    const childId = this._childId();
    if (!childId) return;
    const confirmation = this._doseIntervalConfirmation(button.dataset.lastDoseAt);
    if (confirmation && !window.confirm(confirmation)) return;
    button.disabled = true;
    try { await this._hass.callService("child_medication_dosage", "give_dose", { child_id: childId, medicine, dose_mg: Number(button.dataset.doseMg) }); }
    finally { button.disabled = false; }
  }

  async _resetDose(medicine, button) {
    const childId = this._childId();
    if (!childId) return;
    if (!window.confirm("This will reset dosage for the last 24 hours to zero, continue?")) return;
    button.disabled = true;
    try { await this._hass.callService("child_medication_dosage", "clear_history", { child_id: childId, medicine }); }
    finally { button.disabled = false; }
  }

  _showDoseLog(serializedLog, medicine) {
    const log = this._parseDoseLog(serializedLog);
    const rows = log.map((event) => `
      <div class="log-row">
        <div class="log-time">
          <span class="log-date">${this._escape(this._formatDateTime(event.given_at))}</span>
          <span class="log-since">${this._escape(this._relativeTimeLabel(event.given_at))}</span>
        </div>
        <span class="log-dose">${this._escape(this._formatMg(event.dose_mg))}</span>
        <button class="remove-dose" type="button" title="Remove dose" aria-label="Remove dose" data-medicine="${this._escape(medicine || "")}" data-given-at="${this._escape(event.given_at)}" data-dose-mg="${this._escape(event.dose_mg)}"><ha-icon icon="mdi:delete-outline"></ha-icon></button>
      </div>
    `);
    this._root.querySelector(".overlay")?.remove();
    const overlay = document.createElement("div");
    overlay.className = "overlay";
    overlay.innerHTML = `
      <section class="dialog" role="dialog" aria-modal="true" aria-label="${this._escape(this._titleCase(medicine || "dose"))} dose history">
        <header class="dialog-head">
          <div class="dialog-title">
            <b>${this._escape(this._titleCase(medicine || "Dose"))} history</b>
            <span>Last 48 hours</span>
          </div>
          <button class="icon" type="button" title="Close" aria-label="Close"><ha-icon icon="mdi:close"></ha-icon></button>
        </header>
        <div class="log">
          ${rows.length ? rows.join("") : `<div class="empty">No doses recorded in the last 48 hours.</div>`}
        </div>
      </section>
    `;
    const close = () => {
      this._root.removeEventListener("keydown", handleKeydown);
      overlay.remove();
    };
    const handleKeydown = (event) => {
      if (event.key === "Escape") close();
    };
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) close();
    });
    overlay.querySelector("button").addEventListener("click", close);
    overlay.querySelectorAll("button.remove-dose").forEach((button) => {
      button.addEventListener("click", () => this._removeDose(button));
    });
    this._root.appendChild(overlay);
    this._root.addEventListener("keydown", handleKeydown);
    overlay.querySelector("button").focus();
  }

  async _removeDose(button) {
    const childId = this._childId();
    if (!childId) return;
    if (!window.confirm("Remove this recorded dose?")) return;
    button.disabled = true;
    try {
      await this._hass.callService("child_medication_dosage", "remove_dose", {
        child_id: childId,
        medicine: button.dataset.medicine,
        given_at: button.dataset.givenAt,
        dose_mg: Number(button.dataset.doseMg),
      });
      const log = button.closest(".log");
      button.closest(".log-row")?.remove();
      if (log && !log.querySelector(".log-row")) {
        log.innerHTML = `<div class="empty">No doses recorded in the last 48 hours.</div>`;
      }
    } finally {
      button.disabled = false;
    }
  }

  _parseDoseLog(serializedLog) {
    try {
      const log = JSON.parse(serializedLog || "[]");
      return Array.isArray(log) ? log : [];
    } catch (_error) {
      return [];
    }
  }

  _childAgeWeight(dobIso, weightKg) {
    if (!dobIso) return weightKg ? `Weight: ${weightKg} kg` : "";
    const dob = new Date(dobIso);
    const now = new Date();
    let years = now.getFullYear() - dob.getFullYear();
    const m = now.getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && now.getDate() < dob.getDate())) years--;
    return `Age: ${years}y | Weight: ${weightKg || "?"} kg`;
  }

  _timeSince(value) {
    if (!value) return "n/a";
    const ms = Date.now() - new Date(value).getTime();
    if (Number.isNaN(ms) || ms < 0) return "Just now!";
    const mins = Math.floor(ms / 60000);
    if (mins < 60) return `${mins} ${mins === 1 ? "minute" : "minutes"}`;
    return `${Math.floor(mins / 60)}h ${mins % 60}m`;
  }
  _doseButtonClass(value) {
    if (!value) return "ready";
    const ms = Date.now() - new Date(value).getTime();
    if (Number.isNaN(ms) || ms < 0) return "soon";
    return ms >= 4 * 60 * 60 * 1000 ? "ready" : "soon";
  }
  _doseIntervalConfirmation(value) {
    if (!value) return "";
    const ms = Date.now() - new Date(value).getTime();
    if (Number.isNaN(ms) || ms < 0 || ms >= 4 * 60 * 60 * 1000) return "";
    const totalMinutes = Math.floor(ms / 60000);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    const hourLabel = `${hours} ${hours === 1 ? "hour" : "hours"}`;
    const minuteLabel = `${minutes} ${minutes === 1 ? "minute" : "minutes"}`;
    return `Last dose was given ${hourLabel} and ${minuteLabel} ago. Recommendation is 4-6 hours between doses. Confirm another dose?`;
  }
  _relativeTimeLabel(value) {
    const timeSince = this._timeSince(value);
    if (timeSince === "n/a") return "";
    if (timeSince === "Just now!") return "Just now";
    return `${timeSince} ago`;
  }
  _titleCase(value) { return String(value).charAt(0).toUpperCase() + String(value).slice(1); }
  _medicineLabel(value) {
    if (String(value).includes(" ")) return String(value);
    return this._titleCase(value);
  }
  _childId() {
    if (this.config.child_id) return this.config.child_id;
    const firstState = Object.values(this._findStates())[0];
    return firstState?.state.attributes.child_id;
  }
  _customMedicationNames(states) {
    const configured = Array.isArray(this.config.custom_medications)
      ? this.config.custom_medications
      : String(this.config.custom_medications || "").split(",");
    const names = configured.map((name) => String(name).trim()).filter(Boolean);
    if (names.length) return names;
    return Object.keys(states).filter((medicine) => !["paracetamol", "ibuprofen"].includes(medicine));
  }
  _doseSize(medicine, attributes = {}) {
    const options = {
      paracetamol: {
        "120mg/5ml liquid": 120,
        "250mg/5ml liquid": 250,
        "250mg tablet": 250,
      },
      ibuprofen: {
        "2.5ml/50mg": 50,
        "5ml/100mg": 100,
        "7.5ml/150mg": 150,
        "10ml/200mg": 200,
        "15ml/300mg": 300,
      },
    };
    if (!options[medicine]) {
      const mg = Number(attributes.recommended_dose_mg || 0);
      return { label: this._formatMg(mg), mg };
    }
    const configured = this.config[`${medicine}_dose_size`];
    const label = configured === "auto"
      ? this._autoDoseSize(medicine, attributes)
      : Object.prototype.hasOwnProperty.call(options[medicine], configured)
        ? configured
        : this._autoDoseSize(medicine, attributes);
    return { label, mg: options[medicine][label] };
  }
  _autoDoseSize(medicine, attributes = {}) {
    const months = this._ageMonths(attributes.date_of_birth);
    if (medicine === "paracetamol") {
      return months >= 72 ? "250mg/5ml liquid" : "120mg/5ml liquid";
    }
    if (medicine === "ibuprofen") {
      if (months < 12) return "2.5ml/50mg";
      if (months < 48) return "5ml/100mg";
      if (months < 84) return "7.5ml/150mg";
      if (months < 120) return "10ml/200mg";
      return "15ml/300mg";
    }
    return this._formatMg(Number(attributes.recommended_dose_mg || 0));
  }
  _ageMonths(dobIso) {
    if (!dobIso) return 0;
    const dob = new Date(dobIso);
    if (Number.isNaN(dob.getTime())) return 0;
    const now = new Date();
    let months = (now.getFullYear() - dob.getFullYear()) * 12 + now.getMonth() - dob.getMonth();
    if (now.getDate() < dob.getDate()) months--;
    return Math.max(0, months);
  }
  _barColor(percent) {
    if (percent >= 90) return "var(--error-color, #d32f2f)";
    if (percent >= 60) return "var(--warning-color, #fbc02d)";
    return "var(--ok-color, #2e7d32)";
  }
  _formatMg(value) { return `${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} mg`; }
  _formatDateTime(value) { const d = new Date(value); return Number.isNaN(d.getTime()) ? value : d.toLocaleString(); }
  _escape(value) { return String(value).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
}

class ChildDosageCardEditor extends HTMLElement {
  setConfig(config) {
    this.config = {
      ...ChildDosageCard.getStubConfig(),
      ...config,
    };
    if (!this._root) {
      this._root = this.attachShadow({ mode: "open" });
    }
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this.config) this._render();
  }

  _render() {
    const childOptions = this._childOptions();
    this._root.innerHTML = `
      <style>
        .editor { display: grid; gap: 16px; }
        .section { display: grid; gap: 10px; padding-block: 4px 10px; border-bottom: 1px solid var(--divider-color); }
        .section:last-child { border-bottom: 0; }
        .heading { font-size: 14px; font-weight: 700; color: var(--primary-text-color); }
        .grid { display: grid; gap: 10px; }
        .toggle { display: flex; align-items: center; justify-content: space-between; gap: 14px; min-height: 40px; }
        .toggle span { min-width: 0; }
        ha-textfield, ha-select { width: 100%; }
      </style>
      <div class="editor">
        <div class="section">
          <div class="heading">Child</div>
          ${childOptions.length ? `
            <ha-select label="Configured child" data-field="child_id" fixedMenuPosition value="${this._escape(this.config.child_id || "")}">
              <mwc-list-item value=""></mwc-list-item>
              ${childOptions.map((child) => `<mwc-list-item value="${this._escape(child.id)}">${this._escape(child.label)}</mwc-list-item>`).join("")}
            </ha-select>
          ` : ""}
          <ha-textfield label="Child ID" data-field="child_id" value="${this._escape(this.config.child_id || "")}"></ha-textfield>
          <ha-textfield label="Child name" data-field="child_name" value="${this._escape(this.config.child_name || "")}"></ha-textfield>
        </div>

        <div class="section">
          <div class="heading">Header</div>
          <ha-textfield label="Title" data-field="title" value="${this._escape(this.config.title || "")}"></ha-textfield>
          ${this._toggleTemplate("show_child_name", "Show child name")}
          ${this._toggleTemplate("show_child_age_weight", "Show child age and weight")}
        </div>

        <div class="section">
          <div class="heading">Medicines</div>
          ${this._toggleTemplate("show_paracetamol", "Show paracetamol")}
          <ha-select label="Paracetamol dose size" data-field="paracetamol_dose_size" fixedMenuPosition value="${this._escape(this.config.paracetamol_dose_size || "auto")}">
            ${this._doseOptionTemplates(["auto", "120mg/5ml liquid", "250mg/5ml liquid", "250mg tablet"])}
          </ha-select>
          ${this._toggleTemplate("show_ibuprofen", "Show ibuprofen")}
          <ha-select label="Ibuprofen dose size" data-field="ibuprofen_dose_size" fixedMenuPosition value="${this._escape(this.config.ibuprofen_dose_size || "auto")}">
            ${this._doseOptionTemplates(["auto", "2.5ml/50mg", "5ml/100mg", "7.5ml/150mg", "10ml/200mg", "15ml/300mg"])}
          </ha-select>
          <ha-textfield label="Custom medications" helper="Comma-separated names, or leave blank to show all discovered custom medicines" data-field="custom_medications" value="${this._escape(this._customMedicationsValue())}"></ha-textfield>
        </div>

        <div class="section">
          <div class="heading">Rows</div>
          ${this._toggleTemplate("show_last_dose_time", "Show last dose time")}
          ${this._toggleTemplate("show_time_since_last_dose", "Show time since last dose")}
          ${this._toggleTemplate("show_amount_in_last24h", "Show amount in last 24h")}
          ${this._toggleTemplate("show_dose_button", "Show record dose button")}
          ${this._toggleTemplate("show_reset_button", "Show reset button")}
        </div>
      </div>
    `;

    this._root.querySelectorAll("ha-textfield").forEach((field) => {
      field.addEventListener("input", () => this._valueChanged(field));
      field.addEventListener("change", () => this._valueChanged(field));
    });
    this._root.querySelectorAll("ha-select").forEach((field) => {
      field.addEventListener("selected", () => this._valueChanged(field));
      field.addEventListener("closed", () => this._valueChanged(field));
      field.addEventListener("change", () => this._valueChanged(field));
    });
    this._root.querySelectorAll("ha-switch").forEach((field) => {
      field.addEventListener("change", () => this._valueChanged(field));
    });
  }

  _toggleTemplate(field, label) {
    return `
      <label class="toggle">
        <span>${this._escape(label)}</span>
        <ha-switch data-field="${this._escape(field)}" ${this.config[field] ? "checked" : ""}></ha-switch>
      </label>
    `;
  }

  _doseOptionTemplates(options) {
    return options.map((option) => `<mwc-list-item value="${this._escape(option)}">${this._escape(option)}</mwc-list-item>`).join("");
  }

  _valueChanged(element) {
    const field = element.dataset.field;
    if (!field) return;
    let value = element.checked;
    if (element.tagName !== "HA-SWITCH") {
      value = element.value;
    }
    if (field === "custom_medications") {
      value = String(value || "").split(",").map((name) => name.trim()).filter(Boolean);
    }
    const config = { ...this.config, [field]: value };
    if (field === "child_id" && value) delete config.child_name;
    if (field === "child_name" && value) delete config.child_id;
    this.config = config;
    this.dispatchEvent(new CustomEvent("config-changed", {
      bubbles: true,
      composed: true,
      detail: { config },
    }));
  }

  _customMedicationsValue() {
    const value = this.config.custom_medications;
    return Array.isArray(value) ? value.join(", ") : String(value || "");
  }

  _childOptions() {
    const children = new Map();
    for (const state of Object.values(this._hass?.states || {})) {
      const attrs = state.attributes || {};
      if (!attrs.child_id || !attrs.medicine) continue;
      const label = attrs.child_name ? `${attrs.child_name} (${attrs.child_id})` : attrs.child_id;
      children.set(attrs.child_id, { id: attrs.child_id, label });
    }
    return [...children.values()].sort((a, b) => a.label.localeCompare(b.label));
  }

  _escape(value) {
    return String(value).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  }
}

customElements.define("child-dosage-card", ChildDosageCard);
customElements.define("child-dosage-card-editor", ChildDosageCardEditor);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "child-dosage-card",
  name: "Child Dosage Card",
  description: "Track child medication doses.",
  preview: true,
  documentationURL: "https://github.com/hjennerway/child-dosimeter",
});
