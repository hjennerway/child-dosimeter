"""Unit tests for medication dosing rules."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from datetime import UTC, date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "custom_components.child_medication_dosage"
PACKAGE_PATH = ROOT / "custom_components" / "child_medication_dosage"


def load_dosing_module():
    """Load dosing.py without importing the Home Assistant integration."""

    sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    package = types.ModuleType(PACKAGE_NAME)
    package.__path__ = [str(PACKAGE_PATH)]
    sys.modules[PACKAGE_NAME] = package

    for module_name in ("const", "dosing"):
        full_name = f"{PACKAGE_NAME}.{module_name}"
        spec = importlib.util.spec_from_file_location(
            full_name, PACKAGE_PATH / f"{module_name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = module
        spec.loader.exec_module(module)

    return sys.modules[f"{PACKAGE_NAME}.dosing"]


dosing = load_dosing_module()
recommended_rule = dosing.recommended_rule


class DosingTests(unittest.TestCase):
    """Medication dosing behavior."""

    def test_recommended_rule_returns_custom_medication_values(self) -> None:
        """Custom medication definitions provide fixed dosing rules."""

        rule = recommended_rule(
            "Antibiotic",
            date(2020, 1, 1),
            20,
            datetime(2026, 5, 10, tzinfo=UTC),
            [
                {
                    "name": "Antibiotic",
                    "max_doses_24h": 3,
                    "max_24h_mg": 300,
                    "dose_mg": 100,
                }
            ],
        )

        self.assertEqual(rule.medicine, "Antibiotic")
        self.assertEqual(rule.dose_mg, 100)
        self.assertEqual(rule.max_24h_mg, 300)
        self.assertEqual(rule.max_doses_24h, 3)
        self.assertEqual(rule.note, "custom medication")


if __name__ == "__main__":
    unittest.main()
