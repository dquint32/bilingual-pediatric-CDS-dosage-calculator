# Pediatric Clinical Decision Support (CDS) Dosage Calculator

A professional-grade, full-stack medical tool designed to calculate weight-based pediatric dosages while enforcing strict clinical safety guardrails. This project demonstrates the intersection of software engineering and patient safety.

## 🏥 Project Overview
Medication errors are a significant concern in pediatric care. This CDS prototype provides healthcare providers with an automated, bilingual safety layer. It calculates dosages for common pediatric medications (Acetaminophen, Ibuprofen, Amoxicillin) based on patient weight and evaluates the result against clinical maximums in real-time.

## ✨ Key Features
* **Safety-First Clinical Logic:** Implements three levels of safety assessment: **Safe**, **Caution** (80% of max dose), and **Critical** (exceeds max dose).
* **Bilingual Accessibility:** Full support for English and Spanish, providing instructions and safety alerts in the provider's or patient's preferred language.
* **Weight Validation:** Built-in guardrails to prevent data entry errors by restricting patient weights to a realistic pediatric range (1kg – 200kg).
* **Modern Healthcare UI:** A high-contrast "Electric Tangerine" dark mode theme designed for high visibility in clinical settings, adhering to WCAG 2.1 AA accessibility standards.

## 🛠️ Tech Stack
* **Backend:** Python 3.13 with [FastAPI](https://fastapi.tiangolo.com/) for high-performance API delivery.
* **Data Validation:** [Pydantic](https://docs.pydantic.dev/) for strict type enforcement and request validation.
* **Frontend:** Vanilla JavaScript (ES6+), HTML5 (Semantic), and CSS3 (Custom Properties/Variables).
* **Internationalization:** JSON-based i18n system for seamless language toggling.

## 🛡️ Clinical Guardrails & Logic
The system's core logic (`calculations.py`) is designed to prevent "Sentinel Events" (catastrophic medical errors):
1.  **Dose Capping:** If a weight-based calculation exceeds the adult maximum (e.g., 1000mg for Acetaminophen), the system triggers a **CRITICAL** alert and blocks administration instructions.
2.  **Safety Buffers:** Calculations reaching 80% of a maximum dose are flagged with a **CAUTION** status to prompt a manual double-check.
3.  **Bilingual Warnings:** Critical alerts are delivered in both languages to ensure no miscommunication during high-stakes care.

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Modern Web Browser

### Installation
1.  **Clone the repository**
    ```bash
    git clone [https://github.com/yourusername/pediatric-cds-calculator.git](https://github.com/yourusername/pediatric-cds-calculator.git)
    cd pediatric-cds-calculator
    ```

2.  **Set up the Backend**
    ```bash
    cd backend
    pip install -r requirements.txt
    python main.py
    ```
    The API will be available at `http://localhost:8000`.

3.  **Launch the Frontend**
    Open `index.html` in your browser. Ensure the `API_BASE_URL` in `app.js` matches your running backend service.

## 📝 Project Structure
```text
├── backend/
│   ├── main.py          # FastAPI application & endpoints
│   ├── models.py        # Pydantic data models & Enums
│   ├── calculations.py  # Core clinical logic & safety checks
│   └── requirements.txt # Python dependencies
├── frontend/
│   ├── index.html       # Semantic UI structure
│   ├── styles.css       # Custom healthcare theme
│   └── app.js           # Frontend logic & API communication
└── lang/
    ├── en.json          # English translation strings
    └── es.json          # Spanish translation strings
⚖️ Disclaimer
This application is a prototype created for educational purposes in partial fulfillment of CIS 3030 course requirements. It should not be used for actual clinical decision-making. Always verify dosages with current medical protocols.

Developer: David Quintana Contact: dquint32@msudenver.edu
