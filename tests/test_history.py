"""Unit tests for medication history rolling-window behavior."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "custom_components.child_medication_dosage"
PACKAGE_PATH = ROOT / "custom_components" / "child_medication_dosage"


class FakeStore:
    """Small stand-in for Home Assistant's storage helper."""

    saved: list[dict] | None = None

    def __init__(self, *_args, **_kwargs) -> None:
        """Initialize the fake store."""

    async def async_load(self):
        """Return no persisted events."""

        return []

    async def async_save(self, data):
        """Capture persisted events for assertions."""

        self.saved = data


def load_history_module():
    """Load history.py without importing the full Home Assistant integration."""

    sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    package = types.ModuleType(PACKAGE_NAME)
    package.__path__ = [str(PACKAGE_PATH)]
    sys.modules[PACKAGE_NAME] = package

    homeassistant = types.ModuleType("homeassistant")
    core = types.ModuleType("homeassistant.core")
    helpers = types.ModuleType("homeassistant.helpers")
    storage = types.ModuleType("homeassistant.helpers.storage")
    core.HomeAssistant = object
    storage.Store = FakeStore
    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.storage"] = storage

    for module_name in ("const", "history"):
        full_name = f"{PACKAGE_NAME}.{module_name}"
        spec = importlib.util.spec_from_file_location(
            full_name, PACKAGE_PATH / f"{module_name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = module
        spec.loader.exec_module(module)

    return sys.modules[f"{PACKAGE_NAME}.history"]


history = load_history_module()
DoseEvent = history.DoseEvent
MedicationHistory = history.MedicationHistory


class MedicationHistoryTests(unittest.IsolatedAsyncioTestCase):
    """Medication history behavior."""

    def setUp(self) -> None:
        """Create a fresh history store."""

        self.now = datetime(2026, 5, 10, 12, 0, tzinfo=UTC)
        self.history = MedicationHistory(hass=object())
        self.history._events = [
            DoseEvent("child-1", "paracetamol", 120, self.now - timedelta(hours=2)),
            DoseEvent("child-1", "paracetamol", 120, self.now - timedelta(hours=24)),
            DoseEvent(
                "child-1",
                "paracetamol",
                120,
                self.now - timedelta(hours=24, seconds=1),
            ),
            DoseEvent("child-1", "ibuprofen", 100, self.now - timedelta(hours=1)),
            DoseEvent("child-2", "paracetamol", 120, self.now - timedelta(hours=1)),
        ]

    def test_events_for_excludes_doses_older_than_24_hours_from_total(self) -> None:
        """Only doses in the rolling 24h window are returned for totals."""

        events = self.history.events_for("child-1", "paracetamol", self.now)

        self.assertEqual(sum(event.dose_mg for event in events), 240)
        self.assertEqual(len(events), 2)
        self.assertNotIn(
            self.now - timedelta(hours=24, seconds=1),
            [event.given_at for event in events],
        )

    async def test_async_clear_only_removes_matching_data_from_last_24_hours(self) -> None:
        """Reset behavior keeps older history and unrelated child/medicine data."""

        await self.history.async_clear("child-1", "paracetamol", now=self.now)

        remaining = {
            (event.child_id, event.medicine, event.given_at)
            for event in self.history._events
        }
        self.assertEqual(
            remaining,
            {
                (
                    "child-1",
                    "paracetamol",
                    self.now - timedelta(hours=24, seconds=1),
                ),
                ("child-1", "ibuprofen", self.now - timedelta(hours=1)),
                ("child-2", "paracetamol", self.now - timedelta(hours=1)),
            },
        )

    async def test_async_remove_one_only_removes_exact_matching_dose(self) -> None:
        """Removing one dose leaves unrelated and non-matching events intact."""

        removed = await self.history.async_remove_one(
            "child-1", "paracetamol", self.now - timedelta(hours=2), 120
        )

        self.assertTrue(removed)
        remaining = [
            (event.child_id, event.medicine, event.dose_mg, event.given_at)
            for event in self.history._events
        ]
        self.assertNotIn(
            ("child-1", "paracetamol", 120, self.now - timedelta(hours=2)),
            remaining,
        )
        self.assertIn(
            ("child-1", "ibuprofen", 100, self.now - timedelta(hours=1)),
            remaining,
        )
        self.assertIn(
            ("child-2", "paracetamol", 120, self.now - timedelta(hours=1)),
            remaining,
        )

    async def test_async_remove_one_returns_false_when_no_dose_matches(self) -> None:
        """Missing removal requests do not rewrite history."""

        original = list(self.history._events)

        removed = await self.history.async_remove_one(
            "child-1", "paracetamol", self.now - timedelta(hours=2), 999
        )

        self.assertFalse(removed)
        self.assertEqual(self.history._events, original)

    async def test_async_add_merges_with_previous_dose_inside_two_minutes(self) -> None:
        """Quick repeat clicks increase amount without adding a dose count."""

        self.history._events = [DoseEvent("child-1", "paracetamol", 120, self.now)]

        event = await self.history.async_add(
            "child-1",
            "paracetamol",
            60,
            self.now + timedelta(minutes=1, seconds=59),
        )

        events = self.history.events_for(
            "child-1",
            "paracetamol",
            self.now + timedelta(minutes=2),
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(event.dose_mg, 180)
        self.assertEqual(events[0].dose_mg, 180)
        self.assertEqual(
            events[0].given_at,
            self.now + timedelta(minutes=1, seconds=59),
        )

    async def test_async_add_creates_new_dose_at_two_minutes(self) -> None:
        """The merge window is strictly less than two minutes."""

        self.history._events = [DoseEvent("child-1", "paracetamol", 120, self.now)]

        await self.history.async_add(
            "child-1",
            "paracetamol",
            60,
            self.now + timedelta(minutes=2),
        )

        events = self.history.events_for(
            "child-1",
            "paracetamol",
            self.now + timedelta(minutes=2),
        )
        self.assertEqual(len(events), 2)
        self.assertEqual(sum(event.dose_mg for event in events), 180)

    async def test_async_add_only_merges_same_child_and_medicine(self) -> None:
        """Quick doses for another child or medicine stay separate."""

        self.history._events = [DoseEvent("child-1", "paracetamol", 120, self.now)]

        await self.history.async_add(
            "child-1",
            "ibuprofen",
            60,
            self.now + timedelta(minutes=1),
        )
        await self.history.async_add(
            "child-2",
            "paracetamol",
            60,
            self.now + timedelta(minutes=1),
        )

        self.assertEqual(len(self.history._events), 3)


if __name__ == "__main__":
    unittest.main()
