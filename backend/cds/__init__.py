"""Pediatric clinical decision support: weight-based dosing with safety guardrails.

Layers:
    formulary.py     medication reference table (EN/ES names, limits)
    models.py        Pydantic v2 request/response contracts
    calculations.py  pure dose assessment (no I/O, no strings)
    service.py       validate -> assess -> bilingual response; shared by the API and the browser demo
    api.py           FastAPI routing only
"""
