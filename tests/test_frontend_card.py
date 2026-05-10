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


if __name__ == "__main__":
    unittest.main()
