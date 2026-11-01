import re
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.property import Property
from app.models.benchmark import MarketBenchmark
from app.services.pdf_report_service import pdf_report_service
from app.services.ai_analysis_service import ai_analysis_service

client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def test_property(db_session):
    prop = db_session.query(Property).first()
    assert prop is not None, "At least one property must be seeded in the test database"
    return prop


def test_pdf_report_service_direct_generation(test_property):
    """Verify that pdf_report_service generates valid PDF bytes directly with %PDF header."""
    pdf_bytes = pdf_report_service.generate_pdf_report(prop=test_property)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 10000, "PDF size should be substantial for a 10-page document"
    assert pdf_bytes.startswith(b"%PDF-"), "Generated document must have valid PDF magic signature"


def test_pdf_report_page_count_is_exact_ten(test_property):
    """Verify that every generated PDF report contains exactly 10 pages."""
    pdf_bytes = pdf_report_service.generate_pdf_report(prop=test_property)
    # Count /Type /Page objects in PDF
    page_matches = re.findall(rb"/Type\s*/Page[^s]", pdf_bytes)
    assert len(page_matches) == 10, f"Report must contain exactly 10 pages, found {len(page_matches)}"


def test_get_property_pdf_endpoint_success(test_property):
    """Verify GET /api/v1/reports/{id}/pdf returns application/pdf with valid Content-Disposition."""
    response = client.get(f"/api/v1/reports/{test_property.id}/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "inline;" in response.headers["content-disposition"]
    assert f"DealAnalyzer_Report_Prop_{test_property.id}" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")


def test_get_property_pdf_missing_property_returns_404():
    """Verify GET /api/v1/reports/{id}/pdf returns 404 for non-existent property."""
    response = client.get("/api/v1/reports/999999/pdf")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_post_generate_property_report_metadata(test_property):
    """Verify POST /api/v1/reports/{id}/generate returns detailed report metadata."""
    payload = {
        "include_ai": True,
        "down_payment_pct": 25.0,
        "annual_interest_rate_pct": 9.0,
        "tenure_years": 15,
        "vacancy_rate_pct": 6.0,
        "custom_stamp_duty_pct": 7.0,
        "return_pdf_direct": False,
    }
    response = client.post(f"/api/v1/reports/{test_property.id}/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["property_id"] == test_property.id
    assert data["page_count"] == 10
    assert data["file_size_bytes"] > 10000
    assert "DealAnalyzer_Report_Prop_" in data["file_name"]
    assert f"/api/v1/reports/{test_property.id}/pdf" in data["download_url"]
    assert len(data["sections_included"]) == 10


def test_post_generate_property_report_direct_pdf_stream(test_property):
    """Verify POST /api/v1/reports/{id}/generate with return_pdf_direct=True streams the PDF."""
    payload = {
        "include_ai": False,
        "down_payment_pct": 20.0,
        "return_pdf_direct": True,
    }
    response = client.post(f"/api/v1/reports/{test_property.id}/generate", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment;" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")


def test_preview_property_report_stream(test_property):
    """Verify GET /api/v1/reports/{id}/preview?stream=true streams inline PDF."""
    response = client.get(f"/api/v1/reports/{test_property.id}/preview?stream=true")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "inline;" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")


def test_preview_property_report_metadata(test_property):
    """Verify GET /api/v1/reports/{id}/preview?stream=false returns metadata response."""
    response = client.get(f"/api/v1/reports/{test_property.id}/preview?stream=false")
    assert response.status_code == 200
    data = response.json()
    assert data["property_id"] == test_property.id
    assert data["page_count"] == 10
    assert "download_url" in data


def test_pdf_generation_with_missing_optional_data():
    """Verify that PDF generation handles missing property attributes gracefully."""
    # Create an in-memory property without optional fields
    sparse_prop = Property(
        id=8888,
        title="Sparse Test Listing Without Age or URL",
        city="Pune",
        locality="Kharadi",
        state=None,
        property_type="Apartment",
        bedrooms=2,
        bathrooms=2,
        built_up_area_sqft=1100.0,
        purchase_price_inr=8500000.0,
        expected_monthly_rent_inr=32000.0,
        monthly_maintenance_inr=0.0,
        property_age=None,
        listing_source="Direct",
        source_url=None,
        listing_date=None,
        is_demo=False,
    )

    pdf_bytes = pdf_report_service.generate_pdf_report(prop=sparse_prop, ai_analysis=None, benchmark=None)
    assert pdf_bytes.startswith(b"%PDF-")
    page_matches = re.findall(rb"/Type\s*/Page[^s]", pdf_bytes)
    assert len(page_matches) == 10


def test_pdf_generation_with_extremely_long_text():
    """Verify that PDF generation wraps long descriptions without clipping or failing."""
    long_title = "Ultra Luxurious Grand Penthouse Suite with Panoramic City Views, Sky Deck, Smart Automation, and Double Height Living Room Located in the Heart of the Financial District"
    long_prop = Property(
        id=7777,
        title=long_title,
        city="Hyderabad",
        locality="Financial District - Nanakramguda",
        state="Telangana",
        property_type="Penthouse",
        bedrooms=4,
        bathrooms=5,
        built_up_area_sqft=4500.0,
        purchase_price_inr=45000000.0,
        expected_monthly_rent_inr=175000.0,
        monthly_maintenance_inr=15000.0,
        property_age="1-2 years",
        listing_source="Broker Verified",
        source_url="https://example.com/very/long/listing/url/with/lots/of/parameters?ref=newsletter&campaign=luxury2026",
        listing_date="2026-02-15",
        is_demo=True,
    )

    class MockAIAnalysis:
        investment_verdict = "Strong Potential"
        executive_summary = (
            "This flagship asset represents an extraordinary capitalization opportunity within the high-density tech corridor. "
            * 5
        )
        recommendations = [
            "Verify all building sanction plans and occupancy certificates directly with municipal authorities.",
            "Establish a dedicated reserve fund for long-term maintenance of premium automation systems.",
            "Conduct thorough tenant background checks to ensure compliance with association guidelines.",
        ]

    pdf_bytes = pdf_report_service.generate_pdf_report(prop=long_prop, ai_analysis=MockAIAnalysis())
    assert pdf_bytes.startswith(b"%PDF-")
    page_matches = re.findall(rb"/Type\s*/Page[^s]", pdf_bytes)
    assert len(page_matches) == 10


def test_pdf_generation_demo_property_watermark(test_property):
    """Verify that demo properties are clearly flagged in the report."""
    from reportlab import rl_config
    old_comp = getattr(rl_config, "pageCompression", 1)
    rl_config.pageCompression = 0
    try:
        test_property.is_demo = True
        pdf_bytes = pdf_report_service.generate_pdf_report(prop=test_property)
        assert b"SIMULATED DEMO" in pdf_bytes or b"DEMO" in pdf_bytes
    finally:
        rl_config.pageCompression = old_comp
