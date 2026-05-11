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
    def test_recent_dose_requires_confirmation(self) -> None:
        """Recording inside the 4-hour interval asks for confirmation."""

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
              Date.now = () => new Date("2026-05-11T12:00:00Z").getTime();

              const card = new registry["child-dosage-card"]();
              card.setConfig({{ child_id: "child" }});

              let serviceCalls = 0;
              let prompt = "";
              card._hass = {{
                states: {{}},
                callService() {{ serviceCalls += 1; }},
              }};
              window.confirm = (message) => {{
                prompt = message;
                return false;
              }};

              await card._giveDose("paracetamol", {{
                dataset: {{
                  doseMg: "120",
                  lastDoseAt: "2026-05-11T08:45:00Z",
                }},
                disabled: false,
              }});

              const expected = "Last dose was given 3 hours and 15 minutes ago. Recommendation is 4-6 hours between doses. Confirm another dose?";
              if (prompt !== expected) {{
                throw new Error(`Unexpected prompt: ${{prompt}}`);
              }}
              if (serviceCalls !== 0) {{
                throw new Error("Dose was recorded after confirmation was cancelled.");
              }}

              Date.now = originalNow;
            }})();
            """
        )

        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)

    @unittest.skipUnless(shutil.which("node"), "node is required for frontend tests")
    def test_four_hour_old_dose_does_not_require_confirmation(self) -> None:
        """Recording at or after 4 hours does not ask for confirmation."""

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
              Date.now = () => new Date("2026-05-11T12:00:00Z").getTime();

              const card = new registry["child-dosage-card"]();
              card.setConfig({{ child_id: "child" }});

              let serviceCalls = 0;
              let prompted = false;
              card._hass = {{
                states: {{}},
                callService() {{ serviceCalls += 1; }},
              }};
              window.confirm = () => {{
                prompted = true;
                return false;
              }};

              await card._giveDose("paracetamol", {{
                dataset: {{
                  doseMg: "120",
                  lastDoseAt: "2026-05-11T08:00:00Z",
                }},
                disabled: false,
              }});

              if (prompted) {{
                throw new Error("Dose prompted after the 4-hour interval.");
              }}
              if (serviceCalls !== 1) {{
                throw new Error(`Expected one service call, got ${{serviceCalls}}.`);
              }}

              Date.now = originalNow;
            }})();
            """
        )

        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
