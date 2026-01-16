from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from models import DosageRequest, DosageResponse, SafetyLevel
from calculations import calculate_pediatric_dosage, validate_weight

app = FastAPI(
    title="Pediatric CDS Dosage Calculator API",
    description="Clinical Decision Support API for weight-based pediatric medication dosing",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Pediatric CDS Dosage Calculator",
        "status": "operational",
        "version": "1.0.0"
    }

@app.post("/api/calculate-dosage", response_model=DosageResponse)
async def calculate_dosage(request: DosageRequest):
    """
    Calculate safe pediatric dosage with clinical guardrails.
    
    This endpoint enforces:
    - Weight validation (1-200 kg range)
    - Maximum safe dose limits
    - Bilingual output generation
    - Safety level classification
    """
    
    # Safety Guardrail 1: Validate weight is in realistic range
    weight_validation = validate_weight(request.weight_kg)
    if not weight_validation["valid"]:
        return DosageResponse(
            error=True,
            safety_level=SafetyLevel.CRITICAL,
            message_en=weight_validation["message_en"],
            message_es=weight_validation["message_es"],
            warnings_en=[weight_validation["message_en"]],
            warnings_es=[weight_validation["message_es"]],
            timestamp=datetime.now().isoformat()
        )
    
    # Calculate dosage with safety checks
    result = calculate_pediatric_dosage(
        weight_kg=request.weight_kg,
        medication=request.medication,
        language=request.language
    )
    
    # Safety Guardrail 2: Check for maximum dose exceeded
    if result["error"]:
        return DosageResponse(
            error=True,
            safety_level=SafetyLevel.CRITICAL,
            message_en=result["message_en"],
            message_es=result["message_es"],
            calculated_dose_mg=result.get("calculated_dose"),
            max_safe_dose_mg=result.get("max_dose"),
            warnings_en=result["warnings_en"],
            warnings_es=result["warnings_es"],
            timestamp=datetime.now().isoformat()
        )
    
    # Safe dosage - return complete instructions
    return DosageResponse(
        error=False,
        safety_level=result["safety_level"],
        dose_mg=result["dose_mg"],
        medication_name=result["medication_name"],
        instructions_en=result["instructions_en"],
        instructions_es=result["instructions_es"],
        message_en=result["message_en"],
        message_es=result["message_es"],
        warnings_en=result.get("warnings_en", []),
        warnings_es=result.get("warnings_es", []),
        weight_used_kg=request.weight_kg,
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/medications")
async def get_medications():
    """Return list of available medications with dosing info"""
    from calculations import MEDICATIONS
    return {"medications": MEDICATIONS}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)