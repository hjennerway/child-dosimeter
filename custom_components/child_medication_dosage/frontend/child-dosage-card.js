class ChildDosageCard extends HTMLElement {
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
      paracetamol_dose_size: "120mg/5ml liquid",
      ibuprofen_dose_size: "5ml/100mg",
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
        button.reset { min-height: 32px; padding: 6px 8px; font-size: 12px; background: var(--error-color, #d32f2f); }
        .bar { position: relative; height: 12px; border-radius: 6px; overflow: hidden; background: var(--divider-color); cursor: pointer; }
        .fill { position: absolute; inset: 0 auto 0 0; width: var(--fill-width); background: var(--bar-color); }
        .warning { color: var(--error-color, #d32f2f); font-size: 16px; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 36px; }
        .label { font-weight: 700; color: var(--primary-text-color); }
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
        ["paracetamol", "ibuprofen"].includes(state.attributes.medicine)
      );
    const byMedicine = Object.fromEntries(states.map((item) => [item.state.attributes.medicine, item]));
    return { paracetamol: byMedicine.paracetamol, ibuprofen: byMedicine.ibuprofen };
  }

  _render() {
    const states = this._findStates();
    const attrs = states.paracetamol?.state.attributes || states.ibuprofen?.state.attributes || {};
    const childName = attrs.child_name || this.config.child_id || "Child";
    const ageWeight = this._childAgeWeight(attrs.date_of_birth, attrs.weight_kg);
    const meds = [];
    if (this.config.show_paracetamol) meds.push(["paracetamol", states.paracetamol]);
    if (this.config.show_ibuprofen) meds.push(["ibuprofen", states.ibuprofen]);

    this._content.innerHTML = `
      <div class="title">${this._escape(this.config.title)}</div>
      ${this.config.show_child_name ? `<div class="child">${this._escape(childName)}</div>` : ""}
      ${this.config.show_child_age_weight ? `<div class="child">${this._escape(ageWeight)}</div>` : ""}
      ${meds.map(([name, item]) => this._medicineTemplate(name, item)).join("")}
    `;

    this._content.querySelectorAll("button[data-dose]").forEach((b) => b.addEventListener("click", () => this._giveDose(b.dataset.dose, b)));
    this._content.querySelectorAll("button[data-reset]").forEach((b) => b.addEventListener("click", () => this._resetDose(b.dataset.reset, b)));
    this._content.querySelectorAll(".bar[data-log]").forEach((bar) => bar.addEventListener("click", () => this._showDoseLog(bar.dataset.log)));
  }

  _medicineTemplate(medicine, item) {
    const label = this._titleCase(medicine);
    if (!item) return `<div class="row"><div class="details"><div class="top"><b>${label}</b><span>sensor not found</span></div></div></div>`;
    const a = item.state.attributes;
    const total = Number(a.total_24h_mg || 0);
    const max = Number(a.max_24h_mg || 0);
    const percent = max > 0 ? Math.round((total / max) * 100) : 0;
    const fillWidth = Math.min(100, percent);
    const barColor = this._barColor(percent);
    const last = a.last_dose_at ? this._formatDateTime(a.last_dose_at) : "No doses recorded";
    const doseSize = this._doseSize(medicine);
    return `
      <div class="row">
        <div class="details">
          <div class="top"><b>${label}</b><span>${a.doses_24h || 0}/${a.max_doses_24h || 0} doses</span></div>
          <div class="dose-size">Dose size: ${this._escape(doseSize.label)}</div>
          <div class="bar" data-log='${this._escape(JSON.stringify(a.dose_log_48h || []))}' title="Show last 48h dose log"><div class="fill" style="--fill-width:${fillWidth}%; --bar-color:${barColor}"></div></div>
          ${percent > 100 ? `<div class="warning"><ha-icon icon="mdi:alert"></ha-icon><span>24h Dose Exceeded</span></div>` : ""}
          <div class="meta">
            ${this.config.show_amount_in_last24h ? `<span><span class="label">Amount 24h:</span> ${this._formatMg(total)} / ${this._formatMg(max)}</span>` : ""}
            ${this.config.show_last_dose_time ? `<span><span class="label">Last dose:</span> ${last}</span>` : ""}
            ${this.config.show_time_since_last_dose ? `<span><span class="label">Since last:</span> ${this._timeSince(a.last_dose_at)}</span>` : ""}
          </div>
        </div>
        <div class="actions">
          ${this.config.show_dose_button ? `<button class="dose" data-dose="${medicine}">Record ${label}</button>` : ""}
          ${this.config.show_reset_button ? `<button class="reset" data-reset="${medicine}">Reset</button>` : ""}
        </div>
      </div>`;
  }

  async _giveDose(medicine, button) {
    const childId = this.config.child_id || this._findStates().paracetamol?.state.attributes.child_id || this._findStates().ibuprofen?.state.attributes.child_id;
    if (!childId) return;
    const doseSize = this._doseSize(medicine);
    button.disabled = true;
    try { await this._hass.callService("child_medication_dosage", "give_dose", { child_id: childId, medicine, dose_mg: doseSize.mg }); }
    finally { button.disabled = false; }
  }

  async _resetDose(medicine, button) {
    const childId = this.config.child_id || this._findStates().paracetamol?.state.attributes.child_id || this._findStates().ibuprofen?.state.attributes.child_id;
    if (!childId) return;
    if (!window.confirm("This will reset dosage for the last 24 hours to zero, continue?")) return;
    button.disabled = true;
    try { await this._hass.callService("child_medication_dosage", "clear_history", { child_id: childId, medicine }); }
    finally { button.disabled = false; }
  }

  _showDoseLog(serializedLog) {
    const log = this._parseDoseLog(serializedLog);
    if (!log.length) {
      window.alert("No doses recorded in the last 48 hours.");
      return;
    }
    const lines = log.map((event) => `- ${this._formatDateTime(event.given_at)} - ${this._formatMg(event.dose_mg)}`);
    window.alert(`Doses in last 48 hours:\n\n${lines.join("\n")}`);
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
  _titleCase(value) { return String(value).charAt(0).toUpperCase() + String(value).slice(1); }
  _doseSize(medicine) {
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
      },
    };
    const defaults = {
      paracetamol: "120mg/5ml liquid",
      ibuprofen: "5ml/100mg",
    };
    const configured = this.config[`${medicine}_dose_size`];
    const label = Object.prototype.hasOwnProperty.call(options[medicine], configured) ? configured : defaults[medicine];
    return { label, mg: options[medicine][label] };
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
customElements.define("child-dosage-card", ChildDosageCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "child-dosage-card", name: "Child Dosage Card", description: "Track child medication doses." });
