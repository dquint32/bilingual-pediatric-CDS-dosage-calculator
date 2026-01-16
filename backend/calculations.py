from models import SafetyLevel

# Clinical medication database
# In production, this would be from a pharmaceutical database with regular updates
MEDICATIONS = {
    "acetaminophen": {
        "name": "Acetaminophen (Tylenol)",
        "mg_per_kg": 15,
        "max_dose_mg": 1000,
        "interval_hours": 6,
        "max_daily_dose_mg": 4000
    },
    "ibuprofen": {
        "name": "Ibuprofen (Advil)",
        "mg_per_kg": 10,
        "max_dose_mg": 800,
        "interval_hours": 8,
        "max_daily_dose_mg": 3200
    },
    "amoxicillin": {
        "name": "Amoxicillin",
        "mg_per_kg": 20,
        "max_dose_mg": 1500,
        "interval_hours": 12,
        "max_daily_dose_mg": 3000
    }
}

def validate_weight(weight_kg: float) -> dict:
    """
    Critical Safety Guardrail: Validate patient weight is within realistic pediatric range.
    
    Prevents sentinel events from:
    - Decimal point errors (e.g., 155 kg entered as 1550 kg)
    - Non-pediatric patients
    - Data entry mistakes
    
    Returns:
        dict with 'valid' boolean and bilingual error messages
    """
    if weight_kg < 1.0:
        return {
            "valid": False,
            "message_en": "Invalid weight: Must be at least 1 kg for pediatric patient",
            "message_es": "Peso inválido: Debe ser al menos 1 kg para paciente pediátrico"
        }
    
    if weight_kg > 200.0:
        return {
            "valid": False,
            "message_en": "Invalid weight: Exceeds realistic pediatric range (max 200 kg)",
            "message_es": "Peso inválido: Excede rango pediátrico realista (máx 200 kg)"
        }
    
    return {
        "valid": True,
        "message_en": "Weight validated",
        "message_es": "Peso validado"
    }

def calculate_pediatric_dosage(weight_kg: float, medication: str, language: str = "en") -> dict:
    """
    Calculate weight-based pediatric dosage with clinical safety guardrails.
    
    This is the core CDS logic that prevents medication errors at point of care.
    
    Safety Checks:
    1. Weight validation (handled by caller)
    2. Maximum single dose limit
    3. Caution threshold (80% of max dose)
    
    Args:
        weight_kg: Patient weight in kilograms
        medication: Medication identifier
        language: 'en' or 'es' for bilingual output
    
    Returns:
        dict containing dosage, safety level, and bilingual instructions
    """
    
    if medication not in MEDICATIONS:
        return {
            "error": True,
            "message_en": f"Unknown medication: {medication}",
            "message_es": f"Medicamento desconocido: {medication}",
            "warnings_en": ["Medication not in CDS database"],
            "warnings_es": ["Medicamento no está en la base de datos CDS"]
        }
    
    med_info = MEDICATIONS[medication]
    
    # Calculate dose using weight-based formula
    calculated_dose = weight_kg * med_info["mg_per_kg"]
    max_dose = med_info["max_dose_mg"]
    
    # CRITICAL SAFETY GUARDRAIL: Check maximum dose
    if calculated_dose > max_dose:
        return {
            "error": True,
            "calculated_dose": round(calculated_dose, 1),
            "max_dose": max_dose,
            "message_en": f"WARNING: Calculated dose ({calculated_dose:.1f} mg) EXCEEDS maximum safe dose ({max_dose} mg)",
            "message_es": f"ADVERTENCIA: Dosis calculada ({calculated_dose:.1f} mg) EXCEDE la dosis máxima segura ({max_dose} mg)",
            "warnings_en": [
                f"Calculated: {calculated_dose:.1f} mg",
                f"Maximum safe: {max_dose} mg",
                "DO NOT ADMINISTER - Exceeds safety threshold"
            ],
            "warnings_es": [
                f"Calculado: {calculated_dose:.1f} mg",
                f"Máximo seguro: {max_dose} mg",
                "NO ADMINISTRAR - Excede umbral de seguridad"
            ]
        }
    
    # Determine safety level
    caution_threshold = max_dose * 0.8
    if calculated_dose > caution_threshold:
        safety_level = SafetyLevel.CAUTION
        warnings_en = [
            f"Dose is {(calculated_dose/max_dose*100):.0f}% of maximum safe dose",
            "Consider double-checking calculation"
        ]
        warnings_es = [
            f"La dosis es {(calculated_dose/max_dose*100):.0f}% de la dosis máxima segura",
            "Considere verificar el cálculo dos veces"
        ]
    else:
        safety_level = SafetyLevel.SAFE
        warnings_en = []
        warnings_es = []
    
    # Generate bilingual instructions
    instructions_en = f"Give {calculated_dose:.1f} mg every {med_info['interval_hours']} hours"
    instructions_es = f"Dar {calculated_dose:.1f} mg cada {med_info['interval_hours']} horas"
    
    return {
        "error": False,
        "safety_level": safety_level,
        "dose_mg": round(calculated_dose, 1),
        "medication_name": med_info["name"],
        "instructions_en": instructions_en,
        "instructions_es": instructions_es,
        "message_en": "Safe dosage calculated" if safety_level == SafetyLevel.SAFE else "Caution: High dose",
        "message_es": "Dosis segura calculada" if safety_level == SafetyLevel.SAFE else "Precaución: Dosis alta",
        "warnings_en": warnings_en,
        "warnings_es": warnings_es
    }

def convert_lbs_to_kg(weight_lbs: float) -> float:
    """
    Convert pounds to kilograms for weight-based dosing.
    
    Args:
        weight_lbs: Weight in pounds
    
    Returns:
        Weight in kilograms (rounded to 1 decimal)
    """
    return round(weight_lbs * 0.453592, 1)
