// ============================================
// PEDIATRIC CDS DOSAGE CALCULATOR — frontend
//
// The dose is NOT calculated in JavaScript. Every request goes to the Python
// package in backend/cds (the same code the pytest suite covers):
//   * by default it runs in the browser through Pyodide (see py-engine.js),
//     so the GitHub Pages demo works with no server;
//   * set API_BASE_URL to use the FastAPI service instead
//     (e.g. 'http://127.0.0.1:8000/api' while running backend/main.py).
// ============================================

'use strict';

const API_BASE_URL = null;

const engine = window.createPyEngine({
    files: {
        'cds/__init__.py': 'backend/cds/__init__.py',
        'cds/formulary.py': 'backend/cds/formulary.py',
        'cds/models.py': 'backend/cds/models.py',
        'cds/calculations.py': 'backend/cds/calculations.py',
        'cds/service.py': 'backend/cds/service.py',
    },
    packages: ['pydantic'],
    entry: 'cds.service.calculate_json',
});

const ICONS = {
    safe: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
    caution: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg>',
    critical: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/></svg>',
};

const MEDICATIONS = ['acetaminophen', 'ibuprofen', 'amoxicillin'];

let currentLanguage = 'en';
let translations = {};
let engineState = 'loading';        // loading | ready | error
let lastOutcome = null;             // {kind: 'result'|'invalid'|'message', ...} — re-rendered on language switch

const $ = (id) => document.getElementById(id);

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    await loadTranslations();
    setupEventListeners();
    updateUILanguage();
    if (!API_BASE_URL) warmUpEngine();
});

async function loadTranslations() {
    const [en, es] = await Promise.all(
        ['en', 'es'].map((l) => fetch(`lang/${l}.json`).then((r) => {
            if (!r.ok) throw new Error(`lang/${l}.json: ${r.status}`);
            return r.json();
        }))
    );
    translations = { en, es };
}

function t(key) {
    return (translations[currentLanguage] || {})[key] ?? (translations.en || {})[key] ?? key;
}

function setupEventListeners() {
    document.querySelectorAll('.lang-btn').forEach((btn) => {
        btn.addEventListener('click', () => switchLanguage(btn.dataset.lang));
    });
    $('dosage-form').addEventListener('submit', handleFormSubmit);
    $('clear-btn').addEventListener('click', clearForm);
    $('close-purpose').addEventListener('click', () => { $('purpose-section').hidden = true; });
    $('engine-status').addEventListener('click', (e) => {
        if (e.target.closest('[data-action="retry"]')) warmUpEngine();
    });
}

// ============================================
// PYTHON ENGINE
// ============================================

async function warmUpEngine() {
    setEngineState('loading');
    try {
        await engine.load();
        setEngineState('ready');
    } catch (err) {
        console.error('Python engine failed to load:', err);
        setEngineState('error');
    }
}

function setEngineState(state) {
    engineState = state;
    renderEngineStatus();
}

function renderEngineStatus() {
    const el = $('engine-status');
    if (API_BASE_URL) {
        el.hidden = true;
        return;
    }
    el.hidden = false;
    el.dataset.state = engineState;
    if (engineState === 'loading') {
        el.innerHTML = `<span class="engine-dot" aria-hidden="true"></span>${escapeHtml(t('engineLoading'))}`;
    } else if (engineState === 'ready') {
        el.innerHTML = `<span class="engine-dot" aria-hidden="true"></span>${escapeHtml(t('engineReady'))}`;
    } else {
        el.innerHTML = `<span class="engine-dot" aria-hidden="true"></span>${escapeHtml(t('engineError'))} `
            + `<button type="button" class="link-btn" data-action="retry">${escapeHtml(t('retry'))}</button>`;
    }
}

// Both transports return {status, body} with the same body shape.
async function requestDosage(payload) {
    if (API_BASE_URL) {
        const res = await fetch(`${API_BASE_URL}/calculate-dosage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        return { status: res.status, body: await res.json() };
    }
    return JSON.parse(await engine.call(JSON.stringify(payload)));
}

// ============================================
// LANGUAGE
// ============================================

function switchLanguage(lang) {
    if (!translations[lang]) return;
    currentLanguage = lang;
    document.querySelectorAll('.lang-btn').forEach((btn) => {
        const active = btn.dataset.lang === lang;
        btn.classList.toggle('active', active);
        btn.setAttribute('aria-pressed', String(active));
    });
    updateUILanguage();
    renderOutcome();
}

function updateUILanguage() {
    document.documentElement.lang = currentLanguage;
    document.title = `${t('title')} — ${t('subtitle')}`;
    const text = {
        'app-kicker': 'kicker', 'app-title': 'title', 'app-subtitle': 'subtitle', 'purpose-title': 'purpose',
        'purpose-text': 'purposeText', 'weight-label': 'weightLabel', 'medication-label': 'medicationLabel',
        'select-placeholder': 'selectMed', 'calculate-text': 'calculate', 'clear-text': 'clear',
        'footer-disclaimer': 'footerDisclaimer', 'footer-warning': 'footerWarning',
    };
    for (const [id, key] of Object.entries(text)) $(id).textContent = t(key);
    for (const med of MEDICATIONS) {
        const opt = document.querySelector(`#medication-select option[value="${med}"]`);
        if (opt) opt.textContent = t(`med_${med}`);
    }
    $('close-purpose').setAttribute('aria-label', t('close'));
    $('weight-unit').setAttribute('aria-label', t('weightUnit'));
    renderEngineStatus();
}

// ============================================
// FORM
// ============================================

async function handleFormSubmit(e) {
    e.preventDefault();
    const raw = $('weight-input').value.trim();
    const medication = $('medication-select').value;

    if (!raw) return showMessage('enterWeight');
    if (!medication) return showMessage('selectMedication');

    const payload = {
        weight: Number(raw),
        weight_unit: $('weight-unit').value,
        medication,
        language: currentLanguage,
    };

    const btn = $('calculate-btn');
    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');
    $('calculate-text').textContent = engineState === 'ready' || API_BASE_URL ? t('calculating') : t('engineLoading');
    try {
        const { status, body } = await requestDosage(payload);
        if (!API_BASE_URL) setEngineState('ready');
        lastOutcome = status === 200 ? { kind: 'result', body } : { kind: 'invalid', body };
    } catch (err) {
        console.error('Calculation error:', err);
        if (!API_BASE_URL) setEngineState('error');
        lastOutcome = { kind: 'message', key: 'apiError' };
    } finally {
        btn.disabled = false;
        btn.removeAttribute('aria-busy');
        $('calculate-text').textContent = t('calculate');
    }
    renderOutcome(true);
}

function showMessage(key) {
    lastOutcome = { kind: 'message', key };
    renderOutcome(true);
}

function clearForm() {
    $('dosage-form').reset();
    lastOutcome = null;
    renderOutcome();
    $('weight-input').focus();
}

// ============================================
// RESULTS
// ============================================

function pick(obj, field) {
    return obj[`${field}_${currentLanguage}`] ?? obj[`${field}_en`];
}

function renderOutcome(scroll = false) {
    const box = $('results-container');
    if (!lastOutcome) {
        box.className = 'results-container hidden';
        box.innerHTML = '';
        return;
    }
    const { kind } = lastOutcome;
    if (kind === 'result') {
        box.className = `results-container ${lastOutcome.body.safety_level}`;
        box.innerHTML = resultHtml(lastOutcome.body);
    } else {
        box.className = 'results-container critical';
        const body = lastOutcome.body;
        const lines = kind === 'invalid'
            ? (body.errors || []).map((e) => pick(e, 'message'))
            : [];
        const headline = kind === 'invalid' ? pick(body, 'message') : t(lastOutcome.key);
        box.innerHTML = `
            ${headerHtml(ICONS.caution, t('checkInput'), null, null)}
            <div class="error-display">
                <p class="error-message">${escapeHtml(headline)}</p>
                ${lines.length ? `<ul class="error-list">${lines.map((l) => `<li>${escapeHtml(l)}</li>`).join('')}</ul>` : ''}
            </div>`;
    }
    if (scroll) box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function headerHtml(icon, title, subtitle, timestamp) {
    return `
        <div class="result-header">
            <div class="result-title-group">
                <div class="result-icon" aria-hidden="true">${icon}</div>
                <div class="result-title">
                    <h2>${escapeHtml(title)}</h2>
                    ${subtitle ? `<p>${escapeHtml(subtitle)}</p>` : ''}
                </div>
            </div>
            ${timestamp ? `
            <div class="result-timestamp">
                <p>${escapeHtml(t('timestamp'))}</p>
                <p>${escapeHtml(formatTimestamp(timestamp))}</p>
            </div>` : ''}
        </div>`;
}

function resultHtml(r) {
    const icon = ICONS[r.safety_level] || ICONS.caution;
    const level = t(r.safety_level);
    const warnings = pick(r, 'warnings') || [];
    const medName = pick(r, 'medication_name');
    let html = headerHtml(icon, r.error ? t('warnings') : t('dosageResult'),
        `${t('safetyLevel')}: ${level}`, r.timestamp);

    if (r.error) {
        html += `
            <div class="error-display">
                <p class="error-message">${escapeHtml(pick(r, 'message'))}</p>
            </div>`;
    } else {
        html += `
            <div class="dosage-display">
                <div class="dosage-value">
                    <span class="dose">${escapeHtml(formatNumber(r.dose_mg))} mg</span>
                    <div class="medication">${escapeHtml(medName)}</div>
                </div>
                <div class="dosage-instructions">
                    <div class="label">${escapeHtml(t('instructions'))}</div>
                    <div class="instruction-text">${escapeHtml(pick(r, 'instructions'))}</div>
                </div>
            </div>`;
    }

    if (warnings.length) {
        html += `
            <div class="warnings-section">
                ${r.error ? '' : `<div class="warnings-title">${escapeHtml(t('warnings'))}</div>`}
                ${warnings.map((w) => `<div class="warning-item">${escapeHtml(w)}</div>`).join('')}
            </div>`;
    }

    const meta = [
        [t('weightUsed'), `${formatNumber(r.weight_used_kg)} kg`],
        [t('calculatedDose'), `${formatNumber(r.calculated_dose_mg)} mg`],
        [t('maxSingleDose'), `${formatNumber(r.max_safe_dose_mg)} mg`],
        [t('percentOfMax'), `${formatNumber(r.percent_of_max)}%`],
    ];
    html += `
        <div class="metadata-grid">
            ${meta.map(([label, value]) => `
            <div class="metadata-item">
                <div class="label">${escapeHtml(label)}</div>
                <div class="value">${escapeHtml(value)}</div>
            </div>`).join('')}
        </div>`;
    return html;
}

// ============================================
// UTILITIES
// ============================================

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (c) => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
}

function formatNumber(n) {
    return Number(n).toLocaleString(currentLanguage === 'es' ? 'es-MX' : 'en-US', { maximumFractionDigits: 2 });
}

function formatTimestamp(iso) {
    return new Date(iso).toLocaleString(currentLanguage === 'es' ? 'es-MX' : 'en-US', {
        year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
}
