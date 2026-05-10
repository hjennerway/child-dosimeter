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

FIELD_ADD_ANOTHER_CUSTOM_MEDICATION = "add_another_custom_medication"
FIELD_CONFIGURE_CUSTOM_MEDICATIONS = "configure_custom_medications"


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
                FIELD_CONFIGURE_CUSTOM_MEDICATIONS,
                default=defaults.get(FIELD_CONFIGURE_CUSTOM_MEDICATIONS, False),
            ): selector.BooleanSelector(),
        }
    )


def _custom_medication_schema(
    defaults: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return the custom medication form schema."""

    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_MEDICINE_NAME, default=defaults.get(CONF_MEDICINE_NAME, "")
            ): selector.TextSelector(),
            vol.Required(
                CONF_MAX_DOSES_24H, default=defaults.get(CONF_MAX_DOSES_24H, 4)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=24,
                    mode=selector.NumberSelectorMode.BOX,
                    step=1,
                )
            ),
            vol.Required(
                CONF_MAX_24H_MG, default=defaults.get(CONF_MAX_24H_MG, 0)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=5000,
                    mode=selector.NumberSelectorMode.BOX,
                    step=0.1,
                    unit_of_measurement="mg",
                )
            ),
            vol.Required(
                CONF_DOSE_MG, default=defaults.get(CONF_DOSE_MG, 0)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=5000,
                    mode=selector.NumberSelectorMode.BOX,
                    step=0.1,
                    unit_of_measurement="mg",
                )
            ),
            vol.Optional(
                FIELD_ADD_ANOTHER_CUSTOM_MEDICATION,
                default=defaults.get(FIELD_ADD_ANOTHER_CUSTOM_MEDICATION, False),
            ): selector.BooleanSelector(),
        }
    )


def _date_string(value: Any) -> str:
    """Return an ISO date string from selector input."""

    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(str(value)).isoformat()


def _child_from_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Build stored child data from form input."""

    return {
        ATTR_CHILD_ID: uuid4().hex,
        CONF_CHILD_NAME: user_input[CONF_CHILD_NAME].strip(),
        CONF_DATE_OF_BIRTH: _date_string(user_input[CONF_DATE_OF_BIRTH]),
        CONF_WEIGHT_KG: float(user_input[CONF_WEIGHT_KG]),
        CONF_CUSTOM_MEDICATIONS: [],
    }


def _custom_medication_from_input(
    user_input: dict[str, Any], existing: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build one stored custom medication from form input."""

    name = user_input[CONF_MEDICINE_NAME].strip()
    key = name.casefold()
    existing_names = {
        medication[CONF_MEDICINE_NAME].casefold() for medication in existing
    }
    if (
        not name
        or key in existing_names
        or key in (MEDICINE_PARACETAMOL, MEDICINE_IBUPROFEN)
    ):
        raise vol.Invalid("invalid_custom_medication")

    max_doses = int(user_input[CONF_MAX_DOSES_24H])
    max_24h_mg = float(user_input[CONF_MAX_24H_MG])
    dose_mg = float(user_input[CONF_DOSE_MG])
    if max_doses < 1 or max_24h_mg <= 0 or dose_mg <= 0:
        raise vol.Invalid("invalid_custom_medication")

    return {
        CONF_MEDICINE_NAME: name,
        CONF_MAX_DOSES_24H: max_doses,
        CONF_MAX_24H_MG: max_24h_mg,
        CONF_DOSE_MG: dose_mg,
    }


class ChildMedicationDosageConfigFlow(
    config_entries.ConfigFlow, domain=DOMAIN
):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow state."""

        self._custom_medications: list[dict[str, Any]] = []
        self._pending_child: dict[str, Any] | None = None

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
                self._pending_child = _child_from_input(user_input)
                self._custom_medications = []
                if user_input.get(FIELD_CONFIGURE_CUSTOM_MEDICATIONS):
                    return await self.async_step_custom_medication()
                return self._async_create_pending_child_entry()

        return self.async_show_form(
            step_id="user",
            data_schema=_child_schema(user_input),
            errors=errors,
        )

    async def async_step_custom_medication(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle one custom medication form."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._custom_medications.append(
                    _custom_medication_from_input(
                        user_input, self._custom_medications
                    )
                )
            except (TypeError, ValueError, vol.Invalid):
                errors["base"] = "invalid_custom_medication"
            else:
                if user_input.get(FIELD_ADD_ANOTHER_CUSTOM_MEDICATION):
                    return await self.async_step_custom_medication()
                return self._async_create_pending_child_entry()

        return self.async_show_form(
            step_id="custom_medication",
            data_schema=_custom_medication_schema(user_input),
            errors=errors,
        )

    def _async_create_pending_child_entry(self) -> config_entries.ConfigFlowResult:
        """Create the entry after any custom medications have been collected."""

        child = self._pending_child or {}
        child[CONF_CUSTOM_MEDICATIONS] = list(self._custom_medications)
        return self.async_create_entry(
            title=child[CONF_CHILD_NAME],
            data={CONF_CHILDREN: [child]},
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
        self._custom_medications: list[dict[str, Any]] = []
        self._pending_child: dict[str, Any] | None = None

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
                self._pending_child = _child_from_input(user_input)
                self._custom_medications = []
                if user_input.get(FIELD_CONFIGURE_CUSTOM_MEDICATIONS):
                    return await self.async_step_custom_medication()
                return self._async_update_entry_with_pending_child()

        return self.async_show_form(
            step_id="init",
            data_schema=_child_schema(user_input),
            errors=errors,
        )

    async def async_step_custom_medication(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle one custom medication form."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._custom_medications.append(
                    _custom_medication_from_input(
                        user_input, self._custom_medications
                    )
                )
            except (TypeError, ValueError, vol.Invalid):
                errors["base"] = "invalid_custom_medication"
            else:
                if user_input.get(FIELD_ADD_ANOTHER_CUSTOM_MEDICATION):
                    return await self.async_step_custom_medication()
                return self._async_update_entry_with_pending_child()

        return self.async_show_form(
            step_id="custom_medication",
            data_schema=_custom_medication_schema(user_input),
            errors=errors,
        )

    def _async_update_entry_with_pending_child(self) -> config_entries.ConfigFlowResult:
        """Add the pending child to the existing config entry."""

        child = self._pending_child or {}
        child[CONF_CUSTOM_MEDICATIONS] = list(self._custom_medications)
        children = list(self._config_entry.data.get(CONF_CHILDREN, []))
        children.append(child)
        self.hass.config_entries.async_update_entry(
            self._config_entry,
            data={**self._config_entry.data, CONF_CHILDREN: children},
        )
        return self.async_create_entry(title="", data={})
