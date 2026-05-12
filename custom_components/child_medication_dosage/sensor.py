"""Sensor platform for Child Medication Dosage."""

from __future__ import annotations

from datetime import UTC, datetime
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import (
    SIGNAL_HISTORY_UPDATED,
    child_medicine_names,
    children_from_entry,
    history_from_entry,
)
from .const import (
    ATTR_CHILD_ID,
    ATTR_CHILD_NAME,
    ATTR_DOSES_24H,
    ATTR_LAST_DOSE_AT,
    ATTR_MAX_24H_MG,
    ATTR_MAX_DOSES_24H,
    ATTR_MEDICINE,
    ATTR_PERCENT_USED,
    ATTR_RECOMMENDED_DOSE_MG,
    ATTR_TOTAL_24H_MG,
    CONF_CHILD_NAME,
    CONF_CUSTOM_MEDICATIONS,
    CONF_DATE_OF_BIRTH,
    CONF_WEIGHT_KG,
    CONF_WEIGHT_UPDATED_AT,
    DOMAIN,
)
from .dosing import recommended_rule, weight_stale_warning
from .history import MedicationHistory


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for every configured child and medicine."""

    history = history_from_entry(hass, entry.entry_id)
    entities: list[SensorEntity] = []
    for child in children_from_entry(entry):
        for medicine in child_medicine_names(child):
            entities.append(MedicationDoseSensor(entry.entry_id, child, medicine, history))
    async_add_entities(entities)


class MedicationDoseSensor(SensorEntity):
    """Rolling 24-hour medication dose sensor."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:medication"

    def __init__(
        self,
        entry_id: str,
        child: dict[str, Any],
        medicine: str,
        history: MedicationHistory,
    ) -> None:
        """Initialize the sensor."""

        self._entry_id = entry_id
        self._child = child
        self._medicine = medicine
        self._history = history
        self.entity_description = SensorEntityDescription(
            key=f"{child[ATTR_CHILD_ID]}_{medicine}",
            name=f"{child[CONF_CHILD_NAME]} {medicine.title()} 24h",
            native_unit_of_measurement="mg",
        )
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{child[ATTR_CHILD_ID]}_{medicine}"

    @property
    def native_value(self) -> float:
        """Return the administered amount in the last 24h."""

        return self._summary()[ATTR_TOTAL_24H_MG]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return useful details for the Lovelace card."""

        return self._summary()

    def _summary(self) -> dict[str, Any]:
        """Build the latest rolling 24-hour summary."""

        now = datetime.now(UTC)
        date_of_birth = self._child[CONF_DATE_OF_BIRTH]
        rule = recommended_rule(
            self._medicine,
            date_of_birth,
            self._child[CONF_WEIGHT_KG],
            now,
            self._child.get(CONF_CUSTOM_MEDICATIONS, []),
        )
        consult_warning = rule.consult_warning or weight_stale_warning(
            self._child.get(CONF_WEIGHT_UPDATED_AT),
            now,
        )
        events = self._history.events_for(self._child[ATTR_CHILD_ID], self._medicine, now)
        events_48h = self._history.events_for(
            self._child[ATTR_CHILD_ID],
            self._medicine,
            now,
            window=timedelta(hours=48),
        )
        last = self._history.last_event(self._child[ATTR_CHILD_ID], self._medicine)
        total = round(sum(event.dose_mg for event in events), 1)
        percent = 0 if rule.max_24h_mg <= 0 else min(100, round(total / rule.max_24h_mg * 100))
        return {
            ATTR_CHILD_ID: self._child[ATTR_CHILD_ID],
            ATTR_CHILD_NAME: self._child[CONF_CHILD_NAME],
            "date_of_birth": date_of_birth.isoformat(),
            ATTR_MEDICINE: self._medicine,
            ATTR_TOTAL_24H_MG: total,
            ATTR_MAX_24H_MG: rule.max_24h_mg,
            ATTR_RECOMMENDED_DOSE_MG: rule.dose_mg,
            ATTR_DOSES_24H: len(events),
            ATTR_MAX_DOSES_24H: rule.max_doses_24h,
            ATTR_PERCENT_USED: percent,
            ATTR_LAST_DOSE_AT: last.given_at.isoformat() if last else None,
            "dose_log_48h": [
                {"dose_mg": event.dose_mg, "given_at": event.given_at.isoformat()}
                for event in sorted(events_48h, key=lambda event: event.given_at, reverse=True)
            ],
            "rule_note": rule.note,
            "consult_warning": consult_warning,
            "weight_kg": self._child[CONF_WEIGHT_KG],
            CONF_WEIGHT_UPDATED_AT: self._child.get(CONF_WEIGHT_UPDATED_AT),
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to history updates."""

        @callback
        def _handle_history_updated(child_id: str | None, medicine: str | None) -> None:
            if child_id in (None, self._child[ATTR_CHILD_ID]) and medicine in (
                None,
                self._medicine,
            ):
                self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_HISTORY_UPDATED, _handle_history_updated
            )
        )
