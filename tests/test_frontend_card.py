"""Regression tests for the bundled Lovelace card."""

from __future__ import annotations

import shutil
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CARD_PATH = ROOT / "custom_components" / "child_medication_dosage" / "frontend" / "child-dosage-card.js"


class FrontendCardTests(unittest.TestCase):
    """Medication card frontend behavior."""

    @unittest.skipUnless(shutil.which("node"), "node is required for frontend tests")
    def test_ibuprofen_15ml_300mg_maps_to_300mg(self) -> None:
        """The editor option for older children records 300 mg, not the fallback."""

        script = textwrap.dedent(
            f"""
            const registry = {{}};
            global.HTMLElement = class {{
              attachShadow() {{
                return {{
                  innerHTML: "",
                  querySelector() {{ return {{}}; }},
                  querySelectorAll() {{ return []; }},
                }};
              }}
            }};
            global.customElements = {{
              define: (name, cls) => {{ registry[name] = cls; }},
            }};
            global.window = {{ customCards: [] }};
            require({str(CARD_PATH)!r});

            const card = new registry["child-dosage-card"]();
            card.setConfig({{
              child_id: "child",
              ibuprofen_dose_size: "15ml/300mg",
            }});

            const dose = card._doseSize("ibuprofen", {{}});
            if (dose.label !== "15ml/300mg" || dose.mg !== 300) {{
              throw new Error(`Expected 15ml/300mg to map to 300mg, got ${{JSON.stringify(dose)}}`);
            }}
            """
        )

        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)

    @unittest.skipUnless(shutil.which("node"), "node is required for frontend tests")
    def test_dose_interval_confirmation_prompts_immediately_after_dose(self) -> None:
        """The repeat-dose prompt appears even when the last dose was just recorded."""

        script = textwrap.dedent(
            f"""
            const registry = {{}};
            global.HTMLElement = class {{
              attachShadow() {{
                return {{
                  innerHTML: "",
                  querySelector() {{ return {{}}; }},
                  querySelectorAll() {{ return []; }},
                }};
              }}
            }};
            global.customElements = {{
              define: (name, cls) => {{ registry[name] = cls; }},
            }};
            let confirmMessage = null;
            global.window = {{
              customCards: [],
              confirm: (message) => {{
                confirmMessage = message;
                return false;
              }},
            }};
            require({str(CARD_PATH)!r});

            const originalNow = Date.now;
            Date.now = () => new Date("2026-05-12T10:00:00Z").getTime();
            try {{
              const card = new registry["child-dosage-card"]();
              card.setConfig({{ child_id: "child" }});
              const allowed = card._doseIntervalConfirmation("2026-05-12T10:00:00Z");

              if (allowed !== false) {{
                throw new Error("Expected confirmation result to block the dose when confirm returns false");
              }}
              if (!confirmMessage || !confirmMessage.includes("Confirm another dose?")) {{
                throw new Error(`Expected immediate repeat-dose confirmation, got ${{confirmMessage}}`);
              }}
            }} finally {{
              Date.now = originalNow;
            }}
            """
        )

        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)

    @unittest.skipUnless(shutil.which("node"), "node is required for frontend tests")
    def test_dose_button_carries_last_dose_timestamp(self) -> None:
        """The click handler can evaluate the interval without waiting for a rerender."""

        script = textwrap.dedent(
            f"""
            const registry = {{}};
            global.HTMLElement = class {{
              attachShadow() {{
                return {{
                  innerHTML: "",
                  querySelector() {{ return {{}}; }},
                  querySelectorAll() {{ return []; }},
                }};
              }}
            }};
            global.customElements = {{
              define: (name, cls) => {{ registry[name] = cls; }},
            }};
            global.window = {{ customCards: [] }};
            require({str(CARD_PATH)!r});

            const card = new registry["child-dosage-card"]();
            card.setConfig({{ child_id: "child" }});
            const html = card._medicineTemplate("paracetamol", {{
              state: {{
                attributes: {{
                  medicine: "paracetamol",
                  last_dose_at: "2026-05-12T10:00:00Z",
                }},
              }},
            }});

            if (!html.includes('data-last-dose-at="2026-05-12T10:00:00Z"')) {{
              throw new Error(`Expected dose button to include last dose timestamp, got ${{html}}`);
            }}
            """
        )

        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)

    @unittest.skipUnless(shutil.which("node"), "node is required for frontend tests")
    def test_give_dose_calls_service_when_interval_is_safe(self) -> None:
        """A safe dose interval should not be blocked by the confirmation helper."""

        script = textwrap.dedent(
            f"""
            const registry = {{}};
            global.HTMLElement = class {{
              attachShadow() {{
                return {{
                  innerHTML: "",
                  querySelector() {{ return {{}}; }},
                  querySelectorAll() {{ return []; }},
                }};
              }}
            }};
            global.customElements = {{
              define: (name, cls) => {{ registry[name] = cls; }},
            }};
            global.window = {{ customCards: [] }};
            require({str(CARD_PATH)!r});

            (async () => {{
              const originalNow = Date.now;
              Date.now = () => new Date("2026-05-12T10:00:00Z").getTime();
              try {{
              const card = new registry["child-dosage-card"]();
              card.setConfig({{ child_id: "child" }});
              let call = null;
              card._hass = {{
                callService: async (domain, service, data) => {{
                  call = {{ domain, service, data }};
                }},
              }};
              const button = {{
                dataset: {{
                  doseMg: "120",
                  lastDoseAt: "2026-05-12T05:00:00Z",
                }},
                disabled: false,
              }};

              await card._giveDose("paracetamol", button);

              if (!call || call.domain !== "child_medication_dosage" || call.service !== "give_dose") {{
                throw new Error(`Expected give_dose service call, got ${{JSON.stringify(call)}}`);
              }}
              if (button.disabled) {{
                throw new Error("Expected button to be re-enabled after dose service call");
              }}
              }} finally {{
                Date.now = originalNow;
              }}
            }})();
            """
        )

        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
