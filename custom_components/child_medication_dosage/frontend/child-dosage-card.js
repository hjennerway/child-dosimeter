class ChildDosageCard extends HTMLElement {
  setConfig(config) {
    if (!config.child_id && !config.child_name) {
      throw new Error("child_id or child_name is required");
    }

    this.config = {
      title: "Medication dosage",
      ...config,
    };
    this._root = this.attachShadow({ mode: "open" });
    this._root.innerHTML = `
      <style>
        :host {
          display: block;
        }

        ha-card {
          overflow: hidden;
        }

        .content {
          padding: 16px;
          display: grid;
          gap: 16px;
        }

        .header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 12px;
        }

        .title {
          font-size: 20px;
          font-weight: 600;
          line-height: 1.2;
          color: var(--primary-text-color);
        }

        .child {
          margin-top: 4px;
          color: var(--secondary-text-color);
          font-size: 14px;
        }

        .actions {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
        }

        button {
          border: 0;
          border-radius: 8px;
          min-height: 44px;
          padding: 10px 12px;
          font: inherit;
          font-weight: 600;
          color: var(--text-primary-color, #fff);
          background: var(--primary-color);
          cursor: pointer;
        }

        button.ibuprofen {
          background: var(--accent-color);
        }

        button:disabled {
          opacity: 0.45;
          cursor: not-allowed;
        }

        .medicine-list {
          display: grid;
          gap: 14px;
        }

        .medicine {
          display: grid;
          gap: 8px;
        }

        .medicine-top,
        .medicine-meta {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          gap: 12px;
        }

        .name {
          font-weight: 600;
          color: var(--primary-text-color);
          text-transform: capitalize;
        }

        .dose {
          color: var(--secondary-text-color);
          font-size: 13px;
          white-space: nowrap;
        }

        .bar {
          position: relative;
          height: 14px;
          border-radius: 7px;
          overflow: hidden;
          background: var(--divider-color);
        }

        .fill {
          position: absolute;
          inset: 0 auto 0 0;
          width: var(--fill-width);
          border-radius: inherit;
          background: var(--ok-color, #2e7d32);
        }

        .fill.warn {
          background: var(--warning-color, #f9a825);
        }

        .fill.danger {
          background: var(--error-color, #d32f2f);
        }

        .medicine-meta {
          color: var(--secondary-text-color);
          font-size: 12px;
        }

        .last {
          overflow-wrap: anywhere;
          text-align: right;
        }

        .missing {
          padding: 16px;
          color: var(--error-color);
        }

        @media (max-width: 420px) {
          .actions,
          .medicine-top,
          .medicine-meta {
            grid-template-columns: 1fr;
          }

          .actions {
            display: grid;
          }

          .medicine-top,
          .medicine-meta {
            display: grid;
            gap: 4px;
          }

          .last {
            text-align: left;
          }
        }
      </style>
      <ha-card>
        <div class="content"></div>
      </ha-card>
    `;
    this._content = this._root.querySelector(".content");
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._content) {
      return;
    }
    this._render();
  }

  getCardSize() {
    return 4;
  }

  _findStates() {
    const childId = this.config.child_id;
    const childName = this.config.child_name;
    const states = Object.entries(this._hass.states)
      .map(([entityId, state]) => ({ entityId, state }))
      .filter(
        ({ state }) =>
          (state.attributes.child_id === childId ||
            state.attributes.child_name === childName) &&
          ["paracetamol", "ibuprofen"].includes(state.attributes.medicine)
      );

    const byMedicine = Object.fromEntries(
      states.map((item) => [item.state.attributes.medicine, item])
    );
    return {
      paracetamol: byMedicine.paracetamol,
      ibuprofen: byMedicine.ibuprofen,
    };
  }

  _render() {
    const states = this._findStates();
    const childName =
      states.paracetamol?.state.attributes.child_name ||
      states.ibuprofen?.state.attributes.child_name ||
      this.config.child_id;

    this._content.innerHTML = `
      <div class="header">
        <div>
          <div class="title">${this._escape(this.config.title)}</div>
          <div class="child">${this._escape(childName)}</div>
        </div>
      </div>
      <div class="actions">
        <button class="paracetamol" data-medicine="paracetamol">Given Paracetamol</button>
        <button class="ibuprofen" data-medicine="ibuprofen">Given Ibuprofen</button>
      </div>
      <div class="medicine-list">
        ${this._medicineTemplate("paracetamol", states.paracetamol)}
        ${this._medicineTemplate("ibuprofen", states.ibuprofen)}
      </div>
    `;

    this._content.querySelectorAll("button[data-medicine]").forEach((button) => {
      button.addEventListener("click", () =>
        this._giveDose(button.dataset.medicine, button)
      );
    });
  }

  _medicineTemplate(medicine, item) {
    if (!item) {
      return `
        <div class="medicine">
          <div class="medicine-top">
            <span class="name">${medicine}</span>
            <span class="dose">sensor not found</span>
          </div>
          <div class="bar"><div class="fill danger" style="--fill-width: 0%"></div></div>
          <div class="medicine-meta">
            <span>Add or reload the integration entity</span>
            <span class="last"></span>
          </div>
        </div>
      `;
    }

    const attr = item.state.attributes;
    const total = Number(attr.total_24h_mg || 0);
    const max = Number(attr.max_24h_mg || 0);
    const percent = max > 0 ? Math.min(100, Math.round((total / max) * 100)) : 0;
    const fillClass = percent >= 100 ? "danger" : percent >= 75 ? "warn" : "";
    const doseCount = `${attr.doses_24h || 0}/${attr.max_doses_24h || 0} doses`;
    const doseText = `${this._formatMg(total)} / ${this._formatMg(max)} in 24h`;
    const last = attr.last_dose_at
      ? this._formatDateTime(attr.last_dose_at)
      : "No doses recorded";
    const recommended = attr.recommended_dose_mg
      ? `Next dose ${this._formatMg(attr.recommended_dose_mg)}`
      : "Dose not available";

    return `
      <div class="medicine">
        <div class="medicine-top">
          <span class="name">${medicine}</span>
          <span class="dose">${doseText}</span>
        </div>
        <div class="bar" title="${percent}% used">
          <div class="fill ${fillClass}" style="--fill-width: ${percent}%"></div>
        </div>
        <div class="medicine-meta">
          <span>${doseCount} &bull; ${recommended}</span>
          <span class="last">Last: ${last}</span>
        </div>
      </div>
    `;
  }

  async _giveDose(medicine, button) {
    const states = this._findStates();
    const childId =
      this.config.child_id ||
      states.paracetamol?.state.attributes.child_id ||
      states.ibuprofen?.state.attributes.child_id;
    if (!childId) {
      return;
    }

    button.disabled = true;
    try {
      await this._hass.callService("child_medication_dosage", "give_dose", {
        child_id: childId,
        medicine,
      });
    } finally {
      button.disabled = false;
    }
  }

  _formatMg(value) {
    if (!Number.isFinite(Number(value))) {
      return "0 mg";
    }
    return `${Number(value).toLocaleString(undefined, {
      maximumFractionDigits: 1,
    })} mg`;
  }

  _formatDateTime(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }

  _escape(value) {
    return String(value).replace(/[&<>"']/g, (char) => {
      const replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      };
      return replacements[char];
    });
  }
}

customElements.define("child-dosage-card", ChildDosageCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "child-dosage-card",
  name: "Child Dosage Card",
  description: "Track paracetamol and ibuprofen doses for a configured child.",
});
