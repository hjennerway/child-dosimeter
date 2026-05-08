"""Child Medication Dosage integration."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    ATTR_CHILD_ID,
    ATTR_DOSE_MG,
    ATTR_MEDICINE,
    CONF_CHILDREN,
    DOMAIN,
    MEDICINES,
    PLATFORMS,
    SERVICE_CLEAR_HISTORY,
    SERVICE_GIVE_DOSE,
)
from .dosing import recommended_rule
from .history import MedicationHistory

SIGNAL_HISTORY_UPDATED = f"{DOMAIN}_history_updated"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up Child Medication Dosage from a config entry."""

    history = MedicationHistory(hass)
    await history.async_load()

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = {"entry": entry, "history": history}

    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform(platform) for platform in PLATFORMS]
    )
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _async_register_services(hass)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ChildMedicationConfigEntry
) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform(platform) for platform in PLATFORMS]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant, entry: ChildMedicationConfigEntry
) -> None:
    """Reload the integration after options update."""

    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def children_from_entry(entry: ConfigEntry) -> list[dict[str, Any]]:
    """Return children configured on an entry."""

    children: list[dict[str, Any]] = []
    for child in entry.data.get(CONF_CHILDREN, []):
        parsed = dict(child)
        dob = parsed.get("date_of_birth")
        if isinstance(dob, str):
            parsed["date_of_birth"] = date.fromisoformat(dob)
        children.append(parsed)
    return children


def history_from_entry(hass: HomeAssistant, entry_id: str) -> MedicationHistory:
    """Return the medication history store for an entry."""

    return hass.data[DOMAIN][entry_id]["history"]


def find_child(hass: HomeAssistant, child_id: str) -> tuple[ConfigEntry, dict[str, Any]]:
    """Find a child across loaded entries."""

    for entry_data in hass.data.get(DOMAIN, {}).values():
        entry = entry_data["entry"]
        for child in children_from_entry(entry):
            if child[ATTR_CHILD_ID] == child_id:
                return entry, child
    raise vol.Invalid(f"Unknown child_id: {child_id}")


@callback
def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services once."""

    if hass.services.has_service(DOMAIN, SERVICE_GIVE_DOSE):
        return

    async def async_give_dose(call: ServiceCall) -> None:
        """Record a medication dose."""

        child_id = call.data[ATTR_CHILD_ID]
        medicine = call.data[ATTR_MEDICINE]
        entry, child = find_child(hass, child_id)
        history = history_from_entry(hass, entry.entry_id)
        dose_mg = call.data.get(ATTR_DOSE_MG)
        if dose_mg is None:
            rule = recommended_rule(
                medicine,
                child["date_of_birth"],
                child["weight_kg"],
                datetime.now(UTC),
            )
            dose_mg = rule.dose_mg
        await history.async_add(child_id, medicine, float(dose_mg), datetime.now(UTC))
        async_dispatcher_send(hass, SIGNAL_HISTORY_UPDATED, child_id, medicine)

    async def async_clear_history(call: ServiceCall) -> None:
        """Clear medication history."""

        child_id = call.data.get(ATTR_CHILD_ID)
        entries = hass.data.get(DOMAIN, {}).values()
        for entry_data in entries:
            await entry_data["history"].async_clear(child_id)
        async_dispatcher_send(hass, SIGNAL_HISTORY_UPDATED, child_id, None)

    hass.services.async_register(
        DOMAIN,
        SERVICE_GIVE_DOSE,
        async_give_dose,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CHILD_ID): cv.string,
                vol.Required(ATTR_MEDICINE): vol.In(MEDICINES),
                vol.Optional(ATTR_DOSE_MG): vol.Coerce(float),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_HISTORY,
        async_clear_history,
        schema=vol.Schema({vol.Optional(ATTR_CHILD_ID): cv.string}),
    )
