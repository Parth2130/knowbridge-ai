# KNOWBRIDGE AI

> **"Never Let Critical Project Knowledge Leave With People."**
> **Team Name: Code Crushers**

KnowBridge AI is a full-stack, enterprise-grade AI knowledge handover platform that transforms scattered project documents, meeting notes, runbooks, and team activities into structured, intelligent, and verifiable knowledge handovers.

---

## 🚀 Key Features

* **Complete Full-Stack SaaS Architecture:** Connected HTML5/CSS3/Vanilla JS frontend with Flask Blueprints REST backend and SQLite/SQLAlchemy ORM.
* **Intelligent Document Ingestion:** Full page-by-page text parsing across **PDF** (PyMuPDF), **Word** (python-docx), and **TXT** files.
* **Dual AI Knowledge Extraction Engine:**
  * **Local Deterministic NLP Engine:** Deterministic regex, key phrase extraction, responsibility mapping, deadline identification, and risk auditing with zero external API dependencies.
  * **Optional Cloud LLM Integration:** Plug-and-play support for Google Gemini (`GEMINI_API_KEY`) or OpenAI.
* **Verifiable Evidence Linking:** Every single extracted task, architectural decision, and risk links directly back to exact sentence quotes and page numbers in source documents.
* **Human-in-the-Loop Verification Workflow:** Dedicated approvals interface where project managers approve, edit, or reject AI-generated suggestions before inclusion in reports.
* **16-Section ReportLab PDF Generation:** Download boardroom-ready PDF transition documents complete with 30-60-90 day action plans.
* **Version History & Audit Log:** Automatically creates immutable versions whenever reports are edited, preserving complete change history.
* **Formal Handover Acknowledgement:** Incoming staff review and formally sign off on handover receipts with digital timestamps.
* **Blocking Dependency Enforcement:** Tasks with incomplete prerequisite dependencies are blocked from premature completion.

---

## 🎨 Enterprise Color Theme

* **Main Background:** `#F4F8FC`
* **Sidebar Background:** `#EDF5FC`
* **Card Background:** `#FFFFFF`
* **Primary Blue:** `#2475E8`
* **Secondary Blue:** `#DCEBFA`
* **Teal Accent:** `#20A99A`
* **Success Green:** `#25A66A`
* **Main Text:** `#243449`
* **Secondary Text:** `#718096`
* **Border:** `#DFE9F2`

---

## 📁 Project Directory Structure

```
knowbridge-ai/
├── app.py                     # Flask application factory and entry point
├── config.py                  # Environment and storage configurations
├── seed_demo.py               # Database seeder with sample documents
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # Documentation
│
├── database/
│   └── db.py                  # SQLAlchemy db instance
│
├── models/
│   ├── __init__.py
│   └── models.py              # Relational models (User, Project, Document, Task, Decision, Risk, Dependency, Evidence, Report, etc.)
│
├── routes/
│   ├── auth.py                # Registration, login, session management
│   ├── auth_helpers.py        # Authentication decorators
│   ├── dashboard.py           # Dashboard metrics, chart data & recent activity
│   ├── projects.py            # Project CRUD & filters
│   ├── documents.py           # Upload, view preview, download, delete
│   ├── analysis.py            # AI knowledge extraction (single & batch)
│   ├── tasks.py               # Deliverable management & dependency enforcement
│   ├── decisions.py           # Architectural Decision Records (ADRs)
│   ├── risks.py               # Risk management & task dependencies
│   ├── evidence.py            # Source citation retrieval
│   ├── reports.py             # 16-section report compiler, versioning & PDF export
│   ├── approvals.py           # Human verification approval workflow
│   ├── acknowledgements.py    # Formal sign-off workflow
│   ├── timeline.py            # Chronological audit timeline
│   ├── settings.py            # User profile, password & AI engine info
│   └── pages.py               # HTML template rendering
│
├── services/
│   ├── document_parser.py     # PyMuPDF, python-docx & TXT extraction
│   ├── ai_engine.py           # Unified orchestrator (Local NLP & Cloud Gemini)
│   ├── summarizer.py          # Executive summarisation
│   ├── task_extractor.py      # Action items, owners, deadlines & priority
│   ├── decision_extractor.py  # Architectural decisions & reasons
│   ├── risk_detector.py       # Structural & text-based risk audits
│   ├── dependency_detector.py # Pre-requisite task dependency detection
│   ├── evidence_service.py    # Source citation linkage
│   └── report_generator.py    # ReportLab 16-section PDF document generation
│
├── templates/
│   ├── base.html              # Fixed sidebar & header shell
│   ├── index.html             # Landing page with all 7 requested sections
│   ├── login.html             # Sign in
│   ├── register.html          # Registration
│   ├── dashboard.html         # Main application dashboard
│   ├── projects.html          # Project management
│   ├── documents.html         # Document management
│   ├── analysis.html          # AI knowledge extraction dashboard
│   ├── timeline.html          # Chronological activity timeline
│   ├── decisions.html         # Decision tracking
│   ├── tasks.html             # Pending tasks
│   ├── approvals.html         # Human review workflow
│   ├── reports.html           # Report generation & PDF preview
│   ├── knowledge.html         # Knowledge base repository
│   └── settings.html          # Profile & security settings
│
├── static/
│   ├── css/
│   │   ├── style.css
│   │   ├── dashboard.css
│   │   ├── components.css
│   │   └── responsive.css
│   ├── js/
│   │   ├── main.js
│   │   ├── auth.js
│   │   ├── dashboard.js
│   │   ├── projects.js
│   │   ├── documents.js
│   │   ├── analysis.js
│   │   ├── tasks.js
│   │   ├── decisions.js
│   │   ├── reports.js
│   │   ├── approvals.js
│   │   ├── timeline.js
│   │   └── knowledge.js
│   └── images/
│       └── logo.svg
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_projects.py
│   ├── test_documents.py
│   ├── test_analysis.py
│   ├── test_tasks_decisions.py
│   └── test_reports_approvals.py
│
├── uploads/                   # Stored uploaded project documents
└── instance/
    └── knowbridge.db          # SQLite database
```

---

## ⚡ Quick Start Instructions

### 1. Setup Virtual Environment
```bash
python -m venv venv
```

**Windows Activation:**
```powershell
venv\Scripts\activate
```

**Linux / macOS Activation:**
```bash
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed Demo Project & Documents
```bash
python seed_demo.py
```

### 4. Start the Application
```bash
python app.py
```

The application will be live at:
**`http://127.0.0.1:5000`**

---

## 🔑 Demo Credentials

* **Project Manager Account:**
  * **Email:** `demo@knowbridge.ai`
  * **Password:** `password123`
* **Administrator Account:**
  * **Email:** `sarah.jenkins@knowbridge.ai`
  * **Password:** `admin123`

---

## 🧪 Running the Pytest Suite

```bash
pytest tests/ -v
```

All 21 comprehensive unit and integration tests verify:
* User registration, duplicate checks, login, and session logout
* Unauthorized route protection
* Project creation, updates, and cascading deletion
* PDF (PyMuPDF), DOCX (python-docx), and TXT parsing
* Malicious/unsafe file rejection
* Task, decision, and risk extraction
* Evidence linking and citation verification
* Blocking dependency enforcement
* 16-section report generation and ReportLab PDF download
* Formal handover acknowledgement workflow
