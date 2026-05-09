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
        .meta { color: var(--secondary-text-color); font-size: 12px; display: grid; gap: 4px; }
        .actions { display: grid; gap: 8px; justify-items: stretch; align-content: center; }
        button { border: 0; border-radius: 8px; min-height: 36px; padding: 8px 10px; font: inherit; font-weight: 600; color: #fff; background: var(--primary-color); }
        button.dose { width: 88px; height: 88px; padding: 8px; }
        button.reset { min-height: 32px; padding: 6px 8px; font-size: 12px; background: var(--error-color, #d32f2f); }
        .bar { position: relative; height: 12px; border-radius: 6px; overflow: hidden; background: var(--divider-color); }
        .fill { position: absolute; inset: 0 auto 0 0; width: var(--fill-width); background: var(--ok-color, #2e7d32); }
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
  }

  _medicineTemplate(medicine, item) {
    const label = this._titleCase(medicine);
    if (!item) return `<div class="row"><div class="details"><div class="top"><b>${label}</b><span>sensor not found</span></div></div></div>`;
    const a = item.state.attributes;
    const total = Number(a.total_24h_mg || 0);
    const max = Number(a.max_24h_mg || 0);
    const percent = max > 0 ? Math.min(100, Math.round((total / max) * 100)) : 0;
    const last = a.last_dose_at ? this._formatDateTime(a.last_dose_at) : "No doses recorded";
    return `
      <div class="row">
        <div class="details">
          <div class="top"><b>${label}</b><span>${a.doses_24h || 0}/${a.max_doses_24h || 0} doses</span></div>
          <div class="bar"><div class="fill" style="--fill-width:${percent}%"></div></div>
          <div class="meta">
            ${this.config.show_amount_in_last24h ? `<span>Amount 24h: ${this._formatMg(total)} / ${this._formatMg(max)}</span>` : ""}
            ${this.config.show_last_dose_time ? `<span>Last dose: ${last}</span>` : ""}
            ${this.config.show_time_since_last_dose ? `<span>Since last: ${this._timeSince(a.last_dose_at)}</span>` : ""}
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
    button.disabled = true;
    try { await this._hass.callService("child_medication_dosage", "give_dose", { child_id: childId, medicine }); }
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
  _formatMg(value) { return `${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} mg`; }
  _formatDateTime(value) { const d = new Date(value); return Number.isNaN(d.getTime()) ? value : d.toLocaleString(); }
  _escape(value) { return String(value).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
}
customElements.define("child-dosage-card", ChildDosageCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "child-dosage-card", name: "Child Dosage Card", description: "Track child medication doses." });
