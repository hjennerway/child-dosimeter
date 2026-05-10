"""Dose recommendation helpers for paediatric paracetamol and ibuprofen."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from math import floor

from .const import MEDICINE_IBUPROFEN, MEDICINE_PARACETAMOL
from .const import (
    CONF_DOSE_MG,
    CONF_MAX_24H_MG,
    CONF_MAX_DOSES_24H,
    CONF_MEDICINE_NAME,
)


@dataclass(frozen=True)
class DoseRule:
    """Medication dose information."""

    medicine: str
    dose_mg: float
    max_24h_mg: float
    max_doses_24h: int
    note: str


def age_months(date_of_birth: date, today: date | None = None) -> int:
    """Return whole age in months."""

    today = today or date.today()
    months = (today.year - date_of_birth.year) * 12 + today.month - date_of_birth.month
    if today.day < date_of_birth.day:
        months -= 1
    return max(0, months)


def _paracetamol_rule(months_old: int) -> DoseRule:
    """Return age-band paracetamol dosing from the supplied schedule."""

    # The schedule supplied by the user lists max four doses in 24h for all
    # non-neonate age bands. Use the lower value when a range is printed.
    bands: tuple[tuple[int, int, float, str], ...] = (
        (3, 6, 60, "3-6 months"),
        (6, 24, 120, "6 months-2 years"),
        (24, 48, 180, "2-4 years"),
        (48, 72, 240, "4-6 years"),
        (72, 96, 240, "6-8 years"),
        (96, 120, 360, "8-10 years"),
        (120, 144, 480, "10-12 years"),
        (144, 192, 480, "12-16 years"),
        (192, 216, 500, "16-18 years"),
    )
    for start, end, dose, label in bands:
        if start <= months_old < end:
            return DoseRule(
                medicine=MEDICINE_PARACETAMOL,
                dose_mg=dose,
                max_24h_mg=dose * 4,
                max_doses_24h=4,
                note=label,
            )
    if months_old < 3:
        return DoseRule(
            medicine=MEDICINE_PARACETAMOL,
            dose_mg=0,
            max_24h_mg=0,
            max_doses_24h=0,
            note="under 3 months: clinician-specific dosing required",
        )
    return DoseRule(
        medicine=MEDICINE_PARACETAMOL,
        dose_mg=500,
        max_24h_mg=2000,
        max_doses_24h=4,
        note="18 years and over fallback",
    )


def _ibuprofen_rule(weight_kg: float, months_old: int) -> DoseRule:
    """Return ibuprofen dosing from the supplied weight-based schedule."""

    if months_old < 3:
        return DoseRule(
            medicine=MEDICINE_IBUPROFEN,
            dose_mg=0,
            max_24h_mg=0,
            max_doses_24h=0,
            note="under 3 months: not covered by supplied schedule",
        )

    # The photo gives rounded individual doses for common weights. Interpolate
    # by selecting the nearest lower listed weight so the card does not overstate
    # the per-dose amount.
    table: tuple[tuple[float, float], ...] = (
        (5, 35),
        (6, 45),
        (7, 50),
        (8, 60),
        (9, 65),
        (10, 75),
        (12, 90),
        (14, 105),
        (16, 120),
        (18, 135),
        (20, 150),
        (25, 185),
        (30, 225),
        (35, 260),
        (40, 300),
    )
    dose = table[0][1]
    table_weight = table[0][0]
    for listed_weight, listed_dose in table:
        if weight_kg >= listed_weight:
            table_weight = listed_weight
            dose = listed_dose
        else:
            break

    max_24h_mg = floor(weight_kg * 30)
    return DoseRule(
        medicine=MEDICINE_IBUPROFEN,
        dose_mg=dose,
        max_24h_mg=max_24h_mg,
        max_doses_24h=4,
        note=f"{table_weight:g} kg table band; max 30 mg/kg/day",
    )


def recommended_rule(
    medicine: str,
    date_of_birth: date,
    weight_kg: float,
    now: datetime | None = None,
    custom_medications: list[dict] | None = None,
) -> DoseRule:
    """Return the dose rule for a medicine and child."""

    today = (now or datetime.now()).date()
    months_old = age_months(date_of_birth, today)
    if medicine == MEDICINE_PARACETAMOL:
        return _paracetamol_rule(months_old)
    if medicine == MEDICINE_IBUPROFEN:
        return _ibuprofen_rule(weight_kg, months_old)
    for custom in custom_medications or []:
        if custom[CONF_MEDICINE_NAME] == medicine:
            return DoseRule(
                medicine=medicine,
                dose_mg=float(custom[CONF_DOSE_MG]),
                max_24h_mg=float(custom[CONF_MAX_24H_MG]),
                max_doses_24h=int(custom[CONF_MAX_DOSES_24H]),
                note="custom medication",
            )
    raise ValueError(f"Unsupported medicine: {medicine}")
