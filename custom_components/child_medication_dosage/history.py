"""Persistent medication administration history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import ATTR_DOSE_MG, ATTR_GIVEN_AT, ATTR_MEDICINE, STORAGE_KEY, STORAGE_VERSION


@dataclass(frozen=True)
class DoseEvent:
    """A recorded dose event."""

    child_id: str
    medicine: str
    dose_mg: float
    given_at: datetime

    def as_dict(self) -> dict[str, Any]:
        """Serialize a dose event."""

        return {
            "child_id": self.child_id,
            ATTR_MEDICINE: self.medicine,
            ATTR_DOSE_MG: self.dose_mg,
            ATTR_GIVEN_AT: self.given_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DoseEvent":
        """Deserialize a dose event."""

        given_at = datetime.fromisoformat(data[ATTR_GIVEN_AT])
        if given_at.tzinfo is None:
            given_at = given_at.replace(tzinfo=UTC)
        return cls(
            child_id=str(data["child_id"]),
            medicine=str(data[ATTR_MEDICINE]),
            dose_mg=float(data[ATTR_DOSE_MG]),
            given_at=given_at,
        )


class MedicationHistory:
    """Store and query medication history."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the history store."""

        self._store: Store[list[dict[str, Any]]] = Store(
            hass, STORAGE_VERSION, STORAGE_KEY
        )
        self._events: list[DoseEvent] = []

    async def async_load(self) -> None:
        """Load persisted dose history."""

        stored = await self._store.async_load() or []
        self._events = [DoseEvent.from_dict(event) for event in stored]

    async def async_add(
        self, child_id: str, medicine: str, dose_mg: float, given_at: datetime
    ) -> DoseEvent:
        """Add and persist a dose event."""

        if given_at.tzinfo is None:
            given_at = given_at.replace(tzinfo=UTC)
        event = DoseEvent(child_id, medicine, dose_mg, given_at)
        self._events.append(event)
        await self._async_prune_and_save()
        return event

    async def async_clear(self, child_id: str | None = None) -> None:
        """Clear all history, optionally for one child."""

        if child_id is None:
            self._events = []
        else:
            self._events = [event for event in self._events if event.child_id != child_id]
        await self._async_save()

    def events_for(
        self,
        child_id: str,
        medicine: str,
        now: datetime,
        window: timedelta = timedelta(hours=24),
    ) -> list[DoseEvent]:
        """Return dose events in the rolling window."""

        cutoff = now - window
        return [
            event
            for event in self._events
            if event.child_id == child_id
            and event.medicine == medicine
            and event.given_at >= cutoff
        ]

    def last_event(self, child_id: str, medicine: str) -> DoseEvent | None:
        """Return the latest event for a child and medicine."""

        matching = [
            event
            for event in self._events
            if event.child_id == child_id and event.medicine == medicine
        ]
        return max(matching, key=lambda event: event.given_at, default=None)

    async def _async_prune_and_save(self) -> None:
        """Keep recent history plus one older last-dose marker per medicine."""

        now = datetime.now(UTC)
        cutoff = now - timedelta(days=14)
        self._events = [event for event in self._events if event.given_at >= cutoff]
        await self._async_save()

    async def _async_save(self) -> None:
        """Persist events."""

        await self._store.async_save([event.as_dict() for event in self._events])
