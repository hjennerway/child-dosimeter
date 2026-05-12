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
weight_stale_warning = dosing.weight_stale_warning


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

    def test_paracetamol_under_three_months_has_consult_warning(self) -> None:
        """Paracetamol is blocked with a consult warning under 3 months."""

        rule = recommended_rule(
            "paracetamol",
            date(2026, 3, 1),
            5,
            datetime(2026, 5, 10, tzinfo=UTC),
        )

        self.assertEqual(rule.dose_mg, 0)
        self.assertEqual(rule.max_24h_mg, 0)
        self.assertEqual(
            rule.consult_warning,
            "Consult a doctor if child is less than 3 months old",
        )

    def test_ibuprofen_under_five_kg_has_consult_warning(self) -> None:
        """Ibuprofen is blocked with a consult warning under 5kg."""

        rule = recommended_rule(
            "ibuprofen",
            date(2025, 1, 1),
            4.9,
            datetime(2026, 5, 10, tzinfo=UTC),
        )

        self.assertEqual(rule.dose_mg, 0)
        self.assertEqual(rule.max_24h_mg, 0)
        self.assertEqual(
            rule.consult_warning,
            "Consult a doctor if child is less than 5kg",
        )

    def test_weight_stale_warning_after_three_months(self) -> None:
        """A weight update older than 3 months asks for a fresh weight."""

        warning = weight_stale_warning(
            date(2026, 2, 10),
            datetime(2026, 5, 10, tzinfo=UTC),
        )

        self.assertEqual(
            warning,
            "Update child's weight before giving medicine; weight has not been updated in 3 months",
        )

    def test_weight_stale_warning_not_shown_before_three_months(self) -> None:
        """Recent weight updates do not trigger the warning."""

        warning = weight_stale_warning(
            date(2026, 2, 11),
            datetime(2026, 5, 10, tzinfo=UTC),
        )

        self.assertIsNone(warning)

    def test_weight_stale_warning_when_update_date_missing(self) -> None:
        """Missing weight update dates are treated as stale for existing entries."""

        warning = weight_stale_warning(
            None,
            datetime(2026, 5, 10, tzinfo=UTC),
        )

        self.assertEqual(
            warning,
            "Update child's weight before giving medicine; weight has not been updated in 3 months",
        )


if __name__ == "__main__":
    unittest.main()
