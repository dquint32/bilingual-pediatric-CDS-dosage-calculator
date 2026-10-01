from __future__ import annotations

import pytest
from pydantic import ValidationError

from cds.models import DosageRequest, WeightUnit


def test_kg_request() -> None:
    r = DosageRequest(weight=15, medication="acetaminophen")
    assert r.weight_kg == 15 and r.language == "en"


@pytest.mark.parametrize(("lbs", "kg"), [(33, 14.97), (2.2046226218, 1.0), (440.92, 200.0)])
def test_pounds_are_converted_server_side(lbs, kg) -> None:
    assert DosageRequest(weight=lbs, weight_unit="lbs", medication="ibuprofen").weight_kg == kg


def test_singular_lb_alias() -> None:
    assert DosageRequest.model_validate({"weight": 22, "weight_unit": "lb", "medication": "ibuprofen"}).weight_unit is WeightUnit.LB


def test_legacy_weight_kg_field_still_accepted() -> None:
    r = DosageRequest.model_validate({"weight_kg": 20, "medication": "amoxicillin"})
    assert (r.weight, r.weight_unit, r.weight_kg) == (20, WeightUnit.KG, 20)


@pytest.mark.parametrize("payload", [
    {"weight": 0.9, "medication": "ibuprofen"},                       # below 1 kg
    {"weight": 201, "medication": "ibuprofen"},                       # above 200 kg
    {"weight": 1.5, "weight_unit": "lbs", "medication": "ibuprofen"},  # 0.68 kg after conversion
    {"weight": 0, "medication": "ibuprofen"},
    {"weight": -5, "medication": "ibuprofen"},
    {"weight": "abc", "medication": "ibuprofen"},
    {"weight": float("nan"), "medication": "ibuprofen"},
    {"weight": float("inf"), "medication": "ibuprofen"},
    {"weight": 15, "medication": "morphine"},
    {"weight": 15, "medication": "ibuprofen", "language": "fr"},
    {"weight": 15, "medication": "ibuprofen", "weight_unit": "stone"},
    {"weight": 15, "medication": "ibuprofen", "extra": 1},
    {"medication": "ibuprofen"},
])
def test_invalid_requests(payload) -> None:
    with pytest.raises(ValidationError):
        DosageRequest.model_validate(payload)


def test_range_boundaries_are_inclusive() -> None:
    DosageRequest(weight=1, medication="ibuprofen")
    DosageRequest(weight=200, medication="ibuprofen")
