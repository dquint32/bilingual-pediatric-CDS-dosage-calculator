from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum

class SafetyLevel(str, Enum):
    """Clinical safety classification for dosage calculations"""
    SAFE = "safe"
    CAUTION = "caution"
    CRITICAL = "critical"

class MedicationType(str, Enum):
    """Supported pediatric medications"""
    ACETAMINOPHEN = "acetaminophen"
    IBUPROFEN = "ibuprofen"
    AMOXICILLIN = "amoxicillin"

class DosageRequest(BaseModel):
    """
    Request model for dosage calculation with clinical validation.
    
    All pediatric dosing must be weight-based to prevent sentinel events.
    """
    weight_kg: float = Field(
        ..., 
        gt=0, 
        le=200,
        description="Patient weight in kilograms (must be 0-200 kg)"
    )
    medication: MedicationType = Field(
        ...,
        description="Medication to calculate dosage for"
    )
    language: str = Field(
        default="en",
        pattern="^(en|es)$",
        description="Response language: 'en' for English, 'es' for Spanish"
    )
    
    @field_validator('weight_kg')
    @classmethod
    def validate_weight_range(cls, v: float) -> float:
        """
        Critical Safety Validation: Ensure weight is within human pediatric range.
        
        A weight outside this range indicates either:
        - Data entry error (misplaced decimal)
        - Non-human subject
        - Critical system error
        """
        if v < 1.0:
            raise ValueError("Weight too low: must be at least 1 kg for pediatric patient")
        if v > 200.0:
            raise ValueError("Weight too high: exceeds realistic pediatric range")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "weight_kg": 15.5,
                "medication": "acetaminophen",
                "language": "en"
            }
        }

class DosageResponse(BaseModel):
    """
    Clinical Decision Support response with bilingual output.
    
    Includes safety classifications and guardrail warnings.
    """
    error: bool = Field(
        ...,
        description="True if dosage calculation failed safety checks"
    )
    safety_level: SafetyLevel = Field(
        ...,
        description="Clinical safety classification"
    )
    
    # Dosage information (only present if safe)
    dose_mg: Optional[float] = Field(
        None,
        description="Calculated dose in milligrams"
    )
    medication_name: Optional[str] = Field(
        None,
        description="Full medication name"
    )
    
    # Bilingual instructions
    instructions_en: Optional[str] = Field(
        None,
        description="English administration instructions"
    )
    instructions_es: Optional[str] = Field(
        None,
        description="Spanish administration instructions"
    )
    
    # Bilingual messages
    message_en: str = Field(
        ...,
        description="English result message"
    )
    message_es: str = Field(
        ...,
        description="Spanish result message"
    )
    
    # Safety warnings (bilingual)
    warnings_en: List[str] = Field(
        default_factory=list,
        description="English safety warnings"
    )
    warnings_es: List[str] = Field(
        default_factory=list,
        description="Spanish safety warnings"
    )
    
    # Additional context
    calculated_dose_mg: Optional[float] = Field(
        None,
        description="Calculated dose before safety limits (if exceeded)"
    )
    max_safe_dose_mg: Optional[float] = Field(
        None,
        description="Maximum safe dose for this medication"
    )
    weight_used_kg: Optional[float] = Field(
        None,
        description="Weight used in calculation"
    )
    timestamp: str = Field(
        ...,
        description="ISO timestamp of calculation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": False,
                "safety_level": "safe",
                "dose_mg": 232.5,
                "medication_name": "Acetaminophen (Tylenol)",
                "instructions_en": "Give 232.5 mg every 6 hours",
                "instructions_es": "Dar 232.5 mg cada 6 horas",
                "message_en": "Safe dosage calculated",
                "message_es": "Dosis segura calculada",
                "warnings_en": [],
                "warnings_es": [],
                "weight_used_kg": 15.5,
                "timestamp": "2026-01-16T10:30:00"
            }
        }