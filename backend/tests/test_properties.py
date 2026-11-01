import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.property import Property

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_test_properties():
    """Ensure test properties with 'Test' or 'CSV Test' are cleaned up between test runs."""
    db = SessionLocal()
    try:
        db.query(Property).filter(
            (Property.title.like("Test %")) | (Property.title.like("CSV Test %")) | (Property.title.like("Property %"))
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(Property).filter(
            (Property.title.like("Test %")) | (Property.title.like("CSV Test %")) | (Property.title.like("Property %"))
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def test_create_property_success():
    payload = {
        "title": "Test 3 BHK Lakeview Residency",
        "city": "Hyderabad",
        "locality": "Kondapur",
        "state": "Telangana",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 1750.0,
        "purchase_price_inr": 15000000.0,
        "expected_monthly_rent_inr": 55000.0,
        "monthly_maintenance_inr": 4000.0,
        "property_age": "1 year",
        "listing_source": "Test Broker",
        "is_demo": False,
    }
    response = client.post("/api/v1/properties", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["city"] == "Hyderabad"
    assert data["price_per_sqft"] > 0
    assert data["gross_rental_yield_pct"] > 0
    assert "₹" in data["price_formatted"]
    assert data["id"] is not None


def test_create_property_duplicate_prevention():
    payload = {
        "title": "Test Duplicate Property",
        "city": "Hyderabad",
        "locality": "Kondapur",
        "property_type": "Apartment",
        "bedrooms": 3,
        "built_up_area_sqft": 1750.0,
        "purchase_price_inr": 15000000.0,
    }
    first = client.post("/api/v1/properties", json=payload)
    assert first.status_code == 201

    # Second post with identical title + city + locality should be rejected
    second = client.post("/api/v1/properties", json=payload)
    assert second.status_code == 400
    assert "already exists" in second.json()["detail"]


def test_create_property_invalid_financial_values():
    # Negative purchase price
    bad_payload_1 = {
        "title": "Invalid Price Property",
        "city": "Hyderabad",
        "locality": "Madhapur",
        "built_up_area_sqft": 1000.0,
        "purchase_price_inr": -5000000.0,
    }
    res1 = client.post("/api/v1/properties", json=bad_payload_1)
    assert res1.status_code == 422

    # Negative monthly rent
    bad_payload_2 = {
        "title": "Invalid Rent Property",
        "city": "Hyderabad",
        "locality": "Madhapur",
        "built_up_area_sqft": 1000.0,
        "purchase_price_inr": 5000000.0,
        "expected_monthly_rent_inr": -15000.0,
    }
    res2 = client.post("/api/v1/properties", json=bad_payload_2)
    assert res2.status_code == 422

    # Zero or negative built-up area
    bad_payload_3 = {
        "title": "Invalid Area Property",
        "city": "Hyderabad",
        "locality": "Madhapur",
        "built_up_area_sqft": 0.0,
        "purchase_price_inr": 5000000.0,
    }
    res3 = client.post("/api/v1/properties", json=bad_payload_3)
    assert res3.status_code == 422


def test_get_property_by_id():
    # List first property to get an ID
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) > 0
    prop_id = items[0]["id"]

    res = client.get(f"/api/v1/properties/{prop_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == prop_id
    assert data["title"] is not None
    assert "monthly_cash_flow_inr" in data
    assert "estimated_monthly_cash_flow_inr" in data
    assert "estimated_monthly_rent_inr" in data
    assert data["monthly_cash_flow_inr"] == data["estimated_monthly_cash_flow_inr"]


def test_get_property_not_found():
    res = client.get("/api/v1/properties/9999999")
    assert res.status_code == 404


def test_update_property_and_persistence():
    # Create a property to update
    create_payload = {
        "title": "Property To Update Test",
        "city": "Pune",
        "locality": "Baner",
        "property_type": "Apartment",
        "bedrooms": 2,
        "built_up_area_sqft": 1000.0,
        "purchase_price_inr": 7000000.0,
        "expected_monthly_rent_inr": 25000.0,
    }
    create_res = client.post("/api/v1/properties", json=create_payload)
    assert create_res.status_code == 201
    prop_id = create_res.json()["id"]

    # Update rent and title
    update_payload = {
        "title": "Property Updated Successfully",
        "expected_monthly_rent_inr": 35000.0,
    }
    put_res = client.put(f"/api/v1/properties/{prop_id}", json=update_payload)
    assert put_res.status_code == 200
    updated_data = put_res.json()
    assert updated_data["title"] == "Property Updated Successfully"
    assert updated_data["expected_monthly_rent_inr"] == 35000.0

    # Verify database persistence with fresh query
    get_res = client.get(f"/api/v1/properties/{prop_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Property Updated Successfully"


def test_delete_property():
    # Create a property to delete
    create_payload = {
        "title": "Property To Delete Test",
        "city": "Chennai",
        "locality": "Adyar",
        "property_type": "Apartment",
        "bedrooms": 2,
        "built_up_area_sqft": 900.0,
        "purchase_price_inr": 6000000.0,
    }
    create_res = client.post("/api/v1/properties", json=create_payload)
    assert create_res.status_code == 201
    prop_id = create_res.json()["id"]

    # Delete
    del_res = client.delete(f"/api/v1/properties/{prop_id}")
    assert del_res.status_code == 200

    # Ensure 404 after deletion
    get_res = client.get(f"/api/v1/properties/{prop_id}")
    assert get_res.status_code == 404


def test_search_and_filtering():
    # Filter by city
    res_hyd = client.get("/api/v1/properties?city=Hyderabad")
    assert res_hyd.status_code == 200
    for item in res_hyd.json()["items"]:
        assert item["city"].lower() == "hyderabad"

    # Filter by price range
    min_p = 5000000.0
    max_p = 15000000.0
    res_price = client.get(f"/api/v1/properties?min_price={min_p}&max_price={max_p}")
    assert res_price.status_code == 200
    for item in res_price.json()["items"]:
        assert min_p <= item["purchase_price_inr"] <= max_p

    # Filter by bedrooms
    res_beds = client.get("/api/v1/properties?min_bedrooms=3")
    assert res_beds.status_code == 200
    for item in res_beds.json()["items"]:
        assert item["bedrooms"] >= 3


def test_pagination():
    res = client.get("/api/v1/properties?page=1&page_size=5")
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["items"]) <= 5
    assert data["total"] > 0
    assert data["total_pages"] >= 1


def test_csv_template_download():
    res = client.get("/api/v1/properties/template-csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "title,city,locality" in res.text


def test_csv_import_success_and_validation():
    valid_csv = """title,city,locality,state,property_type,bedrooms,bathrooms,built_up_area_sqft,purchase_price_inr,expected_monthly_rent_inr,monthly_maintenance_inr,property_age,listing_source,source_url,listing_date,is_demo
CSV Test 2 BHK in Gachibowli,Hyderabad,Gachibowli,Telangana,Apartment,2,2,1100,8500000,32000,2500,1-3 years,CSV Test,https://test.local/csv1,2026-10-30,True
CSV Test 3 BHK in Whitefield,Bengaluru,Whitefield,Karnataka,Apartment,3,3,1600,13500000,50000,4000,New,CSV Test,https://test.local/csv2,2026-10-30,True
"""
    files = {"file": ("test_import.csv", io.BytesIO(valid_csv.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/properties/import-csv", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["successful_imports"] == 2
    assert data["failed_imports"] == 0

    # Re-uploading identical CSV should detect duplicates and not insert again
    files_dupe = {"file": ("test_import.csv", io.BytesIO(valid_csv.encode("utf-8")), "text/csv")}
    res_dupe = client.post("/api/v1/properties/import-csv", files=files_dupe)
    assert res_dupe.status_code == 200
    data_dupe = res_dupe.json()
    assert data_dupe["successful_imports"] == 0
    assert data_dupe["skipped_duplicates"] == 2


def test_csv_import_reporting_invalid_rows():
    invalid_csv = """title,city,locality,built_up_area_sqft,purchase_price_inr,expected_monthly_rent_inr
AB,Hyderabad,Kondapur,1200,8000000,30000
Valid Row 3 BHK,Hyderabad,Kondapur,1400,-9000000,35000
Valid Row 2 BHK,Hyderabad,Kondapur,-500,9000000,35000
"""
    files = {"file": ("invalid_test.csv", io.BytesIO(invalid_csv.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/properties/import-csv", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["failed_imports"] > 0
    assert len(data["errors"]) > 0
    # Every invalid row is reported with row number and reason
    assert any("title" in err["error"].lower() for err in data["errors"])
    assert any("price" in err["error"].lower() for err in data["errors"])
    assert any("area" in err["error"].lower() for err in data["errors"])
