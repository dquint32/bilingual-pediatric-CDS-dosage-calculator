"""Medication reference data.

One immutable table replaces the ``MEDICATIONS`` dict that was imported ad hoc by
both the API and the calculator. Names are stored in English and Spanish so a
Spanish-language result no longer shows the English product name.

These values are configured for demonstration only. They are not clinical
guidance and have not been reviewed for use with real patients.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


class MedicationId(StrEnum):
    ACETAMINOPHEN = "acetaminophen"
    IBUPROFEN = "ibuprofen"
    AMOXICILLIN = "amoxicillin"


@dataclass(frozen=True, slots=True)
class Medication:
    id: MedicationId
    name_en: str
    name_es: str
    mg_per_kg: float
    max_single_dose_mg: float
    interval_hours: int
    max_daily_dose_mg: float

    @property
    def doses_per_day_by_interval(self) -> int:
        return 24 // self.interval_hours

    def name(self, language: str) -> str:
        return self.name_es if language == "es" else self.name_en


FORMULARY: Mapping[MedicationId, Medication] = MappingProxyType({
    MedicationId.ACETAMINOPHEN: Medication(
        MedicationId.ACETAMINOPHEN, "Acetaminophen (Tylenol)", "Acetaminofén (Tylenol)",
        mg_per_kg=15, max_single_dose_mg=1000, interval_hours=6, max_daily_dose_mg=4000),
    MedicationId.IBUPROFEN: Medication(
        MedicationId.IBUPROFEN, "Ibuprofen (Advil)", "Ibuprofeno (Advil)",
        mg_per_kg=10, max_single_dose_mg=800, interval_hours=8, max_daily_dose_mg=3200),
    MedicationId.AMOXICILLIN: Medication(
        MedicationId.AMOXICILLIN, "Amoxicillin", "Amoxicilina",
        mg_per_kg=20, max_single_dose_mg=1500, interval_hours=12, max_daily_dose_mg=3000),
})
