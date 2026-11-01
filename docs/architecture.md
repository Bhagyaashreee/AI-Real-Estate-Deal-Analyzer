# System Architecture: AI Real Estate Deal Analyzer

## 1. High-Level Overview

The **AI Real Estate Deal Analyzer** is an offline-capable, privacy-respecting, locally running web application designed to evaluate Indian property investments.

```
+-------------------------------------------------------------+
|                     Next.js Frontend                        |
|   (TypeScript, Tailwind CSS, Recharts, Lucide Icons)        |
|                  http://localhost:3000                      |
+------------------------------+------------------------------+
                               |
                        REST / CORS
                               |
+------------------------------v------------------------------+
|                     FastAPI Backend                         |
|   (Python 3.12, Uvicorn, Pydantic, SQLAlchemy, ReportLab)   |
|                  http://127.0.0.1:8000                      |
+---------------+------------------------------+--------------+
                |                              |
         Local SQLite DB                Local Ollama Engine
  (backend/data/real_estate.db)      (http://127.0.0.1:11434)
                                         (llama3.2:3b)
```

## 2. Core Pillars

1. **100% Free & Local Execution**:
   - Zero paid API keys, zero cloud subscriptions.
   - All AI inferences run on local hardware using Ollama (`llama3.2:3b`).
   - SQLite for lightweight, zero-configuration local database persistence.

2. **Indian Real Estate Domain Specialization**:
   - Denominations in Lakhs (₹ L) and Crores (₹ Cr).
   - Metrics tailored to Indian market benchmarks (Gross Yield 2.5% - 5.5%, Net Yield, Price/sq.ft).
   - Major Tier-1 and Tier-2 hub coverage (Bengaluru, Mumbai, Hyderabad, Gurugram, Pune, Chennai, Guntur, Vijayawada, Visakhapatnam).

3. **Backend Service Layers**:
   - **`app/core`**: Configuration (`Settings`), database session management (`database.py`).
   - **`app/models`**: SQLAlchemy models (`property.py`, `benchmark.py`) with indexes on city, locality, price, area, yield, and property type.
   - **`app/schemas`**: Pydantic validation models for CRUD, search pagination, CSV import, financial analysis (`analysis.py`), AI intelligence (`ai.py`), risk modeling (`risk.py`), market benchmarking (`benchmark.py`), and PDF reports (`report.py`).
   - **`app/services`**:
     - `financial_engine.py`: Deterministic financial engine (Yields, Reducing-Balance EMI, NOI, Cash-on-Cash ROI, Break-Even, Sensitivity Scenarios).
     - `deal_scoring.py`: Transparent 0–100 deal scoring algorithm with configurable weights, factor analysis, and risk flagging.
     - `risk_engine.py`: Advanced risk engine with 5 distinct categories, 0–100 risk score, 6-scenario what-if simulation, and 0–100 data confidence engine.
     - `benchmark_service.py`: Market benchmark management, city/locality querying, matching engine, and CSV ingestion.
     - `pdf_report_service.py`: Professional 10-page A4 PDF investment report generation engine powered by ReportLab Platypus and headless Matplotlib.
     - `ai_analysis_service.py`: Grounded AI evaluation, structured verdict generation, risk intelligence explanation, and property chat.
     - `ollama_service.py`: Async Ollama integration (`llama3.2:3b`) with JSON grammar enforcement and graceful timeout/offline error handling.
     - `property_service.py`: Property catalog queries, filtering, and summary statistics.
     - `csv_service.py`: CSV import validation, error reporting, and duplicate prevention.
     - `seed_data.py`: Idempotent seeding of simulated Indian listings across 8 cities.
   - **`app/api`**: FastAPI route handlers versioned under `/api/v1` (`health.py`, `properties.py`, `analysis.py`, `ai.py`, `risk.py`, `benchmarks.py`, `reports.py`).
   - **`app/utils`**: Indian Rupee currency formatting (`format_inr`), financial calculations.

4. **Frontend Architecture**:
   - Next.js App Router with TypeScript and Tailwind CSS v4.
   - Dark SaaS theme (obsidian/slate) for financial analytics.
   - `FinancialAnalysisView`:
     - Live interactive controls (Down payment %, Interest rate %, Tenure, Vacancy %, Custom stamp duty/registration/brokerage/renovation).
     - 6 High-impact KPI cards (Gross Yield, Net Yield, Monthly Cash Flow, Cash-on-Cash ROI, EMI, Deal Score).
     - Recharts visualizations: Acquisition Cost Pie Chart and 5-Year Cumulative Cash Flow Projection Area Chart.
     - Scenario Testing & Stress Matrix (Conservative/Downturn, Base/Current, Best/Bull Market).
     - Positive Return Drivers, Risk Flags, and Metric Breakdown subscores.
     - Financial Transparency & Formula drawer with exact mathematical equations.
     - Side-by-side Multi-Property Deal Comparison tool (up to 4 properties) with comparative bar charts.
   - `RiskIntelligenceView` (Phase 5):
     - **Three Core Gauges**: Investment Attractiveness (0–100), Risk Exposure (0–100), and Data Confidence (0–100).
     - **5-Category Breakdown**: Financial Risk (30%), Loan Risk (25%), Rental Risk (20%), Data Reliability Risk (15%), External Verification Risk (10%).
     - **What-If Shock Simulator**: 6 Preconfigured scenarios (Conservative, Base, Optimistic, Rental Decline, Rate Hike, Extended Vacancy) + live custom simulation controls + Recharts comparative cash flow bar chart.
     - **Market Benchmarking**: City/locality alignment cards comparing property yield, rent, and price/sq.ft against regional benchmarks, plus benchmark directory table and CSV importer.
     - **AI Risk Advisor**: Local `llama3.2:3b` AI risk synthesis explaining leverage exposure, stress test resilience, and legal due diligence roadmap.
   - `AIDealAdvisor`:
     - Automated executive summary and 5-tier investment verdict (`Strong Potential`, `Potential with Caution`, `Weak Investment`, `High Risk`, `Insufficient Information`).
     - Three-tier risk analysis separating calculated numerical risks, information gaps, and external legal verification.
     - Interactive property chat assistant grounded strictly in verified financials with suggested follow-up prompts.
     - Multi-property AI comparative analysis explaining trade-offs.
   - `PdfReportsView` (Phase 6):
     - Interactive Investment Report Studio with real-time property selector.
     - Section toggles (Financials, Debt, 5-Category Risk, Benchmarks, Scenarios, AI Insights).
     - Underwriting parameter overrides (Down Payment %, Interest Rate %, Tenure, Vacancy %, Stamp Duty %).
     - Live embedded PDF preview viewer via responsive iframe.
     - Direct browser download and print action buttons.
     - Seamless fallback to deterministic financial analysis when Ollama is offline.
   - `PropertiesCatalog`: Interactive filtering, sorting, pagination, and grid/table view toggle.
   - `AddPropertyModal`: Form with live INR preview (Lakhs/Crores) and validation.
   - `PropertyDetailsModal`: Deep metadata inspection and financial breakdowns.
   - `CSVImportModal`: File upload, sample template downloader, and row-by-row error diagnostics.
   - `HealthBanner`: Live FastAPI + SQLite + Ollama diagnostic drawer.

---

## 3. Financial Mathematical Models

### A. Price Per Square Foot
$$\text{Price Per Sq Ft} = \frac{\text{Purchase Price (INR)}}{\text{Built-up Area (Sq Ft)}}$$

### B. Acquisition Cost Breakdown
$$\text{Total Acquisition Cost} = \text{Purchase Price} + \text{Stamp Duty} + \text{Registration} + \text{Brokerage} + \text{Renovation} + \text{Other Closing Costs}$$

### C. Reducing-Balance Loan EMI
$$\text{EMI} = \frac{P \cdot r \cdot (1 + r)^n}{(1 + r)^n - 1}$$
Where:
- $P = \text{Loan Principal} = \text{Purchase Price} \times (1 - \text{Down Payment Ratio})$
- $r = \frac{\text{Annual Interest Rate}}{12 \times 100}$ (Monthly interest rate)
- $n = \text{Tenure (Years)} \times 12$ (Total installments)

### D. Gross & Net Rental Yields
$$\text{Gross Rental Yield (\%)} = \left(\frac{\text{Annual Gross Rental Income}}{\text{Purchase Price}}\right) \times 100$$
$$\text{Net Rental Yield (\%)} = \left(\frac{\text{Annual Net Operating Income (NOI)}}{\text{Total Acquisition Cost}}\right) \times 100$$

### E. Monthly Net Cash Flow
$$\text{Monthly Net Cash Flow} = \text{Monthly NOI} - \text{Monthly Loan EMI}$$

### F. Cash-on-Cash Return (ROI)
$$\text{Cash-on-Cash ROI (\%)} = \left(\frac{\text{Annual Net Cash Flow}}{\text{Total Invested Capital}}\right) \times 100$$
Where $\text{Total Invested Capital} = \text{Down Payment} + \text{Total Closing Costs}$.

---

## 4. Local Ollama AI Integration Architecture (Phase 4)

### A. Grounding Principle
- All numerical metrics (yields, EMI, cash flow, ROI, score) are computed by the deterministic Python financial engine.
- The local LLM (`llama3.2:3b`) receives the exact verified metrics as structured context and is strictly instructed to explain and interpret without inventing or modifying numbers.
- If data points are missing (e.g. verified age, building approvals), the LLM explicitly marks them as unverified information gaps.

### B. Prompt Engineering & Optimization
- **Concise Context**: Prompt inputs are condensed into compact JSON to optimize local CPU inference time.
- **Structured JSON Mode**: Uses Ollama's native `format="json"` constraint to guarantee grammar-compliant JSON output without hallucinated formatting.
- **Three-Tier Risk Architecture**:
  1. *Category A*: Mathematically detected risks (negative cash flow, debt burden > 75%, compressed yields).
  2. *Category B*: Information gap risks (missing listing source, unverified society maintenance, unrecorded property age).
  3. *Category C*: Mandatory external verification (RERA registration, Occupancy Certificate, 30-year Encumbrance Certificate, structural audit).
- **Interactive Multi-Turn Chat**: Maintains recent conversation history while anchoring every answer in the property's financial parameters.

---

## 5. Advanced Risk Detection, What-If Simulation & Market Benchmarking (Phase 5)

### A. Tri-Score Investment Evaluation Model
The system mathematically distinguishes three independent evaluative dimensions:
1. **Investment Attractiveness Score (0–100, Higher = Better)**: Measures capitalization efficiency, net rental yield buffer, and cash-on-cash ROI.
2. **Risk Exposure Score (0–100, Higher = Riskier)**: Measures leverage debt burden, interest rate sensitivity, operating expense overhead, and downside vulnerability.
3. **Data Confidence Score (0–100, Higher = More Reliable)**: Measures source provenance, metadata completeness, property age verification, and regional benchmark alignment. A listing URL is treated merely as a source locator, never as verified legal authenticity.

### B. Explainable 5-Category Risk Formulation
The overall Risk Score is computed deterministically:
$$\text{Risk Score} = 0.30 \cdot R_{\text{Financial}} + 0.25 \cdot R_{\text{Loan}} + 0.20 \cdot R_{\text{Rental}} + 0.15 \cdot R_{\text{Data}} + 0.10 \cdot R_{\text{Legal}}$$
- **Financial Risk ($R_{\text{Financial}}$)**: Cash flow deficit, gross yield $< 3\%$, net yield $< 2\%$, expense-to-rent ratio $> 20\%$.
- **Loan Risk ($R_{\text{Loan}}$)**: Loan-to-Value (LTV) $> 80\%$, Debt-Service Coverage (DSCR) / EMI-to-rent $> 75\%$, vulnerability to +200 bps interest rate hikes.
- **Rental Risk ($R_{\text{Rental}}$)**: Vacancy allowance $> 10\%$, sensitivity to 10% rent deflation, high maintenance expense inflation.
- **Data Reliability Risk ($R_{\text{Data}}$)**: Missing listing sources, unverified society fees, missing property age, missing source URLs.
- **External Verification Risk ($R_{\text{Legal}}$)**: Pending RERA registration, pending encumbrance certificate (EC), missing occupancy certificate (OC), unverified title deeds.

### C. Six-Scenario What-If Shock Matrix
The what-if simulator stress tests each asset under six preconfigured market regimes:
1. **Conservative (Downturn)**: Rent -10%, Vacancy 10%, Maintenance +15%, Interest +1.0%.
2. **Base (Current)**: Stated property inputs with standard 5% vacancy and 8.5% interest.
3. **Optimistic (Bull)**: Rent +8%, Vacancy 3%, Maintenance -5%, Interest -0.5%.
4. **Rental Decline Shock**: Rent -15%, Vacancy 8%, standard rates.
5. **Rate Hike Shock**: Interest +2.5% (simulating aggressive RBI repo tightening), standard rent.
6. **Extended Vacancy Shock**: Vacancy 20% (2.4 months unrented per year), standard rates.

### D. Market Benchmarking & Provenance
- Persistent regional benchmarks stored in SQLite (`market_benchmarks` table) indexed by `city`, `locality`, and `property_type`.
- Includes historical average yields (2.5% to 5.5%), average price/sq.ft, average monthly rents, and provenance metadata (`source_organization`, `sample_size`, `last_updated_date`).
- Automatic property matching query dynamically calculates market deltas:
  $$\Delta \text{Yield} = \text{Property Yield} - \text{Benchmark Yield}$$
  $$\Delta \text{Price/SqFt} = \text{Property Price/SqFt} - \text{Benchmark Price/SqFt}$$

---

## 6. Professional PDF Investment Report Generation Architecture (Phase 6)

### A. Document Engine Principles
- **ReportLab Platypus**: Flowable-based layout ensuring deterministic page budgets and clean text wrapping without clipping.
- **Two-Pass `NumberedCanvas`**: Computes total page count across the document to render running headers and footers ("Page X of 10") alongside ISO generation timestamps.
- **Headless Matplotlib Visualizations**: Renders multi-scenario monthly cash flow bar charts in dark slate styling, saving directly into memory buffers without GUI dependencies.
- **Pure In-Memory Generation**: All PDF generation operates using `io.BytesIO()`, ensuring zero lingering temporary files on the local filesystem.

### B. Standardized 10-Page Investment Report Blueprint
1. **Page 1: Cover Page**: Brand banner, property title, micro-market coordinates, large Tri-Score cards (Investment Attractiveness, Risk Exposure, Data Confidence), and statutory disclaimer.
2. **Page 2: Executive Investment Summary**: Algorithmic investment verdict badge, executive summary narrative, financial strengths, vulnerabilities, and underwriting assumptions.
3. **Page 3: Property Overview**: Complete physical and listing specification table (BHK, baths, built-up area, stated age, pricing, catalog provenance, and demo data status).
4. **Page 4: Financial Analysis**: 4 Core KPI cards (Gross Yield, Net Yield, Cash Flow, CoC ROI), monthly/annual operating statement (EGI, NOI, Debt Service), and acquisition closing cost schedule.
5. **Page 5: Loan & EMI Analysis**: Reducing-balance loan terms, 5-year illustrative amortization schedule, debt-service coverage ratio (DSCR), and debt exposure.
6. **Page 6: Risk Intelligence**: Overall risk score, 5-category decomposition table with weights and observations, critical red flags, and investor mitigations.
7. **Page 7: Market Benchmarking**: Property vs. localized micro-market averages, yield delta, price/sq.ft delta, and survey provenance disclosures.
8. **Page 8: Scenario Analysis**: 6-regime stress test matrix (Conservative, Base, Optimistic, Rent Decline, Rate Hike, Extended Vacancy), break-even rents, and embedded Matplotlib comparison chart.
9. **Page 9: AI Investment Insights**: Local AI synthesized recommendations (or deterministic offline fallback), and a 5-step legal/physical due-diligence roadmap.
10. **Page 10: Disclaimer & Methodology**: Exact mathematical formulas, methodological constraints, and mandatory statutory legal disclaimers.
