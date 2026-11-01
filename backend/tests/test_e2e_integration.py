import io
import re
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.property import Property
from app.models.benchmark import MarketBenchmark
from app.services.ollama_service import OllamaConnectionError
from app.services.financial_engine import (
    financial_engine,
    AcquisitionCostInputs,
    LoanInputs,
    OperatingExpenseInputs,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_e2e_test_data():
    """Ensure all test properties created during E2E runs are cleanly removed."""
    db = SessionLocal()
    try:
        db.query(Property).filter(
            (Property.title.like("E2E %"))
            | (Property.title.like("Test %"))
            | (Property.title.like("%calc%"))
            | (Property.title.like("%cmd%"))
            | (Property.title.like("%Formula%"))
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(Property).filter(
            (Property.title.like("E2E %"))
            | (Property.title.like("Test %"))
            | (Property.title.like("%calc%"))
            | (Property.title.like("%cmd%"))
            | (Property.title.like("%Formula%"))
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


# ==============================================================================
# CASE A: Seeded Demo Property Full Analytical Audit
# ==============================================================================
def test_case_a_demo_property_complete_audit():
    """Verify demo property retrieval, metrics, risk audit, and PDF metadata generation."""
    # 1. Fetch demo property
    list_res = client.get("/api/v1/properties?is_demo=true&page=1&page_size=1")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) >= 1, "Expected at least one seeded demo property"
    demo_prop = items[0]
    prop_id = demo_prop["id"]

    assert demo_prop["is_demo"] is True
    assert "₹" in demo_prop["price_formatted"]
    assert "₹" in demo_prop["rent_formatted"]
    assert demo_prop["price_per_sqft"] > 0
    assert demo_prop["gross_rental_yield_pct"] > 0

    # 2. Run deterministic financial calculation
    fin_res = client.post(
        f"/api/v1/analysis/{prop_id}/calculate",
        json={"down_payment_pct": 20.0, "annual_interest_rate_pct": 8.5, "tenure_years": 20},
    )
    assert fin_res.status_code == 200
    fin_data = fin_res.json()
    assert "acquisition_costs" in fin_data
    assert "loan_metrics" in fin_data
    assert "returns" in fin_data
    assert "deal_score" in fin_data
    assert fin_data["loan_metrics"]["monthly_emi_inr"] > 0

    # 3. Run multi-dimensional risk evaluation
    risk_res = client.post(f"/api/v1/risk/{prop_id}/analyze")
    assert risk_res.status_code == 200
    risk_data = risk_res.json()
    assert risk_data["property_id"] == prop_id
    assert 0 <= risk_data["risk_exposure_score"] <= 100
    assert 0 <= risk_data["investment_attractiveness_score"] <= 100
    assert 0 <= risk_data["data_confidence_score"] <= 100
    assert len(risk_data["categories"]) == 5

    # 4. Generate PDF report metadata
    rep_res = client.post(
        f"/api/v1/reports/{prop_id}/generate",
        json={"include_ai": False, "return_pdf_direct": False},
    )
    assert rep_res.status_code == 200
    rep_meta = rep_res.json()
    assert rep_meta["property_id"] == prop_id
    assert rep_meta["page_count"] == 10
    assert rep_meta["file_size_bytes"] > 10000
    assert f"DealAnalyzer_Report_Prop_{prop_id}" in rep_meta["file_name"]


# ==============================================================================
# CASE B: Manually Entered User Property Full Lifecycle
# ==============================================================================
def test_case_b_manually_entered_property_lifecycle():
    """Verify manual creation, calculation, updates, filtering, and deletion of a user property."""
    payload = {
        "title": "E2E User Luxury Penthouse Indiranagar",
        "city": "Bengaluru",
        "locality": "Indiranagar",
        "state": "Karnataka",
        "property_type": "Apartment",
        "bedrooms": 4,
        "bathrooms": 4,
        "built_up_area_sqft": 3000.0,
        "purchase_price_inr": 35000000.0,
        "expected_monthly_rent_inr": 120000.0,
        "monthly_maintenance_inr": 8000.0,
        "property_age": "2 years",
        "listing_source": "Direct Owner",
        "source_url": "https://example.com/listings/penthouse-3000",
        "is_demo": False,
    }

    # 1. Create property
    create_res = client.post("/api/v1/properties", json=payload)
    assert create_res.status_code == 201
    created_prop = create_res.json()
    prop_id = created_prop["id"]
    assert created_prop["is_demo"] is False
    assert created_prop["title"] == payload["title"]
    assert created_prop["price_per_sqft"] == round(35000000.0 / 3000.0, 2)

    # 2. Update rent and maintenance
    update_res = client.put(
        f"/api/v1/properties/{prop_id}",
        json={"expected_monthly_rent_inr": 135000.0, "monthly_maintenance_inr": 9000.0},
    )
    assert update_res.status_code == 200
    updated_prop = update_res.json()
    assert updated_prop["expected_monthly_rent_inr"] == 135000.0
    # Gross yield = (135000 * 12 / 35000000) * 100 = 4.63%
    assert updated_prop["gross_rental_yield_pct"] == round((135000.0 * 12 / 35000000.0) * 100, 2)

    # 3. Filter and search
    search_res = client.get("/api/v1/properties?city=Bengaluru&search=Indiranagar")
    assert search_res.status_code == 200
    found_ids = [p["id"] for p in search_res.json()["items"]]
    assert prop_id in found_ids

    # 4. Clean deletion
    del_res = client.delete(f"/api/v1/properties/{prop_id}")
    assert del_res.status_code == 200
    get_res = client.get(f"/api/v1/properties/{prop_id}")
    assert get_res.status_code == 404


# ==============================================================================
# CASE C: Incomplete Property with Missing Optional Details
# ==============================================================================
def test_case_c_incomplete_property_missing_optional_details():
    """Verify system handles missing optional fields gracefully and elevates data reliability risk."""
    payload = {
        "title": "E2E Sparse Property Hyderabad",
        "city": "Hyderabad",
        "locality": "Kukatpally",
        "state": "Telangana",
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "built_up_area_sqft": 1100.0,
        "purchase_price_inr": 6500000.0,
        "expected_monthly_rent_inr": 22000.0,
        "monthly_maintenance_inr": 0.0,
        "property_age": None,
        "listing_source": None,
        "source_url": None,
        "is_demo": False,
    }
    create_res = client.post("/api/v1/properties", json=payload)
    assert create_res.status_code == 201
    prop_id = create_res.json()["id"]

    try:
        # Evaluate risk
        risk_res = client.post(f"/api/v1/risk/{prop_id}/analyze")
        assert risk_res.status_code == 200
        risk_data = risk_res.json()

        # Data reliability risk must identify missing source URL and property age
        data_cat = risk_data["categories"]["data_reliability"]
        factors_str = " ".join(data_cat["factors"]).lower()
        assert "url" in factors_str or "unspecified" in factors_str or "age" in factors_str
        assert data_cat["score"] >= 40.0
    finally:
        client.delete(f"/api/v1/properties/{prop_id}")


# ==============================================================================
# CASE D: Cash-Only Purchase (0% Loan / 100% Down Payment)
# ==============================================================================
def test_case_d_cash_only_purchase():
    """Verify 100% down payment (cash purchase) produces 0 EMI, positive cash flow, and avoids ZeroDivisionError."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    res = client.post(
        f"/api/v1/analysis/{prop_id}/calculate",
        json={"down_payment_pct": 100.0, "annual_interest_rate_pct": 8.5, "tenure_years": 20},
    )
    assert res.status_code == 200
    data = res.json()

    loan = data["loan_metrics"]
    assert loan["loan_principal_inr"] == 0.0
    assert loan["monthly_emi_inr"] == 0.0
    assert loan["is_cash_purchase"] is True

    returns = data["returns"]
    op = data["operating_finances"]
    # With 0 EMI, monthly net cash flow must equal monthly NOI
    assert returns["monthly_net_cash_flow_inr"] == op["monthly_noi_inr"]
    assert returns["monthly_net_cash_flow_inr"] > 0


# ==============================================================================
# CASE E: Standard Home Loan Purchase Amortization & Formula Audit
# ==============================================================================
def test_case_e_standard_loan_purchase_math_audit():
    """Audit mathematical rigor of reducing-balance EMI and Cash-on-Cash formulas."""
    purchase_price = 10000000.0  # 1 Crore
    down_payment_pct = 20.0
    annual_rate = 8.5
    tenure_years = 20

    loan_calc = financial_engine.calculate_loan_emi(
        LoanInputs(
            purchase_price_inr=purchase_price,
            down_payment_pct=down_payment_pct,
            annual_interest_rate_pct=annual_rate,
            tenure_years=tenure_years,
        )
    )

    expected_principal = 8000000.0  # 80 Lakhs
    assert loan_calc["loan_principal_inr"] == expected_principal

    # Exact EMI verification: P * r * (1+r)^n / ((1+r)^n - 1)
    monthly_r = (annual_rate / 12.0) / 100.0
    n = tenure_years * 12
    cf = (1.0 + monthly_r) ** n
    expected_emi = round(expected_principal * monthly_r * cf / (cf - 1.0), 2)
    assert abs(loan_calc["monthly_emi_inr"] - expected_emi) < 0.05

    # Returns verification
    annual_gross_rent = 480000.0  # 40k/mo
    annual_noi = 420000.0  # after maintenance/vacancy
    closing_costs = 700000.0  # 7% stamp duty

    returns = financial_engine.calculate_investment_returns(
        purchase_price_inr=purchase_price,
        total_acquisition_cost_inr=purchase_price + closing_costs,
        down_payment_inr=2000000.0,
        total_closing_costs_inr=closing_costs,
        monthly_emi_inr=expected_emi,
        annual_gross_rent_inr=annual_gross_rent,
        annual_noi_inr=annual_noi,
    )

    expected_annual_debt = round(expected_emi * 12, 2)
    expected_net_cf = round(annual_noi - expected_annual_debt, 2)
    assert abs(returns["annual_net_cash_flow_inr"] - expected_net_cf) < 0.1

    # Cash-on-Cash ROI = Net cash flow / (Down payment + closing costs)
    invested_capital = 2000000.0 + closing_costs
    expected_coc = round((expected_net_cf / invested_capital) * 100.0, 2)
    assert abs(returns["cash_on_cash_roi_pct"] - expected_coc) < 0.1


# ==============================================================================
# CASE F: High-Cost Low-Rent Property with Severe Negative Cash Flow
# ==============================================================================
def test_case_f_negative_monthly_cash_flow_detection():
    """Verify that an overpriced property with high debt triggers negative cash flow warnings and red flags."""
    payload = {
        "title": "E2E Overpriced Property Negative Cashflow",
        "city": "Mumbai",
        "locality": "Worli",
        "state": "Maharashtra",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 1600.0,
        "purchase_price_inr": 35000000.0,  # 3.5 Crore
        "expected_monthly_rent_inr": 35000.0,  # Only 35k rent (1.2% gross yield)
        "monthly_maintenance_inr": 12000.0,
        "property_age": "5 years",
        "listing_source": "Broker",
        "is_demo": False,
    }
    create_res = client.post("/api/v1/properties", json=payload)
    assert create_res.status_code == 201
    prop_id = create_res.json()["id"]

    try:
        # Calculate finances with 80% loan
        fin_res = client.post(
            f"/api/v1/analysis/{prop_id}/calculate",
            json={"down_payment_pct": 20.0, "annual_interest_rate_pct": 8.5, "tenure_years": 20},
        )
        assert fin_res.status_code == 200
        fin_data = fin_res.json()
        monthly_cf = fin_data["returns"]["monthly_net_cash_flow_inr"]
        assert monthly_cf < -100000.0, "Monthly cash flow should be severely negative"

        # Risk Engine assessment
        risk_res = client.post(f"/api/v1/risk/{prop_id}/analyze")
        assert risk_res.status_code == 200
        risk_data = risk_res.json()
        assert risk_data["categories"]["financial"]["score"] >= 60.0
        assert len(risk_data["critical_red_flags"]) >= 1
        flags_str = " ".join(risk_data["critical_red_flags"]).lower()
        assert "negative" in flags_str or "drain" in flags_str
    finally:
        client.delete(f"/api/v1/properties/{prop_id}")


# ==============================================================================
# CASE G: Property Without Matching Locality Market Benchmarks
# ==============================================================================
def test_case_g_unbenchmarked_locality_fallback():
    """Verify that a property in an unbenchmarked tier-3 locality falls back gracefully without error."""
    # 1. Direct benchmark query for non-existent city returns null with 200 OK
    bench_res = client.get("/api/v1/benchmarks/match?city=Shillong&locality=PoliceBazar")
    assert bench_res.status_code == 200
    assert bench_res.json() is None

    # 2. Property in unbenchmarked locality can still be analyzed for risk
    payload = {
        "title": "E2E Unbenchmarked Locality Villa",
        "city": "Shillong",
        "locality": "PoliceBazar",
        "state": "Meghalaya",
        "property_type": "Independent House",
        "bedrooms": 3,
        "bathrooms": 2,
        "built_up_area_sqft": 1800.0,
        "purchase_price_inr": 8500000.0,
        "expected_monthly_rent_inr": 30000.0,
        "monthly_maintenance_inr": 2000.0,
        "is_demo": False,
    }
    create_res = client.post("/api/v1/properties", json=payload)
    assert create_res.status_code == 201
    prop_id = create_res.json()["id"]

    try:
        risk_res = client.post(f"/api/v1/risk/{prop_id}/analyze")
        assert risk_res.status_code == 200
        risk_data = risk_res.json()
        # Should complete successfully, data confidence notes lack of benchmark data
        assert 0 <= risk_data["data_confidence_score"] <= 100
        assert len(risk_data["data_confidence_reasons"]) >= 1
    finally:
        client.delete(f"/api/v1/properties/{prop_id}")


# ==============================================================================
# CASE H: Ollama Offline / Connection Failure Fallback
# ==============================================================================
def test_case_h_ollama_offline_fallback():
    """Verify robust offline fallback when local Ollama daemon is unreachable."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    # 1. Status reports offline cleanly
    with patch(
        "app.services.ollama_service.ollama_service.check_health",
        new_callable=AsyncMock,
    ) as mock_health:
        mock_health.return_value = {
            "status": "offline",
            "base_url": "http://127.0.0.1:11434",
            "target_model": "llama3.2:3b",
            "model_ready": False,
            "installed_models": [],
            "error": "Connection refused at 127.0.0.1:11434",
            "guidance": "Start Ollama locally: 'ollama serve'",
        }
        status_res = client.get("/api/v1/ai/status")
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "offline"
        assert status_res.json()["inference_ready"] is False

    # 2. AI analyze endpoint returns HTTP 503 with helpful offline message
    with patch(
        "app.services.ollama_service.ollama_service.generate_json",
        new_callable=AsyncMock,
        side_effect=OllamaConnectionError("Connection refused at port 11434"),
    ):
        ai_res = client.post(f"/api/v1/ai/analyze/{prop_id}")
        assert ai_res.status_code == 503
        assert "offline" in ai_res.json()["detail"].lower()

    # 3. PDF report generation with include_ai=True must NOT crash when Ollama is offline
    with patch(
        "app.services.ollama_service.ollama_service.generate_json",
        new_callable=AsyncMock,
        side_effect=OllamaConnectionError("Connection refused at port 11434"),
    ):
        pdf_res = client.post(
            f"/api/v1/reports/{prop_id}/generate",
            json={"include_ai": True, "return_pdf_direct": True},
        )
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert pdf_res.content.startswith(b"%PDF-")


# ==============================================================================
# CASE I: PDF Report Generation With AI Enabled vs AI Disabled
# ==============================================================================
def test_case_i_pdf_generation_ai_toggle_comparison():
    """Verify both AI-enabled and deterministic PDF reports generate exact 10 pages without errors."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    # 1. AI Disabled
    pdf_no_ai = client.post(
        f"/api/v1/reports/{prop_id}/generate",
        json={"include_ai": False, "return_pdf_direct": True},
    )
    assert pdf_no_ai.status_code == 200
    assert pdf_no_ai.content.startswith(b"%PDF-")
    pages_no_ai = len(re.findall(rb"/Type\s*/Page[^s]", pdf_no_ai.content))
    assert pages_no_ai == 10

    # 2. AI Enabled (with mocked LLM response)
    from tests.test_ai_service import MOCK_AI_STRUCTURED_RESPONSE

    with patch(
        "app.services.ollama_service.ollama_service.generate_json",
        new_callable=AsyncMock,
    ) as mock_gen_json, patch(
        "app.services.ollama_service.ollama_service.verify_model_available",
        new_callable=AsyncMock,
    ):
        mock_gen_json.return_value = {
            "data": MOCK_AI_STRUCTURED_RESPONSE,
            "total_duration_ms": 950.0,
            "model": "llama3.2:3b",
        }

        pdf_ai = client.post(
            f"/api/v1/reports/{prop_id}/generate",
            json={"include_ai": True, "return_pdf_direct": True},
        )
        assert pdf_ai.status_code == 200
        assert pdf_ai.content.startswith(b"%PDF-")
        pages_ai = len(re.findall(rb"/Type\s*/Page[^s]", pdf_ai.content))
        assert pages_ai == 10


# ==============================================================================
# CASE J: CSV Import Security & Validation Audit
# ==============================================================================
def test_case_j_csv_import_security_and_validation():
    """Verify CSV formula injection sanitization, invalid row rejection, and 5MB size limit."""
    # 1. Formula injection & invalid row CSV content
    csv_content = (
        "title,city,locality,state,property_type,bedrooms,bathrooms,built_up_area_sqft,purchase_price_inr,expected_monthly_rent_inr,monthly_maintenance_inr,property_age,listing_source,source_url\n"
        # Row 1: Valid clean property
        "E2E CSV Clean Villa,Chennai,Adyar,Tamil Nadu,Villa,4,4,2800,28000000,90000,6000,3 years,Portal,https://example.com/adyar\n"
        # Row 2: Formula injection in title (=cmd|' /C calc'!A0)
        "=cmd|'/c calc'!A1,Bengaluru,Whitefield,Karnataka,Apartment,3,3,1500,12000000,45000,3500,1 year,Direct,https://example.com/wf\n"
        # Row 3: Formula injection in source_url (@SUM(1+1))
        "E2E Formula URL Flat,Pune,Baner,Maharashtra,Apartment,2,2,1000,8000000,28000,2500,2 years,Portal,@SUM(1+1)\n"
        # Row 4: Invalid negative price
        "E2E Invalid Row,Kolkata,Salt Lake,West Bengal,Apartment,2,2,900,-5000000,18000,1500,4 years,Direct,https://example.com/sl\n"
    )

    file_obj = io.BytesIO(csv_content.encode("utf-8"))
    upload_res = client.post(
        "/api/v1/properties/import-csv",
        files={"file": ("test_e2e_import.csv", file_obj, "text/csv")},
    )
    assert upload_res.status_code == 200
    import_result = upload_res.json()

    # Row 1, 2, 3 should succeed (sanitized), Row 4 should fail due to negative price
    assert import_result["successful_imports"] >= 2
    assert len(import_result["errors"]) >= 1
    assert any("price" in err["error"].lower() or "positive" in err["error"].lower() for err in import_result["errors"])

    # Verify formula injection was sanitized in DB
    db = SessionLocal()
    try:
        # Check title starting with = was escaped with single quote '
        injected = db.query(Property).filter(Property.city == "Bengaluru", Property.locality == "Whitefield").first()
        if injected:
            assert injected.title.startswith("'") or not injected.title.startswith("=")
    finally:
        db.close()

    # 2. Test 5 MB size limit enforcement
    large_bytes = b"title,city\n" + b"X" * (5 * 1024 * 1024 + 100)
    large_file = io.BytesIO(large_bytes)
    large_res = client.post(
        "/api/v1/properties/import-csv",
        files={"file": ("too_large.csv", large_file, "text/csv")},
    )
    assert large_res.status_code == 413
    assert "5 MB" in large_res.json()["detail"]
