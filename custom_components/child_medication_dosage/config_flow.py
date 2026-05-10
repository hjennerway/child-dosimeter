"""Config flow for Child Medication Dosage."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import uuid4

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    ATTR_CHILD_ID,
    CONF_CHILDREN,
    CONF_CHILD_NAME,
    CONF_CUSTOM_MEDICATIONS,
    CONF_DATE_OF_BIRTH,
    CONF_DOSE_MG,
    CONF_MAX_24H_MG,
    CONF_MAX_DOSES_24H,
    CONF_MEDICINE_NAME,
    CONF_WEIGHT_KG,
    DOMAIN,
    MEDICINE_IBUPROFEN,
    MEDICINE_PARACETAMOL,
)


def _child_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the child form schema."""

    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_CHILD_NAME, default=defaults.get(CONF_CHILD_NAME, "")
            ): selector.TextSelector(),
            vol.Required(
                CONF_DATE_OF_BIRTH,
                default=defaults.get(CONF_DATE_OF_BIRTH, date.today().isoformat()),
            ): selector.DateSelector(),
            vol.Required(
                CONF_WEIGHT_KG, default=defaults.get(CONF_WEIGHT_KG, 10.0)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.1,
                    max=120,
                    mode=selector.NumberSelectorMode.BOX,
                    step=0.1,
                )
            ),
            vol.Optional(
                CONF_CUSTOM_MEDICATIONS,
                default=_custom_medications_text(
                    defaults.get(CONF_CUSTOM_MEDICATIONS, [])
                ),
            ): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
        }
    )


def _date_string(value: Any) -> str:
    """Return an ISO date string from selector input."""

    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(str(value)).isoformat()


def _custom_medications_text(custom_medications: Any) -> str:
    """Serialize custom medication config for the options form."""

    if isinstance(custom_medications, str):
        return custom_medications
    return "\n".join(
        (
            f"{medication[CONF_MEDICINE_NAME]}, "
            f"{medication[CONF_MAX_DOSES_24H]}, "
            f"{medication[CONF_MAX_24H_MG]}, "
            f"{medication[CONF_DOSE_MG]}"
        )
        for medication in custom_medications
    )


def _parse_custom_medications(value: Any) -> list[dict[str, Any]]:
    """Parse one custom medication per line from the config form."""

    medications: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in str(value or "").splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 4:
            raise vol.Invalid("invalid_custom_medications")
        name, max_doses, max_24h_mg, dose_mg = parts
        key = name.casefold()
        if (
            not name
            or key in seen
            or key in (MEDICINE_PARACETAMOL, MEDICINE_IBUPROFEN)
        ):
            raise vol.Invalid("invalid_custom_medications")
        seen.add(key)
        max_doses_value = int(max_doses)
        max_24h_value = float(max_24h_mg)
        dose_value = float(dose_mg)
        if max_doses_value < 1 or max_24h_value <= 0 or dose_value <= 0:
            raise vol.Invalid("invalid_custom_medications")
        medications.append(
            {
                CONF_MEDICINE_NAME: name,
                CONF_MAX_DOSES_24H: max_doses_value,
                CONF_MAX_24H_MG: max_24h_value,
                CONF_DOSE_MG: dose_value,
            }
        )
    return medications


class ChildMedicationDosageConfigFlow(
    config_entries.ConfigFlow, domain=DOMAIN
):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_CHILD_NAME].strip()
            if not name:
                errors[CONF_CHILD_NAME] = "required"
            else:
                try:
                    child = {
                        ATTR_CHILD_ID: uuid4().hex,
                        CONF_CHILD_NAME: name,
                        CONF_DATE_OF_BIRTH: _date_string(user_input[CONF_DATE_OF_BIRTH]),
                        CONF_WEIGHT_KG: float(user_input[CONF_WEIGHT_KG]),
                        CONF_CUSTOM_MEDICATIONS: _parse_custom_medications(
                            user_input.get(CONF_CUSTOM_MEDICATIONS)
                        ),
                    }
                except (TypeError, ValueError, vol.Invalid):
                    errors[CONF_CUSTOM_MEDICATIONS] = "invalid_custom_medications"
                else:
                    return self.async_create_entry(
                        title=child[CONF_CHILD_NAME],
                        data={CONF_CHILDREN: [child]},
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=_child_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""

        return ChildMedicationDosageOptionsFlow(config_entry)


class ChildMedicationDosageOptionsFlow(config_entries.OptionsFlow):
    """Allow adding another child by updating the config entry data."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""

        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show the add-child form."""

        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_CHILD_NAME].strip()
            if not name:
                errors[CONF_CHILD_NAME] = "required"
            else:
                try:
                    child = {
                        ATTR_CHILD_ID: uuid4().hex,
                        CONF_CHILD_NAME: name,
                        CONF_DATE_OF_BIRTH: _date_string(user_input[CONF_DATE_OF_BIRTH]),
                        CONF_WEIGHT_KG: float(user_input[CONF_WEIGHT_KG]),
                        CONF_CUSTOM_MEDICATIONS: _parse_custom_medications(
                            user_input.get(CONF_CUSTOM_MEDICATIONS)
                        ),
                    }
                except (TypeError, ValueError, vol.Invalid):
                    errors[CONF_CUSTOM_MEDICATIONS] = "invalid_custom_medications"
                else:
                    children = list(self._config_entry.data.get(CONF_CHILDREN, []))
                    children.append(child)
                    self.hass.config_entries.async_update_entry(
                        self._config_entry,
                        data={**self._config_entry.data, CONF_CHILDREN: children},
                    )
                    return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=_child_schema(user_input),
            errors=errors,
        )
