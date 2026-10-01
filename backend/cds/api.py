"""HTTP layer: routing and CORS only. All clinical logic lives in service/calculations."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import service
from .formulary import FORMULARY
from .models import DosageResponse, ErrorResponse

DEFAULT_ORIGINS = "https://dquint32.github.io,https://davidquintana.dev,http://127.0.0.1:5500,http://localhost:5500"


def create_app() -> FastAPI:
    app = FastAPI(title="Pediatric CDS Dosage Calculator API", version="2.0.0",
                  description="Weight-based pediatric dosing with clinical guardrails. Demonstration only.")
    origins = [o.strip().rstrip("/") for o in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    @app.get("/health")
    def health() -> dict:
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    @app.post("/api/calculate-dosage", response_model=DosageResponse,
              responses={422: {"model": ErrorResponse}})
    async def calculate_dosage(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
        except ValueError:
            payload = None
        status, body = service.calculate(payload)
        return JSONResponse(status_code=status, content=body)

    @app.get("/api/medications")
    def medications() -> dict:
        return {"medications": [
            {"id": m.id.value, "name_en": m.name_en, "name_es": m.name_es, "mg_per_kg": m.mg_per_kg,
             "max_single_dose_mg": m.max_single_dose_mg, "interval_hours": m.interval_hours,
             "max_daily_dose_mg": m.max_daily_dose_mg}
            for m in FORMULARY.values()]}

    return app


app = create_app()
