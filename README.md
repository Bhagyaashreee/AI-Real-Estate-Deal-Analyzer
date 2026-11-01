# AI Real Estate Deal Analyzer (India) 🏢🇮🇳

A locally running, privacy-respecting, AI-powered real estate investment analysis platform specialized for the Indian property market.

---

## 🌟 Key Highlights

- **100% Free & Local Execution**: Zero cloud API dependencies, zero subscriptions, zero recurring costs.
- **Indian Financial Metrics**: Native financial calculations in Indian Rupees (₹), formatted in Lakhs (L) and Crores (Cr).
- **Professional PDF Investment Reports (Phase 6)**: Institutional 10-page A4 PDF memoranda generated locally using ReportLab Platypus and headless Matplotlib charts, with live browser preview and download.
- **Advanced Risk Engine & What-If Simulator (Phase 5)**: 5-category risk breakdown (Financial, Loan, Rental, Data Reliability, Legal Verification), 0–100 risk score, 0–100 data confidence engine, and 6 preconfigured market stress scenarios.
- **Regional Market Benchmarking (Phase 5)**: Ground-truth benchmarks across 8 Indian cities (Hyderabad, Bengaluru, Chennai, Pune, Mumbai, Guntur, Vijayawada, Visakhapatnam) with property-to-market yield and price/sq.ft delta tracking.
- **Local Ollama AI Integration (Phase 4)**: Powered by local **Ollama** running `llama3.2:3b` for grounded investment verdicts, executive summaries, three-tier risk profiling, and interactive property Q&A.
- **Financial Modeling & Deal Engine (Phase 3)**: Deterministic evaluation of Gross Yield, Net Yield (NOI), Reducing-Balance EMI, Cash-on-Cash ROI, Break-Even analysis, and multi-scenario stress testing.
- **Explainable Deal Scoring (0–100)**: Transparent investment scoring with positive return drivers, risk flags, and 5 deal classifications (`Excellent Deal`, `Good Deal`, `Average Deal`, `Overpriced`, `High Risk`).
- **Property Comparison & Trade-off Analysis**: Side-by-side comparison of up to 4 properties with Recharts comparative analytics and local AI trade-off evaluation.
- **Property Management & Ingestion (Phase 2)**: Full CRUD, multi-criteria filtering, pagination, and robust CSV bulk import with row-by-row error reporting.
- **Simulated Indian Demo Catalog**: 24 simulated property listings across Hyderabad, Bengaluru, Chennai, Pune, Mumbai, Guntur, Vijayawada, and Visakhapatnam.
- **Persistent Local Database**: Built-in **SQLite** storage (`backend/data/real_estate.db`).
- **High-Performance Dark SaaS Dashboard**: Modern financial analytics UI built with **Next.js**, **React**, **TypeScript**, **Tailwind CSS**, and **Recharts**.

---

## 🏗️ Architecture & Project Structure

```text
AI-Real-Estate-Deal-Analyzer/
│
├── frontend/                     # Next.js 16 + React 19 + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css       # Obsidian/slate dark theme & custom scrollbars
│   │   │   ├── layout.tsx        # Root HTML layout & metadata
│   │   │   └── page.tsx          # Main SaaS Dashboard & Module Switcher
│   │   └── components/
│   │       ├── Sidebar.tsx       # Navigation & local environment badges
│   │       ├── Header.tsx        # Search, city filters, & live health indicator
│   │       ├── KpiCards.tsx      # Metric cards (Yield, Deals, Cash Flow, Ticket)
│   │       ├── YieldChart.tsx    # Recharts micro-market yield comparison
│   │       ├── DealsTable.tsx    # Property screener table with AI deal scores
│   │       ├── PropertiesCatalog.tsx # Property catalog, filters, view switcher
│   │       ├── PropertyCard.tsx  # Visual listing cards with Indian currency metrics
│   │       ├── AddPropertyModal.tsx # Add/Edit form with live INR preview
│   │       ├── PropertyDetailsModal.tsx # In-depth financial breakdown drawer
│   │       ├── CSVImportModal.tsx # CSV file upload & validation results
│   │       ├── FinancialAnalysisView.tsx # Financial Deal Engine, Recharts charts, multi-property comparison
│   │       ├── RiskIntelligenceView.tsx # Phase 5: Risk Engine, What-If Simulator & Benchmarking
│   │       ├── PdfReportsView.tsx        # Phase 6: Investment Report Studio & Inline PDF Viewer
│   │       ├── AIDealAdvisor.tsx # Local Ollama AI Deal Advisor, Structured Report & Interactive Chat
│   │       └── HealthBanner.tsx  # Live FastAPI + SQLite + Ollama diagnostic drawer
│   ├── .env.example              # NEXT_PUBLIC_API_URL template
│   ├── .env.local                # Local Next.js environment
│   ├── package.json              # Next.js, React, Recharts, Lucide-React
│   └── tsconfig.json
│
├── backend/                      # Python FastAPI Backend
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── health.py     # System health & Ollama readiness
│   │   │       │   ├── properties.py # Property CRUD, CSV import, filtering, summary
│   │   │       │   ├── analysis.py   # Financial calculations, EMI, scoring & comparison
│   │   │       │   ├── ai.py         # Local Ollama AI analyze, chat, status & compare endpoints
│   │   │       │   ├── risk.py       # Phase 5: Risk analysis, What-if simulator, AI risk explainer
│   │   │       │   ├── benchmarks.py # Phase 5: Benchmark listing, matching & CSV import
│   │   │       │   └── reports.py    # Phase 6: PDF report generation, download & preview
│   │   │       └── api.py            # Aggregated v1 API router
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic BaseSettings, local CORS & Ollama timeout settings
│   │   │   └── database.py       # SQLite connection & session management
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── property.py       # Property & investment SQLAlchemy model
│   │   │   └── benchmark.py      # Market benchmark regional model (Phase 5)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── property.py       # Pydantic schemas (Create, Update, Response, CSV)
│   │   │   ├── analysis.py       # Pydantic financial analysis & comparison schemas
│   │   │   ├── ai.py             # Pydantic structured AI analysis, chat & comparison schemas
│   │   │   ├── risk.py           # Phase 5: Risk breakdown, What-if simulation & confidence schemas
│   │   │   ├── benchmark.py      # Phase 5: Benchmark schemas & CSV import
│   │   │   └── report.py         # Phase 6: PDF report generation & metadata schemas
│   │   ├── services/
│   │   │   ├── financial_engine.py # Deterministic yields, reducing-balance EMI, cash flow, ROI
│   │   │   ├── deal_scoring.py   # Explainable 0-100 deal scoring & factor engine
│   │   │   ├── risk_engine.py    # Phase 5: 5-category risk breakdown, simulator & data confidence
│   │   │   ├── benchmark_service.py # Phase 5: Regional benchmark querying & CSV ingestion
│   │   │   ├── pdf_report_service.py # Phase 6: 10-page A4 PDF report generator & headless Matplotlib
│   │   │   ├── ai_analysis_service.py # Grounded AI investment analysis, chat & comparisons
│   │   │   ├── ollama_service.py # Async Ollama integration, JSON enforcement & error recovery
│   │   │   ├── property_service.py # Financial calculations & search engine
│   │   │   ├── csv_service.py    # CSV validator & ingestion processor
│   │   │   └── seed_data.py      # 24 simulated Indian listings seeder
│   │   ├── utils/
│   │   │   └── financial.py      # INR formatting (Lakhs/Crores), yield & cash flow formulas
│   │   └── main.py               # FastAPI entry point, CORS, and lifespan init
│   ├── data/                     # SQLite database storage directory
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_health.py        # Health & diagnostic test suite (3 tests)
│   │   ├── test_properties.py    # CRUD, CSV, duplicate prevention & search (12 tests)
│   │   ├── test_financial_engine.py # Financial formulas, EMI, edge cases & comparison (16 tests)
│   │   ├── test_ai_service.py    # Ollama health, structured JSON, timeouts & chat tests (10 tests)
│   │   ├── test_risk_engine.py   # Phase 5: Risk analysis, What-if simulator & benchmarks (12 tests)
│   │   ├── test_pdf_reports.py   # Phase 6: PDF generation, MIME, 10-page layout & metadata (11 tests)
│   │   └── test_e2e_integration.py # Phase 7: End-to-end integration Cases A–J (10 tests)
│   ├── seed.py                   # Standalone CLI seeder script
│   ├── venv/                     # Python 3.12 virtual environment
│   ├── .env.example              # Backend environment template
│   ├── .env                      # Backend local environment configuration
│   ├── pytest.ini                # Pytest async configuration
│   └── requirements.txt          # Python dependencies
│
├── docs/                         # Architecture documentation
│   └── architecture.md
├── start_local.bat               # Windows 1-click startup launcher
├── start_local.ps1               # PowerShell startup script (prereq checks + dual servers)
├── .env.example                  # Root combined environment template
├── .gitignore                    # Git ignore file (venv, node_modules, .db, secrets)
└── README.md                     # Documentation & startup instructions
```

---

## 🚀 Quickstart Guide

### 1-Click Windows 11 Startup (Recommended)

Simply double-click `start_local.bat` or run in PowerShell:
```powershell
.\start_local.ps1
```
This automated script validates your Python 3.12+ and Node.js 18+ environments, checks Ollama connectivity on `http://127.0.0.1:11434`, launches the FastAPI backend on port 8000, launches the Next.js frontend on port 3000, and opens your default browser automatically.

---

### Manual Step-by-Step Startup

#### Step 1: Start Ollama (if not already running)

Ensure Ollama is running in the background:
```powershell
ollama list
```
Verify that `llama3.2:3b` appears in the list. If not installed:
```powershell
ollama pull llama3.2:3b
```

---

### Step 2: Start the Backend (FastAPI)

1. Open a terminal in the project root:
   ```powershell
   cd backend
   ```
2. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. (Optional) Populate the simulated demo catalog:
   ```powershell
   python seed.py
   ```
4. Start the FastAPI development server:
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
5. Test the API:
   - **Interactive API Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **Health Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
   - **AI Status Endpoint**: [http://127.0.0.1:8000/api/v1/ai/status](http://127.0.0.1:8000/api/v1/ai/status)
   - **Properties API**: [http://127.0.0.1:8000/api/v1/properties](http://127.0.0.1:8000/api/v1/properties)
   - **Financial Analysis API**: [http://127.0.0.1:8000/api/v1/analysis/1/calculate](http://127.0.0.1:8000/api/v1/analysis/1/calculate)
   - **Risk Evaluation API**: [http://127.0.0.1:8000/api/v1/risk/analyze](http://127.0.0.1:8000/api/v1/risk/analyze)
   - **What-If Simulator API**: [http://127.0.0.1:8000/api/v1/risk/simulate](http://127.0.0.1:8000/api/v1/risk/simulate)
   - **Regional Benchmarks API**: [http://127.0.0.1:8000/api/v1/benchmarks](http://127.0.0.1:8000/api/v1/benchmarks)
   - **PDF Report Stream**: [http://127.0.0.1:8000/api/v1/reports/1/pdf](http://127.0.0.1:8000/api/v1/reports/1/pdf)
   - **PDF Report Metadata**: [http://127.0.0.1:8000/api/v1/reports/1/preview?stream=false](http://127.0.0.1:8000/api/v1/reports/1/preview?stream=false)

---

### Step 3: Start the Frontend (Next.js)

1. Open a second terminal in the project root:
   ```powershell
   cd frontend
   ```
2. Start the Next.js development server:
   ```powershell
   npm run dev
   ```
3. Open your browser:
   - **Dashboard & Deal Intelligence**: [http://localhost:3000](http://localhost:3000)

---

## 🧪 Running Automated Tests

Run all 74 backend unit, financial, risk, AI, PDF, and end-to-end integration tests (Cases A–J):
```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/ -v
```

Run frontend TypeScript check and production build verification:
```powershell
cd frontend
npm run build
```

---

## 🔒 Security & Privacy

- **100% Free & Local-First**: No data leaves your machine. Deal information, financial models, and AI chat queries are computed 100% locally on Windows 11.
- **Strictly Local Storage**: Persistent data is maintained locally in SQLite (`backend/data/real_estate.db`).
- **Local-Only CORS Restriction**: Backend is configured to accept requests exclusively from trusted local origins (`http://localhost:3000`, `http://127.0.0.1:3000`).
- **CSV Formula Injection Defense**: Automated sanitization prepends single quotes to cell values beginning with `=`, `@`, `+`, `-`, tabs, or carriage returns.
- **Entity Size Limits**: CSV file imports enforce a 5 MB maximum size limit (`HTTP 413 CONTENT TOO LARGE`).
- **In-Memory PDF Generation**: Platypus PDF reports compile entirely in-memory (`io.BytesIO`) to prevent file residue or path traversal risks.
- **Traceable Formulas**: All yields, NOI, EMI, cash flow, and deal scoring are computed deterministically. Property appreciation is strictly separated from cash returns.
