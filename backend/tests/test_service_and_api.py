from __future__ import annotations

import json

import pytest

from cds import service

from .conftest import FIXED_NOW


def calc(payload):
    return service.calculate(payload, now=FIXED_NOW)


def test_safe_response_contract() -> None:
    status, body = calc({"weight": 15, "medication": "acetaminophen"})
    assert status == 200 and body["error"] is False and body["safety_level"] == "safe"
    assert body["dose_mg"] == 225.0 and body["weight_used_kg"] == 15.0
    assert body["instructions_en"] == "Give 225 mg every 6 hours. Do not give more than 4 doses in 24 hours."
    assert body["instructions_es"] == "Dar 225 mg cada 6 horas. No dar más de 4 dosis en 24 horas."
    assert body["timestamp"] == "2026-01-15T09:30:00+00:00"
    assert body["warnings_en"] == []


def test_caution_response_has_bilingual_warning() -> None:
    _, body = calc({"weight": 55, "medication": "acetaminophen", "language": "es"})
    assert body["safety_level"] == "caution" and body["dose_mg"] == 825.0
    assert body["warnings_en"][0] == "Dose is 82.5% of the maximum safe single dose"
    assert body["warnings_es"][0] == "La dosis es el 82.5% de la dosis única máxima segura"


def test_critical_response_withholds_the_dose() -> None:
    _, body = calc({"weight": 80, "medication": "acetaminophen"})
    assert body["error"] is True and body["safety_level"] == "critical"
    assert body["dose_mg"] is None and body["instructions_en"] is None
    assert body["calculated_dose_mg"] == 1200.0 and body["max_safe_dose_mg"] == 1000
    assert any("DO NOT ADMINISTER" in w for w in body["warnings_en"])
    assert any("NO ADMINISTRAR" in w for w in body["warnings_es"])


def test_spanish_medication_name_is_returned() -> None:
    _, body = calc({"weight": 15, "medication": "ibuprofen"})
    assert body["medication_name_es"] == "Ibuprofeno (Advil)"


def test_pound_input_reports_rounded_kg() -> None:
    _, body = calc({"weight": 33, "weight_unit": "lbs", "medication": "acetaminophen"})
    assert body["weight_used_kg"] == 14.97  # not 14.968536


@pytest.mark.parametrize(("payload", "field"), [
    ({"weight": 0.5, "medication": "ibuprofen"}, "weight"),
    ({"weight": 15, "medication": "aspirin"}, "medication"),
    ({"medication": "ibuprofen"}, "weight"),
])
def test_validation_errors_are_bilingual_and_located(payload, field) -> None:
    status, body = calc(payload)
    assert status == 422 and body["error"] is True
    assert body["errors"][0]["field"] == field
    assert body["errors"][0]["message_es"] and body["errors"][0]["message_en"]


def test_weight_range_error_in_spanish() -> None:
    _, body = calc({"weight": 250, "medication": "ibuprofen"})
    assert body["errors"][0]["message_es"] == "peso: el peso debe estar entre 1 y 200 kg (recibido: 250 kg)"


@pytest.mark.parametrize("payload", [None, [], "text", 42])
def test_non_object_payloads(payload) -> None:
    assert calc(payload)[0] == 422


def test_json_bridge_used_by_the_browser() -> None:
    out = json.loads(service.calculate_json(json.dumps({"weight": 15, "medication": "acetaminophen", "language": "es"})))
    assert out["status"] == 200 and out["body"]["dose_mg"] == 225.0


# ------------------------------------------------------------------ HTTP


def test_api_matches_service(client) -> None:
    r = client.post("/api/calculate-dosage", json={"weight": 55, "medication": "acetaminophen"})
    assert r.status_code == 200 and r.json()["safety_level"] == "caution"


def test_api_validation_error(client) -> None:
    r = client.post("/api/calculate-dosage", json={"weight": 500, "medication": "ibuprofen"})
    assert r.status_code == 422 and r.json()["errors"][0]["field"] == "weight"


def test_api_malformed_json_is_422_not_500(client) -> None:
    r = client.post("/api/calculate-dosage", content="{not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422


def test_api_medications_and_health(client) -> None:
    meds = client.get("/api/medications").json()["medications"]
    assert {m["id"] for m in meds} == {"acetaminophen", "ibuprofen", "amoxicillin"}
    assert client.get("/health").json()["status"] == "healthy"


def test_cors_is_restricted(client) -> None:
    ok = client.options("/api/calculate-dosage", headers={"Origin": "https://davidquintana.dev", "Access-Control-Request-Method": "POST"})
    bad = client.options("/api/calculate-dosage", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "https://davidquintana.dev"
    assert "access-control-allow-origin" not in bad.headers
