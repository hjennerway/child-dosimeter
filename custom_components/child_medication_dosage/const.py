"""Constants for the Child Medication Dosage integration."""

from __future__ import annotations

DOMAIN = "child_medication_dosage"
PLATFORMS = ["sensor"]

CONF_CHILDREN = "children"
CONF_CHILD_ID = "child_id"
CONF_CHILD_NAME = "child_name"
CONF_DATE_OF_BIRTH = "date_of_birth"
CONF_WEIGHT_KG = "weight_kg"

MEDICINE_PARACETAMOL = "paracetamol"
MEDICINE_IBUPROFEN = "ibuprofen"
MEDICINES = (MEDICINE_PARACETAMOL, MEDICINE_IBUPROFEN)

ATTR_CHILD_ID = "child_id"
ATTR_CHILD_NAME = "child_name"
ATTR_MEDICINE = "medicine"
ATTR_DOSE_MG = "dose_mg"
ATTR_GIVEN_AT = "given_at"
ATTR_LAST_DOSE_AT = "last_dose_at"
ATTR_TOTAL_24H_MG = "total_24h_mg"
ATTR_MAX_24H_MG = "max_24h_mg"
ATTR_RECOMMENDED_DOSE_MG = "recommended_dose_mg"
ATTR_DOSES_24H = "doses_24h"
ATTR_MAX_DOSES_24H = "max_doses_24h"
ATTR_PERCENT_USED = "percent_used"

SERVICE_GIVE_DOSE = "give_dose"
SERVICE_CLEAR_HISTORY = "clear_history"

STORAGE_KEY = f"{DOMAIN}.history"
STORAGE_VERSION = 1
