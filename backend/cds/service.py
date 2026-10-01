"""Use-case layer shared by the FastAPI app and the in-browser demo (Pyodide).

``calculate(payload)`` takes the raw JSON-like dict, validates it, runs the
clinical assessment, and builds the bilingual response. It returns
``(status_code, body)`` so both callers produce identical results.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from .calculations import DoseAssessment, assess
from .models import DosageRequest, DosageResponse, ErrorResponse, FieldError, SafetyLevel


def _fmt(mg: float) -> str:
    return f"{mg:g}" if mg == int(mg) else f"{mg:.1f}"


def build_response(req: DosageRequest, a: DoseAssessment, now: datetime | None = None) -> DosageResponse:
    med = a.medication
    pct = f"{a.percent_of_max:g}"
    common = dict(
        safety_level=a.level, medication=med.id,
        medication_name_en=med.name_en, medication_name_es=med.name_es,
        weight_used_kg=a.weight_kg, calculated_dose_mg=a.calculated_dose_mg,
        max_safe_dose_mg=med.max_single_dose_mg, percent_of_max=a.percent_of_max,
        timestamp=(now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
    )
    dose, cap = _fmt(a.calculated_dose_mg), _fmt(med.max_single_dose_mg)

    if a.level is SafetyLevel.CRITICAL:
        return DosageResponse(
            error=True, **common,
            message_en=f"Calculated dose ({dose} mg) exceeds the maximum safe single dose ({cap} mg).",
            message_es=f"La dosis calculada ({dose} mg) supera la dosis única máxima segura ({cap} mg).",
            warnings_en=[f"Calculated: {dose} mg", f"Maximum safe: {cap} mg", "DO NOT ADMINISTER — verify weight and order"],
            warnings_es=[f"Calculada: {dose} mg", f"Máximo seguro: {cap} mg", "NO ADMINISTRAR — verifique el peso y la orden"],
        )

    n, h = a.max_doses_per_day, med.interval_hours
    warnings_en: list[str] = []
    warnings_es: list[str] = []
    if a.level is SafetyLevel.CAUTION:
        warnings_en = [f"Dose is {pct}% of the maximum safe single dose", "Double-check the weight before giving"]
        warnings_es = [f"La dosis es el {pct}% de la dosis única máxima segura", "Verifique el peso antes de administrar"]
    return DosageResponse(
        error=False, **common, dose_mg=a.calculated_dose_mg, interval_hours=h, max_doses_per_day=n,
        message_en="Safe dosage calculated" if a.level is SafetyLevel.SAFE else "Caution: high dose",
        message_es="Dosis segura calculada" if a.level is SafetyLevel.SAFE else "Precaución: dosis alta",
        warnings_en=warnings_en, warnings_es=warnings_es,
        instructions_en=f"Give {dose} mg every {h} hours. Do not give more than {n} doses in 24 hours.",
        instructions_es=f"Dar {dose} mg cada {h} horas. No dar más de {n} dosis en 24 horas.",
    )


_ES_FIELD = {"weight": "peso", "weight_unit": "unidad", "medication": "medicamento", "language": "idioma"}


def format_errors(errors: list[dict[str, Any]]) -> ErrorResponse:
    out = []
    for e in errors:
        loc = [str(p) for p in e.get("loc", ()) if p != "body"]
        kind = e.get("type")
        ctx = e.get("ctx") or {}
        if kind == "weight_range":
            field = "weight"
            en = f"weight must be between {ctx['min']:g} and {ctx['max']:g} kg (got {ctx['got']:g} kg)"
            es = f"el peso debe estar entre {ctx['min']:g} y {ctx['max']:g} kg (recibido: {ctx['got']:g} kg)"
        else:
            field = ".".join(loc) or "request"
            en = str(e.get("msg", ""))
            es = _ES_BY_TYPE.get(kind, en)
        out.append(FieldError(field=field, message_en=f"{field}: {en}",
                              message_es=f"{_ES_FIELD.get(field, field)}: {es}"))
    return ErrorResponse(errors=out)


_ES_BY_TYPE = {
    "missing": "valor requerido",
    "greater_than": "debe ser mayor que 0",
    "float_parsing": "debe ser un número",
    "finite_number": "debe ser un número válido",
    "enum": "valor no permitido",
    "literal_error": "valor no permitido",
    "extra_forbidden": "campo no permitido",
    "model_type": "solicitud inválida",
    "model_attributes_type": "solicitud inválida",
}


def calculate(payload: Any, now: datetime | None = None) -> tuple[int, dict[str, Any]]:
    try:
        req = DosageRequest.model_validate(payload)
    except ValidationError as exc:
        return 422, format_errors(exc.errors()).model_dump(mode="json")
    return 200, build_response(req, assess(req.weight_kg, req.medication), now).model_dump(mode="json")


def calculate_json(payload_json: str) -> str:
    """String-in/string-out wrapper for the browser bridge."""
    status, body = calculate(json.loads(payload_json))
    return json.dumps({"status": status, "body": body}, ensure_ascii=False)
