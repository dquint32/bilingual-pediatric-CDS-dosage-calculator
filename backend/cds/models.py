"""Request/response contracts (Pydantic v2).

Changes from the original models:

* ``class Config`` (Pydantic v1 style, deprecated in v2) replaced by ``model_config``;
* unit conversion moved server-side: the request carries ``weight`` + ``weight_unit``,
  so pounds are converted once, by the tested code, instead of by the browser;
  the legacy ``weight_kg`` field is still accepted;
* the 1–200 kg range check lives in one place instead of three (Field bounds, a
  validator, and ``validate_weight`` in the calculator);
* ``language`` is a ``Literal`` rather than a regex.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator
from pydantic_core import PydanticCustomError

from .formulary import MedicationId

MIN_WEIGHT_KG = 1.0
MAX_WEIGHT_KG = 200.0
LB_TO_KG = 0.45359237  # exact, by definition


class SafetyLevel(StrEnum):
    SAFE = "safe"
    CAUTION = "caution"
    CRITICAL = "critical"


class WeightUnit(StrEnum):
    KG = "kg"
    LB = "lbs"


class DosageRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"weight": 33, "weight_unit": "lbs", "medication": "acetaminophen", "language": "es"}},
    )

    weight: float = Field(gt=0, allow_inf_nan=False, description="Patient weight in weight_unit")
    weight_unit: WeightUnit = WeightUnit.KG
    medication: MedicationId
    language: Literal["en", "es"] = "en"

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_weight_kg(cls, data: Any) -> Any:
        # The first version of the frontend sent {"weight_kg": ...}; keep it working.
        if isinstance(data, dict) and "weight_kg" in data and "weight" not in data:
            data = {**data, "weight": data["weight_kg"], "weight_unit": WeightUnit.KG}
            data.pop("weight_kg")
        if isinstance(data, dict) and data.get("weight_unit") == "lb":
            data = {**data, "weight_unit": WeightUnit.LB}
        return data

    @computed_field  # type: ignore[prop-decorator]
    @property
    def weight_kg(self) -> float:
        kg = self.weight * LB_TO_KG if self.weight_unit is WeightUnit.LB else self.weight
        return round(kg, 2)

    @model_validator(mode="after")
    def _plausible_weight(self) -> "DosageRequest":
        if not MIN_WEIGHT_KG <= self.weight_kg <= MAX_WEIGHT_KG:
            raise PydanticCustomError(
                "weight_range", "weight must be between {min:g} and {max:g} kg (got {got:g} kg)",
                {"min": MIN_WEIGHT_KG, "max": MAX_WEIGHT_KG, "got": self.weight_kg})
        return self


class DosageResponse(BaseModel):
    """Same field names the frontend already reads, plus daily-limit context."""

    error: bool
    safety_level: SafetyLevel
    message_en: str
    message_es: str
    warnings_en: list[str] = Field(default_factory=list)
    warnings_es: list[str] = Field(default_factory=list)
    medication: MedicationId
    medication_name_en: str
    medication_name_es: str
    weight_used_kg: float
    calculated_dose_mg: float
    max_safe_dose_mg: float
    percent_of_max: float
    dose_mg: float | None = None            # only when the dose may be given
    interval_hours: int | None = None
    max_doses_per_day: int | None = None
    instructions_en: str | None = None
    instructions_es: str | None = None
    timestamp: str


class FieldError(BaseModel):
    field: str
    message_en: str
    message_es: str


class ErrorResponse(BaseModel):
    error: Literal[True] = True
    message_en: str = "Please check the values below."
    message_es: str = "Por favor revise los valores indicados."
    errors: list[FieldError] = Field(default_factory=list)
