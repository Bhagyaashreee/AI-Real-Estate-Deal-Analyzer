import io
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.models.property import Property
from app.core.database import SessionLocal

client = TestClient(app)


# ----------------------------------------------------------------------
# 1. Advanced Risk Engine & Scoring Tests
# ----------------------------------------------------------------------

def test_analyze_property_risk_success():
    """Verify multi-dimensional risk evaluation endpoint."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    res = client.post(f"/api/v1/risk/{prop_id}/analyze")
    assert res.status_code == 200
    data = res.json()

    assert data["property_id"] == prop_id
    assert 0 <= data["risk_exposure_score"] <= 100
    assert 0 <= data["investment_attractiveness_score"] <= 100
    assert 0 <= data["data_confidence_score"] <= 100
    assert data["overall_risk_level"] in [
        "Low Risk",
        "Moderate Risk",
        "Elevated Risk",
        "High Risk",
        "Critical Risk",
    ]

    # Verify 5 distinct category subscores exist
    assert "categories" in data
    cats = data["categories"]
    assert "financial" in cats
    assert "loan" in cats
    assert "rental" in cats
    assert "data_reliability" in cats
    assert "external_verification" in cats

    # Verify factors and mitigations are lists
    assert len(cats["financial"]["factors"]) > 0
    assert len(cats["loan"]["factors"]) > 0
    assert len(cats["external_verification"]["mitigation_steps"]) > 0
    assert "disclaimer" in data


def test_analyze_risk_nonexistent_property():
    """Nonexistent property should return HTTP 404."""
    res = client.post("/api/v1/risk/999999/analyze")
    assert res.status_code == 404


def test_data_confidence_endpoint():
    """Verify independent data confidence score and reasons."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    # Test via direct endpoint alias
    res = client.get(f"/api/v1/data-confidence/{prop_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["property_id"] == prop_id
    assert 0 <= data["confidence_score"] <= 100
    assert data["confidence_level"] in [
        "High Confidence",
        "Moderate Confidence",
        "Low Confidence",
        "Unverified",
    ]
    assert len(data["positive_signals"]) > 0 or len(data["missing_elements"]) > 0
    assert "benchmark_status" in data


# ----------------------------------------------------------------------
# 2. What-If Simulator Tests
# ----------------------------------------------------------------------

def test_what_if_simulation_standard_scenarios():
    """Verify 6 standard stress-test scenarios."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    res = client.post(f"/api/v1/risk/{prop_id}/simulate")
    assert res.status_code == 200
    data = res.json()

    assert data["property_id"] == prop_id
    assert "base_case" in data
    assert len(data["scenarios"]) == 6

    # Verify specific shock scenarios are present
    scenario_ids = [s["scenario_id"] for s in data["scenarios"]]
    assert "base" in scenario_ids
    assert "conservative" in scenario_ids
    assert "optimistic" in scenario_ids
    assert "rental_decline" in scenario_ids
    assert "rate_hike" in scenario_ids
    assert "extended_vacancy" in scenario_ids

    # Rate hike scenario should have higher interest rate and EMI than base
    base = next(s for s in data["scenarios"] if s["scenario_id"] == "base")
    rate_hike = next(s for s in data["scenarios"] if s["scenario_id"] == "rate_hike")
    assert rate_hike["interest_rate_pct"] > base["interest_rate_pct"]
    assert rate_hike["monthly_emi_inr"] > base["monthly_emi_inr"]

    # Rental decline scenario should have lower rent and net cash flow
    rent_drop = next(s for s in data["scenarios"] if s["scenario_id"] == "rental_decline")
    assert rent_drop["monthly_rent_inr"] < base["monthly_rent_inr"]
    assert rent_drop["monthly_cash_flow_inr"] < base["monthly_cash_flow_inr"]


def test_what_if_simulation_custom_override():
    """Verify user custom override simulation parameters."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    custom_payload = {
        "purchase_price_inr": 12000000.0,
        "expected_monthly_rent_inr": 60000.0,
        "vacancy_rate_pct": 10.0,
        "annual_interest_rate_pct": 9.0,
        "down_payment_pct": 30.0,
        "tenure_years": 15,
    }

    res = client.post(f"/api/v1/risk/{prop_id}/simulate", json=custom_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["custom_simulation"] is not None
    custom = data["custom_simulation"]
    assert custom["purchase_price_inr"] == 12000000.0
    assert custom["monthly_rent_inr"] == 60000.0
    assert custom["down_payment_pct"] == 30.0
    assert custom["interest_rate_pct"] == 9.0
    assert custom["tenure_years"] == 15


def test_compare_scenarios_across_properties():
    """Verify comparing scenarios across up to 4 properties."""
    list_res = client.get("/api/v1/properties?page=1&page_size=2")
    items = list_res.json()["items"]
    ids = [p["id"] for p in items[:2]]

    res = client.post("/api/v1/risk/compare-scenarios", json={"property_ids": ids})
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == len(ids)
    assert len(data["properties"]) == len(ids)


# ----------------------------------------------------------------------
# 3. Market Benchmarking Tests
# ----------------------------------------------------------------------

def test_list_benchmarks_and_provenance():
    """Verify listing benchmarks and provenance count separation."""
    res = client.get("/api/v1/benchmarks?page=1&page_size=20")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 15
    assert len(data["items"]) >= 15
    assert "provenance_summary" in data

    # Check provenance counts
    prov = data["provenance_summary"]
    assert "simulated_demo" in prov or "user_submitted" in prov


def test_benchmark_match_endpoint():
    """Verify finding matching benchmark for a city and locality."""
    res = client.get("/api/v1/benchmarks/match?city=Bengaluru&locality=Whitefield&property_type=Apartment")
    assert res.status_code == 200
    data = res.json()
    assert data is not None
    assert data["city"] == "Bengaluru"
    assert data["locality"] == "Whitefield"
    assert data["avg_price_per_sqft"] > 0
    assert data["avg_gross_rental_yield_pct"] > 0


def test_benchmark_match_insufficient_data():
    """Verify returning null without fabricating numbers for an unmapped city."""
    res = client.get("/api/v1/benchmarks/match?city=NonexistentCityXYZ&locality=UnknownZone")
    assert res.status_code == 200
    assert res.json() is None


def test_create_benchmark_manually():
    """Verify manual benchmark creation."""
    payload = {
        "city": "TestCity",
        "locality": "TechZone Sector 1",
        "property_type": "Apartment",
        "avg_price_per_sqft": 7500.0,
        "min_price_per_sqft": 6500.0,
        "max_price_per_sqft": 8500.0,
        "avg_monthly_rent_inr": 32000.0,
        "avg_gross_rental_yield_pct": 4.50,
        "data_source": "Brokerage Field Survey",
        "collection_date": "2026-Q1",
        "verification_status": "user_submitted",
        "is_demo": False,
        "notes": "Verified through 5 recent registration deeds.",
    }
    res = client.post("/api/v1/benchmarks", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["id"] is not None
    assert data["city"] == "TestCity"
    assert data["verification_status"] == "user_submitted"
    assert data["is_demo"] is False


def test_import_benchmarks_csv():
    """Verify CSV import of benchmarks with column validation."""
    csv_content = (
        "city,locality,property_type,avg_price_per_sqft,min_price_per_sqft,max_price_per_sqft,avg_monthly_rent_inr,avg_gross_rental_yield_pct,data_source,collection_date,verification_status,is_demo\n"
        "Pune,Baner,Apartment,9500,8200,11000,38000,4.20,Local Survey 2026,2026-Q1,verified_market,false\n"
        "Hyderabad,Nanakramguda,Apartment,10500,9000,12500,48000,4.40,Cyberabad Index,2026-Q1,verified_market,false\n"
    )
    files = {"file": ("benchmarks.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/benchmarks/import-csv", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["successful_imports"] == 2
    assert data["failed_rows"] == 0


# ----------------------------------------------------------------------
# 4. AI Risk Explanation Test
# ----------------------------------------------------------------------

def test_ai_risk_explain_endpoint():
    """Verify AI risk explanation with mocked Ollama inference."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    mock_ai_risk = {
        "executive_risk_summary": "Overall risk is moderate. The property exhibits attractive rental yields but is exposed to interest rate spikes.",
        "biggest_risks": ["Interest rate sensitivity under floating loans", "High acquisition stamp duty"],
        "sensitive_assumptions": ["Stable tenant occupancy without extended vacancy", "8.5% interest rate cap"],
        "downside_scenarios_interpretation": "A 2% interest rate hike would reduce monthly cash flow from positive to near-neutral.",
        "data_verification_checklist": ["Verify 30-year Encumbrance Certificate", "Check RERA registration"],
        "benchmark_comparison_analysis": "Gross yield of 4.30% aligns closely with the micro-market benchmark of 4.25%.",
    }

    with patch(
        "app.services.ollama_service.ollama_service.generate_json",
        new_callable=AsyncMock,
    ) as mock_gen_json, patch(
        "app.services.ollama_service.ollama_service.verify_model_available",
        new_callable=AsyncMock,
    ):
        mock_gen_json.return_value = {
            "data": mock_ai_risk,
            "total_duration_ms": 950.0,
            "model": "llama3.2:3b",
        }

        res = client.post(f"/api/v1/risk/{prop_id}/ai-explain")
        assert res.status_code == 200
        data = res.json()
        assert data["property_id"] == prop_id
        assert "executive_risk_summary" in data
        assert len(data["biggest_risks"]) >= 2
        assert len(data["data_verification_checklist"]) >= 2
        assert "disclaimer" in data
