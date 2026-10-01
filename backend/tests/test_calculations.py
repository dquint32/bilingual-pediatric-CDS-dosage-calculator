from __future__ import annotations

import pytest

from cds.calculations import CAUTION_FRACTION, assess, classify, round_dose
from cds.formulary import FORMULARY, MedicationId
from cds.models import SafetyLevel


@pytest.mark.parametrize(("weight", "med", "dose", "level"), [
    (15, "acetaminophen", 225.0, SafetyLevel.SAFE),
    (55, "acetaminophen", 825.0, SafetyLevel.CAUTION),
    (80, "acetaminophen", 1200.0, SafetyLevel.CRITICAL),
    (18, "ibuprofen", 180.0, SafetyLevel.SAFE),
    (20, "amoxicillin", 400.0, SafetyLevel.SAFE),
])
def test_known_doses(weight, med, dose, level) -> None:
    a = assess(weight, med)
    assert (a.calculated_dose_mg, a.level) == (dose, level)


@pytest.mark.parametrize("med", list(MedicationId))
def test_threshold_boundaries_for_every_medication(med) -> None:
    m = FORMULARY[med]
    max_mg = m.max_single_dose_mg
    exactly_80 = max_mg * CAUTION_FRACTION
    assert classify(exactly_80, max_mg) is SafetyLevel.SAFE          # 80% is still safe
    assert classify(exactly_80 + 0.1, max_mg) is SafetyLevel.CAUTION  # just above → caution
    assert classify(max_mg, max_mg) is SafetyLevel.CAUTION            # exactly the max is allowed
    assert classify(max_mg + 0.1, max_mg) is SafetyLevel.CRITICAL     # one tenth over → hard stop


def test_critical_is_not_administrable() -> None:
    assert not assess(80, "acetaminophen").administrable
    assert assess(55, "acetaminophen").administrable


@pytest.mark.parametrize(("mg", "expected"), [(149.6880, 149.7), (0.05, 0.1), (224.95, 225.0), (10.0, 10.0)])
def test_round_dose_half_up(mg, expected) -> None:
    assert round_dose(mg) == expected


@pytest.mark.parametrize(("weight", "med", "doses"), [
    (15, "acetaminophen", 4),   # 225 mg × 4 = 900 ≤ 4000
    (66, "acetaminophen", 4),   # 990 mg × 4 = 3960 ≤ 4000
    (18, "ibuprofen", 3),       # every 8 h → 3
    (75, "amoxicillin", 2),     # every 12 h → 2
])
def test_doses_per_day_respect_interval_and_daily_cap(weight, med, doses) -> None:
    a = assess(weight, med)
    assert a.max_doses_per_day == doses
    assert a.calculated_dose_mg * a.max_doses_per_day <= FORMULARY[MedicationId(med)].max_daily_dose_mg


def test_daily_cap_can_limit_doses() -> None:
    # A hypothetical drug where four doses would break the daily cap.
    from cds.formulary import Medication
    import cds.calculations as calc
    med = Medication(MedicationId.ACETAMINOPHEN, "x", "x", mg_per_kg=15, max_single_dose_mg=1000,
                     interval_hours=6, max_daily_dose_mg=2000)
    original = dict(calc.FORMULARY)
    try:
        calc.FORMULARY = {MedicationId.ACETAMINOPHEN: med}  # type: ignore[assignment]
        assert assess(50, "acetaminophen").max_doses_per_day == 2   # 750 mg → floor(2000/750) = 2
    finally:
        calc.FORMULARY = original  # type: ignore[assignment]


def test_every_medication_has_spanish_name() -> None:
    for m in FORMULARY.values():
        assert m.name_es and m.name_es != m.name_en
        assert m.name("es") == m.name_es and m.name("en") == m.name_en
