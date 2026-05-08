"""Config flow for Child Medication Dosage."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import uuid4

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_CHILD_ID,
    CONF_CHILDREN,
    CONF_CHILD_NAME,
    CONF_DATE_OF_BIRTH,
    CONF_WEIGHT_KG,
    DOMAIN,
)


def _child_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the child form schema."""

    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_CHILD_NAME, default=defaults.get(CONF_CHILD_NAME, "")
            ): cv.string,
            vol.Required(
                CONF_DATE_OF_BIRTH,
                default=defaults.get(CONF_DATE_OF_BIRTH, date.today().isoformat()),
            ): cv.date,
            vol.Required(
                CONF_WEIGHT_KG, default=defaults.get(CONF_WEIGHT_KG, 10.0)
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=120)),
        }
    )


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
            child = {
                ATTR_CHILD_ID: uuid4().hex,
                CONF_CHILD_NAME: user_input[CONF_CHILD_NAME].strip(),
                CONF_DATE_OF_BIRTH: user_input[CONF_DATE_OF_BIRTH].isoformat(),
                CONF_WEIGHT_KG: user_input[CONF_WEIGHT_KG],
            }
            if not child[CONF_CHILD_NAME]:
                errors[CONF_CHILD_NAME] = "required"
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
                child = {
                    ATTR_CHILD_ID: uuid4().hex,
                    CONF_CHILD_NAME: name,
                    CONF_DATE_OF_BIRTH: user_input[CONF_DATE_OF_BIRTH].isoformat(),
                    CONF_WEIGHT_KG: user_input[CONF_WEIGHT_KG],
                }
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
