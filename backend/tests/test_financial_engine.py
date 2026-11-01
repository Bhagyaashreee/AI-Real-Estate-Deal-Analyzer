import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.financial_engine import (
    financial_engine,
    AcquisitionCostInputs,
    LoanInputs,
    OperatingExpenseInputs,
)
from app.services.deal_scoring import deal_scoring_engine, ScoringWeights

client = TestClient(app)


# ----------------------------------------------------------------------
# 1. Direct Financial Engine Unit Tests
# ----------------------------------------------------------------------

def test_gross_rental_yield_calculation():
    # Purchase Price: ₹1 Cr (10,000,000), Annual Rent: ₹4.8 Lakhs (40,000 * 12 = 480,000)
    # Expected Gross Yield = (480,000 / 10,000,000) * 100 = 4.80%
    returns = financial_engine.calculate_investment_returns(
        purchase_price_inr=10000000.0,
        total_acquisition_cost_inr=10700000.0,
        down_payment_inr=2000000.0,
        total_closing_costs_inr=700000.0,
        monthly_emi_inr=69426.0,
        annual_gross_rent_inr=480000.0,
        annual_noi_inr=400000.0,
    )
    assert returns["gross_rental_yield_pct"] == 4.80


def test_net_rental_yield_calculation():
    # Purchase Price: ₹1 Cr, Total Acquisition Cost: ₹1.07 Cr (10,700,000)
    # Annual NOI: ₹4,00,000
    # Expected Net Yield = (400,000 / 10,700,000) * 100 = 3.74%
    returns = financial_engine.calculate_investment_returns(
        purchase_price_inr=10000000.0,
        total_acquisition_cost_inr=10700000.0,
        down_payment_inr=2000000.0,
        total_closing_costs_inr=700000.0,
        monthly_emi_inr=69426.0,
        annual_gross_rent_inr=480000.0,
        annual_noi_inr=400000.0,
    )
    assert returns["net_rental_yield_pct"] == 3.74


def test_loan_emi_standard_reducing_balance():
    # Principal: ₹80 Lakhs (8,000,000), 8.5% interest, 20 years (240 months)
    # Standard EMI formula check
    inputs = LoanInputs(
        purchase_price_inr=10000000.0,
        down_payment_pct=20.0,  # Loan = 80,000,000
        annual_interest_rate_pct=8.5,
        tenure_years=20,
    )
    res = financial_engine.calculate_loan_emi(inputs)
    assert res["loan_principal_inr"] == 8000000.0
    assert res["total_installments"] == 240
    # Standard EMI for 80L at 8.5% for 20 yrs is ~69,426
    assert 69400.0 <= res["monthly_emi_inr"] <= 69500.0
    assert res["total_repayment_amount_inr"] > res["loan_principal_inr"]
    assert res["is_zero_interest"] is False


def test_loan_emi_zero_interest():
    # Principal: ₹60 Lakhs, 0% interest, 5 years (60 months)
    # Expected EMI = 6,000,000 / 60 = 100,000
    inputs = LoanInputs(
        purchase_price_inr=10000000.0,
        down_payment_pct=40.0,
        annual_interest_rate_pct=0.0,
        tenure_years=5,
    )
    res = financial_engine.calculate_loan_emi(inputs)
    assert res["is_zero_interest"] is True
    assert res["loan_principal_inr"] == 6000000.0
    assert res["monthly_emi_inr"] == 100000.0
    assert res["total_interest_payable_inr"] == 0.0
    assert res["total_repayment_amount_inr"] == 6000000.0


def test_acquisition_costs_custom_rates_and_amounts():
    # 1. Using explicit percentage rates (Telangana ~7.5% stamp duty, 1% registration)
    inputs = AcquisitionCostInputs(
        purchase_price_inr=10000000.0,
        stamp_duty_rate_pct=7.5,
        registration_rate_pct=1.0,
        brokerage_rate_pct=1.0,
        renovation_expenses_inr=300000.0,
        other_acquisition_costs_inr=50000.0,
    )
    res = financial_engine.calculate_acquisition_costs(inputs)
    assert res["stamp_duty_inr"] == 750000.0
    assert res["registration_charges_inr"] == 100000.0
    assert res["brokerage_inr"] == 100000.0
    assert res["renovation_expenses_inr"] == 300000.0
    # Total closing costs = 750k + 100k + 100k + 300k + 50k = 1,300,000
    assert res["total_closing_costs_inr"] == 1300000.0
    assert res["total_acquisition_cost_inr"] == 11300000.0


def test_cash_flow_and_break_even_positive():
    # Positive cash flow test
    returns = financial_engine.calculate_investment_returns(
        purchase_price_inr=8000000.0,
        total_acquisition_cost_inr=8500000.0,
        down_payment_inr=1600000.0,
        total_closing_costs_inr=500000.0,  # Total invested capital = 2,100,000
        monthly_emi_inr=25000.0,
        annual_gross_rent_inr=420000.0,
        annual_noi_inr=360000.0,  # Annual debt service = 300,000 -> Cash flow = +60,000/yr
    )
    assert returns["annual_net_cash_flow_inr"] == 60000.0
    assert returns["monthly_net_cash_flow_inr"] == 5000.0
    assert returns["cash_on_cash_roi_pct"] == round((60000.0 / 2100000.0) * 100, 2)
    assert returns["break_even"]["status"] == "Achievable"
    # Break-even = 2,100,000 / 60,000 = 35.0 years
    assert returns["break_even"]["years"] == 35.0


def test_break_even_negative_cash_flow():
    # Negative cash flow test
    returns = financial_engine.calculate_investment_returns(
        purchase_price_inr=20000000.0,
        total_acquisition_cost_inr=21500000.0,
        down_payment_inr=4000000.0,
        total_closing_costs_inr=1500000.0,
        monthly_emi_inr=140000.0,  # Annual debt service = 1,680,000
        annual_gross_rent_inr=720000.0,
        annual_noi_inr=650000.0,  # Annual cash flow = 650,000 - 1,680,000 = -1,030,000
    )
    assert returns["annual_net_cash_flow_inr"] < 0
    assert returns["break_even"]["status"] == "Indefinite"
    assert returns["break_even"]["years"] is None


def test_appreciation_roi_distinction():
    # Explicit user appreciation rate = 5%
    returns = financial_engine.calculate_investment_returns(
        purchase_price_inr=10000000.0,
        total_acquisition_cost_inr=10700000.0,
        down_payment_inr=2000000.0,
        total_closing_costs_inr=700000.0,  # Invested capital = 2,700,000
        monthly_emi_inr=50000.0,
        annual_gross_rent_inr=500000.0,
        annual_noi_inr=450000.0,  # Cash flow = 450,000 - 600,000 = -150,000
        annual_appreciation_rate_pct=5.0,  # 5% of 10M = +500,000
    )
    apprec = returns["appreciation_metrics"]
    assert apprec["appreciation_considered"] is True
    assert apprec["annual_capital_appreciation_inr"] == 500000.0
    # Net return = -150,000 + 500,000 = +350,000
    assert apprec["total_annual_return_inr"] == 350000.0
    assert apprec["total_roi_pct"] == round((350000.0 / 2700000.0) * 100, 2)


def test_division_by_zero_protection():
    # Zero area
    p_sqft = financial_engine.calculate_price_per_sqft(10000000.0, 0.0)
    assert p_sqft == 0.0

    # Zero purchase price
    returns = financial_engine.calculate_investment_returns(
        purchase_price_inr=0.0,
        total_acquisition_cost_inr=0.0,
        down_payment_inr=0.0,
        total_closing_costs_inr=0.0,
        monthly_emi_inr=0.0,
        annual_gross_rent_inr=0.0,
        annual_noi_inr=0.0,
    )
    assert returns["gross_rental_yield_pct"] == 0.0
    assert returns["net_rental_yield_pct"] == 0.0
    assert returns["cash_on_cash_roi_pct"] == 0.0


# ----------------------------------------------------------------------
# 2. Deal Scoring & Classification Engine Tests
# ----------------------------------------------------------------------

def test_deal_scoring_classifications():
    # 1. Excellent Deal: High yield (5.2%), strong cash flow (+₹20,000)
    res_exc = deal_scoring_engine.evaluate_deal(
        purchase_price_inr=8000000.0,
        built_up_area_sqft=1100.0,
        gross_monthly_rent_inr=36000.0,
        monthly_maintenance_inr=2000.0,
        monthly_emi_inr=14000.0,
        gross_rental_yield_pct=5.40,
        net_rental_yield_pct=4.80,
        monthly_net_cash_flow_inr=20000.0,
        has_source_url=True,
        has_property_age=True,
    )
    assert res_exc["overall_score"] >= 80
    assert res_exc["classification"] == "Excellent Deal"
    assert len(res_exc["positive_factors"]) > 0

    # 2. Overpriced Deal: Compressed yield (2.2%), negative cash flow
    res_over = deal_scoring_engine.evaluate_deal(
        purchase_price_inr=35000000.0,
        built_up_area_sqft=900.0,
        gross_monthly_rent_inr=65000.0,
        monthly_maintenance_inr=6000.0,
        monthly_emi_inr=85000.0,
        gross_rental_yield_pct=2.22,
        net_rental_yield_pct=1.85,
        monthly_net_cash_flow_inr=-26000.0,
        has_source_url=True,
        has_property_age=True,
    )
    assert res_over["classification"] in ["Overpriced", "High Risk"]
    assert len(res_over["risk_flags"]) > 0


# ----------------------------------------------------------------------
# 3. API Endpoints Integration Tests
# ----------------------------------------------------------------------

def test_api_calculate_endpoint():
    # First get a valid property from list
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    assert list_res.status_code == 200
    prop_id = list_res.json()["items"][0]["id"]

    calc_payload = {
        "down_payment_pct": 25.0,
        "annual_interest_rate_pct": 8.75,
        "tenure_years": 15,
        "stamp_duty_rate_pct": 6.5,
        "registration_rate_pct": 1.0,
        "renovation_expenses_inr": 200000.0,
        "annual_appreciation_rate_pct": 4.0,
    }
    res = client.post(f"/api/v1/analysis/{prop_id}/calculate", json=calc_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["property_id"] == prop_id
    assert "acquisition_costs" in data
    assert "loan_metrics" in data
    assert "operating_finances" in data
    assert "returns" in data
    assert "deal_score" in data
    assert "transparency_notes" in data


def test_api_loan_endpoint():
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    loan_payload = {
        "down_payment_pct": 20.0,
        "annual_interest_rate_pct": 8.5,
        "tenure_years": 20,
    }
    res = client.post(f"/api/v1/analysis/{prop_id}/loan", json=loan_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["monthly_emi_inr"] > 0
    assert data["total_installments"] == 240


def test_api_score_endpoint():
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    res = client.post(f"/api/v1/analysis/{prop_id}/score", json={})
    assert res.status_code == 200
    data = res.json()
    assert "overall_score" in data
    assert 0 <= data["overall_score"] <= 100
    assert data["classification"] in ["Excellent Deal", "Good Deal", "Average Deal", "Overpriced", "High Risk"]


def test_api_compare_endpoint_success_and_limits():
    list_res = client.get("/api/v1/properties?page=1&page_size=4")
    items = list_res.json()["items"]
    ids = [item["id"] for item in items[:3]]

    # 1. Valid compare of 3 properties
    compare_payload = {
        "property_ids": ids,
        "down_payment_pct": 20.0,
        "annual_interest_rate_pct": 8.5,
        "tenure_years": 20,
    }
    res = client.post("/api/v1/analysis/compare", json=compare_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == len(ids)
    assert len(data["items"]) == len(ids)

    # 2. Exceeding 4 properties limit should fail
    bad_payload = {
        "property_ids": [1, 2, 3, 4, 5],
    }
    res_bad = client.post("/api/v1/analysis/compare", json=bad_payload)
    assert res_bad.status_code == 422 or res_bad.status_code == 400


def test_api_report_data_endpoint():
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    res = client.get(f"/api/v1/analysis/{prop_id}/report-data")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "property" in data
    assert "financial_analysis" in data
    assert "disclaimer" in data


def test_sensitivity_scenarios():
    scenarios = financial_engine.calculate_sensitivity_scenarios(
        purchase_price_inr=10000000.0,
        expected_monthly_rent_inr=45000.0,
        monthly_maintenance_inr=3000.0,
        total_acquisition_cost_inr=10700000.0,
        down_payment_inr=2000000.0,
        total_closing_costs_inr=700000.0,
        base_down_payment_pct=20.0,
        base_interest_rate_pct=8.5,
        base_tenure_years=20,
        base_vacancy_rate_pct=5.0,
    )
    assert "base" in scenarios
    assert "conservative" in scenarios
    assert "optimistic" in scenarios

    # Check optimistic generates higher or equal cash flow than conservative
    assert scenarios["optimistic"]["monthly_net_cash_flow_inr"] > scenarios["conservative"]["monthly_net_cash_flow_inr"]
    assert scenarios["optimistic"]["gross_rental_yield_pct"] > scenarios["conservative"]["gross_rental_yield_pct"]
