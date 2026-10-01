# Pediatric Clinical Decision Support (CDS) Dosage Calculator

[![tests](https://github.com/dquint32/bilingual-pediatric-CDS-dosage-calculator/actions/workflows/tests.yml/badge.svg)](https://github.com/dquint32/bilingual-pediatric-CDS-dosage-calculator/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.11%E2%80%933.13-blue)
![Pydantic](https://img.shields.io/badge/pydantic-v2-e92063)
![coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)

Bilingual (English / Spanish) weight-based pediatric dosage calculator with clinical safety guardrails.

**Live demo:** https://dquint32.github.io/bilingual-pediatric-CDS-dosage-calculator/

The live demo has no server. It loads [Pyodide](https://pyodide.org) (CPython compiled to WebAssembly) and runs the **same `backend/cds` package the test suite covers**, so the dose shown in the browser comes from tested Python code rather than a JavaScript copy of the rules. The same package is also served by a FastAPI app for local or hosted use.

> Educational prototype. Not for clinical use. Always verify doses against current references and institutional protocols.

## What it does

1. Takes a patient weight (kg or lbs) and one of three medications.
2. Converts pounds to kilograms on the Python side (exact factor 0.45359237, rounded to 0.01 kg) and rejects weights outside 1–200 kg.
3. Calculates `dose = weight_kg × mg/kg`, rounded half-up to 0.1 mg.
4. Classifies the dose against the maximum single dose:

| Level | Rule | What the user sees |
|---|---|---|
| **Safe** | ≤ 80% of max single dose | Dose and bilingual administration instructions |
| **Caution** | > 80% and ≤ 100% | Dose plus a "double-check the weight" warning |
| **Critical** | > 100% | **No dose.** Hard stop: "DO NOT ADMINISTER — verify weight and order" |

5. Limits doses per 24 hours to the smaller of what the dosing interval allows and what keeps the day's total under the maximum daily dose.
6. Returns every message in both languages, so switching language never needs a second calculation.

Invalid input (missing fields, unknown medication, negative / non-numeric / implausible weight) returns HTTP 422 with field-level messages in English and Spanish.

## Architecture

```text
backend/cds/
├── formulary.py      reference data: MedicationId enum + immutable formulary
├── models.py         Pydantic v2 request/response contracts, unit conversion, weight range
├── calculations.py   pure clinical logic (no I/O, no language strings)
├── service.py        use case: validate → assess → bilingual response; shared by API and browser
└── api.py            FastAPI routes + CORS only
```

```text
browser (index.html + app.js)
   │  JSON payload
   ├──► py-engine.js ─► Pyodide ─► cds.service.calculate_json   (default: live demo, no server)
   └──► fetch POST /api/calculate-dosage ─► cds.api ─► cds.service.calculate   (optional)
```

Both paths call the same `service.calculate()` and return the same `{status, body}`.

## Modernization (v2)

- **Pydantic v2:** `model_config`, `computed_field`, `model_validator`, `PydanticCustomError`, `StrEnum`, and `Literal` instead of v1 `class Config` and regexes.
- **One source of truth for each rule.** The 1–200 kg check used to live in three places (Field bounds, a validator, and a calculator function); now it lives in one. Unit conversion moved from JavaScript into the tested Python.
- **Separation of concerns:** reference data, validation, clinical logic, response building, and HTTP are now separate modules. `calculations.py` is pure and has no I/O.
- **Daily maximum now enforced.** It was stored before but never used.
- **Bug fixes:**
  - Weight display: 33 lbs used to show "14.968536 kg"; it now shows 14.97 kg.
  - Floating-point rounding artefacts in doses.
  - Fragile string replacement for Spanish error messages.
- **Frontend:**
  - All dynamic content is HTML-escaped.
  - The language switch re-renders the last result and translates medication names.
  - `aria-live` result and status regions.
  - WCAG AA contrast on the primary buttons.
  - Proper heading order.
- **Tests and CI:** 58 pytest tests at 100% line coverage, covering calculations, validation edge cases, the bilingual service, and the API. They run in GitHub Actions on Python 3.11–3.13.

## Run it locally

### Frontend only (Python runs in the browser)

```bash
python -m http.server 5500
# open http://localhost:5500
```

The page must be served over HTTP (not opened as `file://`) so it can fetch the `.py` files.

### API

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py                                      # http://127.0.0.1:8000/docs
```

To point the frontend at the API instead of Pyodide, set `API_BASE_URL = 'http://127.0.0.1:8000/api'` in `app.js`. Allowed CORS origins come from the `ALLOWED_ORIGINS` environment variable (comma-separated).

```bash
curl -X POST http://127.0.0.1:8000/api/calculate-dosage \
  -H "Content-Type: application/json" \
  -d '{"weight": 33, "weight_unit": "lbs", "medication": "ibuprofen", "language": "es"}'
```

### Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest --cov=cds --cov-report=term-missing
```

## Formulary (demonstration values)

| Medication | mg/kg | Max single dose | Interval | Max daily dose |
|---|---|---|---|---|
| Acetaminophen | 15 | 1000 mg | q6h | 4000 mg |
| Ibuprofen | 10 | 800 mg | q8h | 3200 mg |
| Amoxicillin | 20 | 1500 mg | q12h | 3000 mg |

These values come from the original course prototype and are kept as demonstration data. They are **not** a clinical reference. For example, the usual pediatric OTC single-dose cap for ibuprofen is lower than 800 mg, and amoxicillin dosing depends on the indication. Values live in one file (`backend/cds/formulary.py`), so a pharmacist-reviewed table can replace them without touching the logic.

## Project structure

```text
├── index.html            UI
├── styles.css            dark "Electric Tangerine" theme
├── app.js                UI logic; sends requests to the Python engine or the API
├── py-engine.js          Pyodide loader (runs backend/cds in the browser)
├── dq-theme.css/.js      shared design system (same look as davidquintana.dev, light/dark)
├── lang/en.json, es.json UI strings
├── backend/
│   ├── cds/              the Python package (see Architecture)
│   ├── tests/            pytest suite
│   ├── main.py           uvicorn entry point
│   ├── requirements.txt
│   └── requirements-dev.txt
└── .github/workflows/tests.yml
```

## Disclaimer

Created as an educational prototype for CIS 3030. It must not be used for clinical decision-making.

**Developer:** David Quintana · [davidquintana.dev](https://davidquintana.dev) · MIT License
