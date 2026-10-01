"""Clinical calculation: pure functions, no I/O, no language strings.

Rules (unchanged from the original prototype):
* dose = weight (kg) × mg/kg
* above the maximum single dose          → CRITICAL (hard stop, no dose returned)
* above 80% of the maximum single dose   → CAUTION  (dose returned with a warning)
* otherwise                              → SAFE

New: the number of doses allowed in 24 hours is the *smaller* of what the dosing
interval allows and what keeps the day's total under the maximum daily dose. The
daily maximum was stored before but never used.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .formulary import FORMULARY, Medication, MedicationId
from .models import SafetyLevel

CAUTION_FRACTION = 0.80


@dataclass(frozen=True, slots=True)
class DoseAssessment:
    medication: Medication
    weight_kg: float
    calculated_dose_mg: float
    percent_of_max: float
    level: SafetyLevel
    max_doses_per_day: int

    @property
    def administrable(self) -> bool:
        return self.level is not SafetyLevel.CRITICAL


def round_dose(mg: float) -> float:
    """Round half up to 0.1 mg (avoids banker's rounding and float artefacts)."""
    return math.floor(mg * 10 + 0.5 + 1e-9) / 10


def classify(dose_mg: float, max_mg: float) -> SafetyLevel:
    if dose_mg > max_mg:
        return SafetyLevel.CRITICAL
    if dose_mg > max_mg * CAUTION_FRACTION:
        return SafetyLevel.CAUTION
    return SafetyLevel.SAFE


def assess(weight_kg: float, medication: MedicationId | str) -> DoseAssessment:
    med = FORMULARY[MedicationId(medication)]
    dose = round_dose(weight_kg * med.mg_per_kg)
    by_daily_cap = int(med.max_daily_dose_mg // dose) if dose else med.doses_per_day_by_interval
    return DoseAssessment(
        medication=med,
        weight_kg=weight_kg,
        calculated_dose_mg=dose,
        percent_of_max=round(dose / med.max_single_dose_mg * 100, 1),
        level=classify(dose, med.max_single_dose_mg),
        max_doses_per_day=max(1, min(med.doses_per_day_by_interval, by_daily_cap)),
    )
