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
    CONF_WEIGHT_UPDATED_AT,
    DOMAIN,
    MEDICINE_IBUPROFEN,
    MEDICINE_PARACETAMOL,
)

FIELD_ADD_ANOTHER_CUSTOM_MEDICATION = "add_another_custom_medication"
FIELD_CHILD_ACTION = "child_action"
FIELD_CONFIGURE_CUSTOM_MEDICATIONS = "configure_custom_medications"
VALUE_ADD_CHILD = "__add_child__"


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


def _child_action_schema(children: list[dict[str, Any]]) -> vol.Schema:
    """Return the options form schema for selecting a child to edit."""

    options = [
        {"value": child[ATTR_CHILD_ID], "label": child[CONF_CHILD_NAME]}
        for child in children
    ]
    options.append({"value": VALUE_ADD_CHILD, "label": "Add another child"})
    return vol.Schema(
        {
            vol.Required(FIELD_CHILD_ACTION): selector.SelectSelector(
                selector.SelectSelectorConfig(options=options)
            )
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
        CONF_WEIGHT_UPDATED_AT: date.today().isoformat(),
        CONF_CUSTOM_MEDICATIONS: [],
    }


def _child_defaults(child: dict[str, Any] | None) -> dict[str, Any]:
    """Return child form defaults from stored child data."""

    if not child:
        return {}
    return {
        CONF_CHILD_NAME: child.get(CONF_CHILD_NAME, ""),
        CONF_DATE_OF_BIRTH: _date_string(child.get(CONF_DATE_OF_BIRTH)),
        CONF_WEIGHT_KG: child.get(CONF_WEIGHT_KG, 10.0),
        FIELD_CONFIGURE_CUSTOM_MEDICATIONS: bool(
            child.get(CONF_CUSTOM_MEDICATIONS, [])
        ),
    }


def _child_from_input_with_id(
    user_input: dict[str, Any],
    child_id: str | None = None,
    existing_child: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build stored child data from form input, preserving an existing id."""

    child = _child_from_input(user_input)
    if child_id:
        child[ATTR_CHILD_ID] = child_id
    if (
        existing_child
        and float(existing_child.get(CONF_WEIGHT_KG, 0)) == child[CONF_WEIGHT_KG]
    ):
        child[CONF_WEIGHT_UPDATED_AT] = existing_child.get(
            CONF_WEIGHT_UPDATED_AT,
            child[CONF_WEIGHT_UPDATED_AT],
        )
    return child


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
    """Allow editing children by updating the config entry data."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""

        self._config_entry = config_entry
        self._custom_medications: list[dict[str, Any]] = []
        self._custom_medication_defaults: list[dict[str, Any]] = []
        self._custom_medication_index = 0
        self._editing_child_index: int | None = None
        self._pending_child: dict[str, Any] | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Select a child to edit or add a new child."""

        children = list(self._config_entry.data.get(CONF_CHILDREN, []))
        if not children:
            self._editing_child_index = None
            return await self.async_step_child()

        if user_input is not None:
            selected = user_input[FIELD_CHILD_ACTION]
            if selected == VALUE_ADD_CHILD:
                self._editing_child_index = None
                return await self.async_step_child()
            for index, child in enumerate(children):
                if child[ATTR_CHILD_ID] == selected:
                    self._editing_child_index = index
                    return await self.async_step_child()

        return self.async_show_form(
            step_id="init",
            data_schema=_child_action_schema(children),
            errors={},
        )

    async def async_step_child(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show the child edit form."""

        errors: dict[str, str] = {}
        existing_child = self._editing_child()
        if user_input is not None:
            name = user_input[CONF_CHILD_NAME].strip()
            if not name:
                errors[CONF_CHILD_NAME] = "required"
            else:
                self._pending_child = _child_from_input_with_id(
                    user_input,
                    existing_child.get(ATTR_CHILD_ID) if existing_child else None,
                    existing_child,
                )
                self._custom_medications = []
                self._custom_medication_defaults = list(
                    existing_child.get(CONF_CUSTOM_MEDICATIONS, [])
                    if existing_child
                    else []
                )
                self._custom_medication_index = 0
                if user_input.get(FIELD_CONFIGURE_CUSTOM_MEDICATIONS):
                    return await self.async_step_custom_medication()
                return self._async_update_entry_with_pending_child()

        return self.async_show_form(
            step_id="child",
            data_schema=_child_schema(user_input or _child_defaults(existing_child)),
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
                self._custom_medication_index += 1
                if self._custom_medication_index < len(
                    self._custom_medication_defaults
                ) or user_input.get(FIELD_ADD_ANOTHER_CUSTOM_MEDICATION):
                    return await self.async_step_custom_medication()
                return self._async_update_entry_with_pending_child()

        return self.async_show_form(
            step_id="custom_medication",
            data_schema=_custom_medication_schema(
                user_input or self._current_custom_medication_defaults()
            ),
            errors=errors,
        )

    def _async_update_entry_with_pending_child(self) -> config_entries.ConfigFlowResult:
        """Add or replace the pending child in the existing config entry."""

        child = self._pending_child or {}
        child[CONF_CUSTOM_MEDICATIONS] = list(self._custom_medications)
        children = list(self._config_entry.data.get(CONF_CHILDREN, []))
        if self._editing_child_index is None:
            children.append(child)
        else:
            children[self._editing_child_index] = child
        self.hass.config_entries.async_update_entry(
            self._config_entry,
            data={**self._config_entry.data, CONF_CHILDREN: children},
        )
        return self.async_create_entry(title="", data={})

    def _editing_child(self) -> dict[str, Any] | None:
        """Return the selected child being edited."""

        if self._editing_child_index is None:
            return None
        children = list(self._config_entry.data.get(CONF_CHILDREN, []))
        if self._editing_child_index >= len(children):
            return None
        return children[self._editing_child_index]

    def _current_custom_medication_defaults(self) -> dict[str, Any]:
        """Return defaults for the custom medication currently being edited."""

        if self._custom_medication_index >= len(self._custom_medication_defaults):
            return {}
        return self._custom_medication_defaults[self._custom_medication_index]
