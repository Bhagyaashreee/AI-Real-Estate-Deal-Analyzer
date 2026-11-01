from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.property import Property
from app.schemas.analysis import (
    AnalysisCalculateRequest,
    LoanCalculationRequest,
    DealScoreRequest,
    PropertyComparisonRequest,
    FinancialAnalysisResponse,
    PropertyComparisonResponse,
    ComparisonItem,
)
from app.services.financial_engine import (
    financial_engine,
    AcquisitionCostInputs,
    LoanInputs,
    OperatingExpenseInputs,
)
from app.services.deal_scoring import deal_scoring_engine
from app.utils.financial import format_inr

router = APIRouter()


def perform_full_analysis(
    prop: Property,
    req: AnalysisCalculateRequest,
) -> FinancialAnalysisResponse:
    """Helper to execute the full deterministic financial model on a Property."""
    price = prop.purchase_price_inr
    area = prop.built_up_area_sqft
    price_per_sqft = financial_engine.calculate_price_per_sqft(price, area)

    # 1. Acquisition Costs
    acq_inputs = AcquisitionCostInputs(
        purchase_price_inr=price,
        stamp_duty_rate_pct=req.stamp_duty_rate_pct,
        stamp_duty_inr=req.stamp_duty_inr,
        registration_rate_pct=req.registration_rate_pct,
        registration_inr=req.registration_inr,
        brokerage_rate_pct=req.brokerage_rate_pct,
        brokerage_inr=req.brokerage_inr,
        renovation_expenses_inr=req.renovation_expenses_inr or 0.0,
        other_acquisition_costs_inr=req.other_acquisition_costs_inr or 0.0,
    )
    acq_results = financial_engine.calculate_acquisition_costs(acq_inputs)

    # 2. Loan & EMI Metrics
    loan_inputs = LoanInputs(
        purchase_price_inr=price,
        down_payment_pct=req.down_payment_pct if req.down_payment_pct is not None else 20.0,
        annual_interest_rate_pct=req.annual_interest_rate_pct if req.annual_interest_rate_pct is not None else 8.5,
        tenure_years=req.tenure_years if req.tenure_years is not None else 20,
    )
    loan_results = financial_engine.calculate_loan_emi(loan_inputs)

    # 3. Operating Finances
    op_inputs = OperatingExpenseInputs(
        expected_monthly_rent_inr=prop.expected_monthly_rent_inr,
        monthly_maintenance_inr=prop.monthly_maintenance_inr,
        vacancy_rate_pct=req.vacancy_rate_pct if req.vacancy_rate_pct is not None else 5.0,
        property_management_pct=req.property_management_pct if req.property_management_pct is not None else 0.0,
        other_monthly_expenses_inr=req.other_monthly_expenses_inr or 0.0,
    )
    op_results = financial_engine.calculate_operating_finances(op_inputs)

    # 4. Returns & Yields
    returns = financial_engine.calculate_investment_returns(
        purchase_price_inr=price,
        total_acquisition_cost_inr=acq_results["total_acquisition_cost_inr"],
        down_payment_inr=loan_results["down_payment_inr"],
        total_closing_costs_inr=acq_results["total_closing_costs_inr"],
        monthly_emi_inr=loan_results["monthly_emi_inr"],
        annual_gross_rent_inr=op_results["annual_gross_rent_inr"],
        annual_noi_inr=op_results["annual_noi_inr"],
        annual_appreciation_rate_pct=req.annual_appreciation_rate_pct,
    )

    # 4b. Sensitivity Scenarios (Best / Base / Conservative)
    returns["sensitivity_scenarios"] = financial_engine.calculate_sensitivity_scenarios(
        purchase_price_inr=price,
        expected_monthly_rent_inr=prop.expected_monthly_rent_inr,
        monthly_maintenance_inr=prop.monthly_maintenance_inr,
        total_acquisition_cost_inr=acq_results["total_acquisition_cost_inr"],
        down_payment_inr=loan_results["down_payment_inr"],
        total_closing_costs_inr=acq_results["total_closing_costs_inr"],
        base_down_payment_pct=loan_inputs.down_payment_pct,
        base_interest_rate_pct=loan_inputs.annual_interest_rate_pct,
        base_tenure_years=loan_inputs.tenure_years,
        base_vacancy_rate_pct=op_inputs.vacancy_rate_pct,
    )

    # 5. Deal Scoring Engine
    deal_score = deal_scoring_engine.evaluate_deal(
        purchase_price_inr=price,
        built_up_area_sqft=area,
        gross_monthly_rent_inr=op_results["gross_monthly_rent_inr"],
        monthly_maintenance_inr=op_results["monthly_maintenance_inr"],
        monthly_emi_inr=loan_results["monthly_emi_inr"],
        gross_rental_yield_pct=returns["gross_rental_yield_pct"],
        net_rental_yield_pct=returns["net_rental_yield_pct"],
        monthly_net_cash_flow_inr=returns["monthly_net_cash_flow_inr"],
        vacancy_rate_pct=op_results["vacancy_rate_pct"],
        has_source_url=bool(prop.source_url),
        has_property_age=bool(prop.property_age),
    )

    # 6. Formulas & Transparency Documentation
    transparency = {
        "gross_rental_yield_formula": "Gross Rental Yield (%) = (Annual Gross Rent / Purchase Price) * 100",
        "net_rental_yield_formula": "Net Rental Yield (%) = (Annual Net Operating Income / Total Acquisition Cost) * 100",
        "monthly_cash_flow_formula": "Monthly Cash Flow = Effective Monthly Rent - Operating Expenses - Monthly EMI",
        "emi_formula": "Reducing Balance: E = P * r * (1 + r)^n / ((1 + r)^n - 1)",
        "cash_on_cash_roi_formula": "Cash-on-Cash Return (%) = (Annual Net Cash Flow / Total Invested Capital) * 100",
        "break_even_formula": "Break-even Timeline (Years) = Total Invested Capital / Annual Net Cash Flow",
        "assumptions": [
            f"Vacancy rate assumed at {op_results['vacancy_rate_pct']}% (~{round(op_results['vacancy_rate_pct'] * 3.65)} unoccupied days per year).",
            f"Loan structured with {loan_inputs.down_payment_pct}% down payment at {loan_inputs.annual_interest_rate_pct}% interest over {loan_inputs.tenure_years} years.",
            "All calculations reflect local Indian Rupee (₹) cash flows without third-party API dependencies.",
        ],
        "limitations": [
            "Analytical screening model; does not account for changes in tax law, personal income tax brackets, or variable interest rate resets.",
            "Capital appreciation is strictly omitted from cash-on-cash yield to ensure conservative baseline viability.",
        ],
    }

    return FinancialAnalysisResponse(
        property_id=prop.id,
        property_title=prop.title,
        city=prop.city,
        locality=prop.locality,
        purchase_price_inr=price,
        built_up_area_sqft=area,
        price_per_sqft=price_per_sqft,
        acquisition_costs=acq_results,
        loan_metrics=loan_results,
        operating_finances=op_results,
        returns=returns,
        deal_score=deal_score,
        transparency_notes=transparency,
    )


@router.post("/{property_id}/calculate", response_model=FinancialAnalysisResponse)
def calculate_property_analysis(
    property_id: int,
    request: AnalysisCalculateRequest,
    db: Session = Depends(get_db),
):
    """
    Perform a complete deterministic financial analysis on an Indian real estate property.
    Calculates Acquisition Costs, EMI, Net Operating Income, Yields, Cash Flow,
    Cash-on-Cash Return, and Break-Even Timeline.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} was not found",
        )

    return perform_full_analysis(prop, request)


@router.post("/{property_id}/loan")
def calculate_property_loan(
    property_id: int,
    request: LoanCalculationRequest,
    db: Session = Depends(get_db),
):
    """Calculate home loan reducing-balance EMI and interest burden for a property."""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} was not found",
        )

    price = request.purchase_price_inr or prop.purchase_price_inr
    loan_inputs = LoanInputs(
        purchase_price_inr=price,
        down_payment_pct=request.down_payment_pct,
        annual_interest_rate_pct=request.annual_interest_rate_pct,
        tenure_years=request.tenure_years,
    )
    return financial_engine.calculate_loan_emi(loan_inputs)


@router.post("/{property_id}/score")
def calculate_property_score(
    property_id: int,
    request: DealScoreRequest,
    db: Session = Depends(get_db),
):
    """Calculate the explainable 0-100 investment score and classification for a property."""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} was not found",
        )

    # Perform base calculation
    calc_req = AnalysisCalculateRequest(
        down_payment_pct=request.down_payment_pct,
        annual_interest_rate_pct=request.annual_interest_rate_pct,
        tenure_years=request.tenure_years,
        vacancy_rate_pct=request.vacancy_rate_pct,
    )
    analysis = perform_full_analysis(prop, calc_req)

    # If custom weights supplied, recalculate score
    if request.weights:
        custom_score = deal_scoring_engine.evaluate_deal(
            purchase_price_inr=prop.purchase_price_inr,
            built_up_area_sqft=prop.built_up_area_sqft,
            gross_monthly_rent_inr=analysis.operating_finances["gross_monthly_rent_inr"],
            monthly_maintenance_inr=analysis.operating_finances["monthly_maintenance_inr"],
            monthly_emi_inr=analysis.loan_metrics["monthly_emi_inr"],
            gross_rental_yield_pct=analysis.returns["gross_rental_yield_pct"],
            net_rental_yield_pct=analysis.returns["net_rental_yield_pct"],
            monthly_net_cash_flow_inr=analysis.returns["monthly_net_cash_flow_inr"],
            vacancy_rate_pct=analysis.operating_finances["vacancy_rate_pct"],
            has_source_url=bool(prop.source_url),
            has_property_age=bool(prop.property_age),
            weights=request.weights,
        )
        return custom_score

    return analysis.deal_score


@router.post("/compare", response_model=PropertyComparisonResponse)
def compare_properties(
    request: PropertyComparisonRequest,
    db: Session = Depends(get_db),
):
    """
    Compare up to 4 Indian properties side by side across purchase ticket,
    acquisition costs, yields, EMI, monthly cash flow, ROI, and investment score.
    """
    if not request.property_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one property ID must be provided for comparison.",
        )
    if len(request.property_ids) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A maximum of 4 properties can be compared simultaneously.",
        )

    properties = (
        db.query(Property).filter(Property.id.in_(request.property_ids)).all()
    )
    if not properties:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="None of the specified property IDs were found.",
        )

    # Preserve requested order
    prop_dict = {p.id: p for p in properties}
    ordered_props = [prop_dict[pid] for pid in request.property_ids if pid in prop_dict]

    items: List[ComparisonItem] = []
    calc_req = AnalysisCalculateRequest(
        down_payment_pct=request.down_payment_pct,
        annual_interest_rate_pct=request.annual_interest_rate_pct,
        tenure_years=request.tenure_years,
        vacancy_rate_pct=request.vacancy_rate_pct,
        annual_appreciation_rate_pct=request.annual_appreciation_rate_pct,
    )

    for prop in ordered_props:
        analysis = perform_full_analysis(prop, calc_req)
        items.append(
            ComparisonItem(
                property_id=prop.id,
                title=prop.title,
                city=prop.city,
                locality=prop.locality,
                property_type=prop.property_type,
                bedrooms=prop.bedrooms,
                built_up_area_sqft=prop.built_up_area_sqft,
                price_per_sqft=analysis.price_per_sqft,
                purchase_price_inr=prop.purchase_price_inr,
                total_acquisition_cost_inr=analysis.acquisition_costs["total_acquisition_cost_inr"],
                gross_monthly_rent_inr=prop.expected_monthly_rent_inr,
                monthly_emi_inr=analysis.loan_metrics["monthly_emi_inr"],
                monthly_net_cash_flow_inr=analysis.returns["monthly_net_cash_flow_inr"],
                gross_rental_yield_pct=analysis.returns["gross_rental_yield_pct"],
                net_rental_yield_pct=analysis.returns["net_rental_yield_pct"],
                cash_on_cash_roi_pct=analysis.returns["cash_on_cash_roi_pct"],
                investment_score=analysis.deal_score["overall_score"],
                classification=analysis.deal_score["classification"],
                price_formatted=format_inr(prop.purchase_price_inr),
                rent_formatted=f"{format_inr(prop.expected_monthly_rent_inr)}/mo",
                is_demo=prop.is_demo,
            )
        )

    return PropertyComparisonResponse(
        count=len(items),
        assumptions={
            "down_payment_pct": request.down_payment_pct,
            "annual_interest_rate_pct": request.annual_interest_rate_pct,
            "tenure_years": request.tenure_years,
            "vacancy_rate_pct": request.vacancy_rate_pct,
            "currency": "INR (₹)",
        },
        items=items,
    )


@router.get("/{property_id}/report-data")
def get_property_report_data(
    property_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve comprehensive report data for a property, structured for
    exportable investment dossiers or deep analytical presentations.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} was not found",
        )

    calc_req = AnalysisCalculateRequest()
    analysis = perform_full_analysis(prop, calc_req)
    return {
        "status": "success",
        "property": {
            "id": prop.id,
            "title": prop.title,
            "city": prop.city,
            "locality": prop.locality,
            "state": prop.state,
            "property_type": prop.property_type,
            "bedrooms": prop.bedrooms,
            "bathrooms": prop.bathrooms,
            "built_up_area_sqft": prop.built_up_area_sqft,
            "property_age": prop.property_age,
            "listing_source": prop.listing_source,
            "source_url": prop.source_url,
            "listing_date": prop.listing_date,
            "is_demo": prop.is_demo,
        },
        "financial_analysis": analysis,
        "disclaimer": (
            "NOTICE: Deterministic financial model calculation. "
            "Property listings marked as DEMO DATA are simulated for computational testing only. "
            "Does not constitute legal or certified investment advice."
        ),
    }
