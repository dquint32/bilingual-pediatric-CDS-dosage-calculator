// ============================================
// PEDIATRIC CDS DOSAGE CALCULATOR
// Frontend Application Logic
// ============================================

// Try localhost first, fallback to 127.0.0.1 if needed
const API_BASE_URL = 'http://127.0.0.1:8000/api';

let currentLanguage = 'en';
let translations = {};

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    await loadTranslations();
    setupEventListeners();
    updateUILanguage();
});

// ============================================
// LOAD BILINGUAL TRANSLATIONS
// ============================================

async function loadTranslations() {
    try {
        const [enData, esData] = await Promise.all([
            fetch('lang/en.json').then(r => r.json()),
            fetch('lang/es.json').then(r => r.json())
        ]);
        
        translations = {
            en: enData,
            es: esData
        };
    } catch (error) {
        console.error('Failed to load translations:', error);
        // Fallback to embedded translations
        translations = getFallbackTranslations();
    }
}

// ============================================
// EVENT LISTENERS
// ============================================

function setupEventListeners() {
    // Language toggle buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', () => switchLanguage(btn.dataset.lang));
    });
    
    // Form submission
    document.getElementById('dosage-form').addEventListener('submit', handleFormSubmit);
    
    // Clear button
    document.getElementById('clear-btn').addEventListener('click', clearForm);
    
    // Close purpose section
    document.getElementById('close-purpose').addEventListener('click', () => {
        document.getElementById('purpose-section').style.display = 'none';
    });
}

// ============================================
// LANGUAGE SWITCHING
// ============================================

function switchLanguage(lang) {
    currentLanguage = lang;
    
    // Update button states
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });
    
    updateUILanguage();
}

function updateUILanguage() {
    const t = translations[currentLanguage];
    
    if (!t) return;
    
    // Update all translatable elements
    document.getElementById('app-title').textContent = t.title;
    document.getElementById('app-subtitle').textContent = t.subtitle;
    document.getElementById('purpose-title').textContent = t.purpose;
    document.getElementById('purpose-text').textContent = t.purposeText;
    document.getElementById('weight-label').textContent = t.weightLabel;
    document.getElementById('medication-label').textContent = t.medicationLabel;
    document.getElementById('select-placeholder').textContent = t.selectMed;
    document.getElementById('calculate-text').textContent = t.calculate;
    document.getElementById('clear-text').textContent = t.clear;
    document.getElementById('footer-disclaimer').textContent = t.footerDisclaimer;
    document.getElementById('footer-warning').textContent = t.footerWarning;
}

// ============================================
// FORM HANDLING
// ============================================

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const weightValue = parseFloat(document.getElementById('weight-input').value);
    const weightUnit = document.getElementById('weight-unit').value;
    const medication = document.getElementById('medication-select').value;
    
    // Convert weight to kg if needed
    const weightKg = weightUnit === 'lbs' ? convertLbsToKg(weightValue) : weightValue;
    
    // Validate inputs
    if (!weightValue || !medication) {
        displayError(
            translations[currentLanguage].enterWeight || 'Please enter weight and select medication'
        );
        return;
    }
    
    // Call backend API
    await calculateDosage(weightKg, medication);
}

function clearForm() {
    document.getElementById('dosage-form').reset();
    document.getElementById('results-container').classList.add('hidden');
}

// ============================================
// API COMMUNICATION
// ============================================

async function calculateDosage(weightKg, medication) {
    try {
        const response = await fetch(`${API_BASE_URL}/calculate-dosage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                weight_kg: weightKg,
                medication: medication,
                language: currentLanguage
            })
        });
        
        if (!response.ok) {
            throw new Error('API request failed');
        }
        
        const result = await response.json();
        displayResults(result);
        
    } catch (error) {
        console.error('Calculation error:', error);
        displayError(
            translations[currentLanguage].apiError || 
            'Unable to connect to calculation service. Please try again.'
        );
    }
}

// ============================================
// RESULTS DISPLAY
// ============================================

function displayResults(result) {
    const container = document.getElementById('results-container');
    const t = translations[currentLanguage];
    
    // Clear previous results
    container.innerHTML = '';
    
    // Set safety level class
    container.className = `results-container ${result.safety_level}`;
    
    // Get appropriate message based on language
    const message = currentLanguage === 'en' ? result.message_en : result.message_es;
    const warnings = currentLanguage === 'en' ? result.warnings_en : result.warnings_es;
    const instructions = currentLanguage === 'en' ? result.instructions_en : result.instructions_es;
    
    // Build results HTML
    let html = `
        <div class="result-header">
            <div class="result-title-group">
                <div class="result-icon">${getSafetyIcon(result.safety_level)}</div>
                <div class="result-title">
                    <h3>${result.error ? t.warnings : t.dosageResult}</h3>
                    <p>${t.safetyLevel}: ${t[result.safety_level]}</p>
                </div>
            </div>
            <div class="result-timestamp">
                <p>${t.timestamp}</p>
                <p>${formatTimestamp(result.timestamp)}</p>
            </div>
        </div>
    `;
    
    if (result.error) {
        // Error display
        html += `
            <div class="error-display">
                <p class="error-message">${message}</p>
            </div>
        `;
        
        if (warnings && warnings.length > 0) {
            html += `
                <div class="warnings-section">
                    ${warnings.map(w => `
                        <div class="warning-item">⚠️ ${w}</div>
                    `).join('')}
                </div>
            `;
        }
    } else {
        // Success display
        html += `
            <div class="dosage-display">
                <div class="dosage-value">
                    <span class="dose">${result.dose_mg} mg</span>
                    <div class="medication">${result.medication_name}</div>
                </div>
                <div class="dosage-instructions">
                    <div class="label">${t.instructions}</div>
                    <div class="instruction-text">${instructions}</div>
                </div>
            </div>
        `;
        
        if (warnings && warnings.length > 0) {
            html += `
                <div class="warnings-section">
                    <div class="warnings-title">
                        ⚠️ ${t.warnings}
                    </div>
                    ${warnings.map(w => `
                        <div class="warning-item">${w}</div>
                    `).join('')}
                </div>
            `;
        }
        
        html += `
            <div class="metadata-grid">
                <div class="metadata-item">
                    <div class="label">${t.weightLabel}</div>
                    <div class="value">${result.weight_used_kg} kg</div>
                </div>
                <div class="metadata-item">
                    <div class="label">${t.safetyLevel}</div>
                    <div class="value">${t[result.safety_level]}</div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
    container.classList.remove('hidden');
    
    // Scroll to results
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function displayError(message) {
    const container = document.getElementById('results-container');
    container.className = 'results-container critical';
    container.innerHTML = `
        <div class="result-header">
            <div class="result-title-group">
                <div class="result-icon">⚠️</div>
                <div class="result-title">
                    <h3>${translations[currentLanguage].warnings}</h3>
                </div>
            </div>
        </div>
        <div class="error-display">
            <p class="error-message">${message}</p>
        </div>
    `;
    container.classList.remove('hidden');
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function convertLbsToKg(lbs) {
    return lbs * 0.453592;
}

function getSafetyIcon(level) {
    const icons = {
        safe: '✓',
        caution: '⚠️',
        critical: '⚠️'
    };
    return icons[level] || '•';
}

function formatTimestamp(isoString) {
    const date = new Date(isoString);
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleString(currentLanguage === 'en' ? 'en-US' : 'es-ES', options);
}

// ============================================
// FALLBACK TRANSLATIONS
// ============================================

function getFallbackTranslations() {
    return {
        en: {
            title: "Pediatric Clinical Decision Support",
            subtitle: "Weight-Based Dosage Calculator",
            purpose: "Purpose",
            purposeText: "This prototype demonstrates how Clinical Decision Support (CDS) logic can reduce medication errors at the point of care by enforcing safety guardrails and providing bilingual instructions.",
            weightLabel: "Patient Weight",
            medicationLabel: "Select Medication",
            selectMed: "Choose medication...",
            calculate: "Calculate Safe Dosage",
            clear: "Clear",
            dosageResult: "Recommended Dosage",
            instructions: "Administration Instructions",
            warnings: "Safety Alerts",
            timestamp: "Calculation Time",
            safetyLevel: "Safety Assessment",
            safe: "Safe",
            caution: "Caution",
            critical: "Critical - Do Not Administer",
            enterWeight: "Please enter patient weight",
            apiError: "Unable to connect to service",
            footerDisclaimer: "Clinical Decision Support Prototype • For Educational Purposes Only",
            footerWarning: "Always verify dosages with current medical guidelines and protocols"
        },
        es: {
            title: "Soporte de Decisiones Clínicas Pediátricas",
            subtitle: "Calculadora de Dosis Basada en Peso",
            purpose: "Propósito",
            purposeText: "Este prototipo demuestra cómo la lógica de Soporte de Decisiones Clínicas (CDS) puede reducir errores de medicación en el punto de atención al hacer cumplir las medidas de seguridad y proporcionar instrucciones bilingües.",
            weightLabel: "Peso del Paciente",
            medicationLabel: "Seleccionar Medicamento",
            selectMed: "Elegir medicamento...",
            calculate: "Calcular Dosis Segura",
            clear: "Limpiar",
            dosageResult: "Dosis Recomendada",
            instructions: "Instrucciones de Administración",
            warnings: "Alertas de Seguridad",
            timestamp: "Hora de Cálculo",
            safetyLevel: "Evaluación de Seguridad",
            safe: "Seguro",
            caution: "Precaución",
            critical: "Crítico - No Administrar",
            enterWeight: "Por favor ingrese el peso del paciente",
            apiError: "No se puede conectar al servicio",
            footerDisclaimer: "Prototipo de Soporte de Decisiones Clínicas • Solo con Fines Educativos",
            footerWarning: "Siempre verifique las dosis con las pautas y protocolos médicos actuales"
        }
    };
}