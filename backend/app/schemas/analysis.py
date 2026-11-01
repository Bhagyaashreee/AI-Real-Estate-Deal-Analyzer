from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.services.financial_engine import (
    AcquisitionCostInputs,
    LoanInputs,
    OperatingExpenseInputs,
)
from app.services.deal_scoring import ScoringWeights


class AnalysisCalculateRequest(BaseModel):
    # Optional overrides for property defaults
    down_payment_pct: Optional[float] = Field(20.0, ge=0, le=100)
    annual_interest_rate_pct: Optional[float] = Field(8.5, ge=0, le=30)
    tenure_years: Optional[int] = Field(20, ge=1, le=40)
    vacancy_rate_pct: Optional[float] = Field(5.0, ge=0, le=50)
    property_management_pct: Optional[float] = Field(0.0, ge=0, le=30)
    stamp_duty_rate_pct: Optional[float] = Field(None, ge=0, le=25)
    stamp_duty_inr: Optional[float] = Field(None, ge=0)
    registration_rate_pct: Optional[float] = Field(None, ge=0, le=10)
    registration_inr: Optional[float] = Field(None, ge=0)
    brokerage_rate_pct: Optional[float] = Field(None, ge=0, le=10)
    brokerage_inr: Optional[float] = Field(None, ge=0)
    renovation_expenses_inr: Optional[float] = Field(0.0, ge=0)
    other_acquisition_costs_inr: Optional[float] = Field(0.0, ge=0)
    other_monthly_expenses_inr: Optional[float] = Field(0.0, ge=0)
    annual_appreciation_rate_pct: Optional[float] = Field(None, ge=0, le=50)


class LoanCalculationRequest(BaseModel):
    purchase_price_inr: Optional[float] = Field(None, gt=0)
    down_payment_pct: float = Field(default=20.0, ge=0, le=100)
    annual_interest_rate_pct: float = Field(default=8.5, ge=0, le=30)
    tenure_years: int = Field(default=20, ge=1, le=40)


class DealScoreRequest(BaseModel):
    down_payment_pct: Optional[float] = Field(20.0, ge=0, le=100)
    annual_interest_rate_pct: Optional[float] = Field(8.5, ge=0, le=30)
    tenure_years: Optional[int] = Field(20, ge=1, le=40)
    vacancy_rate_pct: Optional[float] = Field(5.0, ge=0, le=50)
    weights: Optional[ScoringWeights] = None


class PropertyComparisonRequest(BaseModel):
    property_ids: List[int] = Field(..., min_length=1, max_length=4, description="Up to 4 property IDs to compare")
    down_payment_pct: float = Field(default=20.0, ge=0, le=100)
    annual_interest_rate_pct: float = Field(default=8.5, ge=0, le=30)
    tenure_years: int = Field(default=20, ge=1, le=40)
    vacancy_rate_pct: float = Field(default=5.0, ge=0, le=50)
    annual_appreciation_rate_pct: Optional[float] = Field(None, ge=0, le=50)


class FinancialAnalysisResponse(BaseModel):
    property_id: int
    property_title: str
    city: str
    locality: str
    purchase_price_inr: float
    built_up_area_sqft: float
    price_per_sqft: float

    # Acquisition Breakdown
    acquisition_costs: Dict[str, Any]

    # Loan & Debt Metrics
    loan_metrics: Dict[str, Any]

    # Operating Finances
    operating_finances: Dict[str, Any]

    # Return Metrics
    returns: Dict[str, Any]

    # Deal Scoring & Screening
    deal_score: Dict[str, Any]

    # Formulas & Transparency Documentation
    transparency_notes: Dict[str, Any]


class ComparisonItem(BaseModel):
    property_id: int
    title: str
    city: str
    locality: str
    property_type: str
    bedrooms: int
    built_up_area_sqft: float
    price_per_sqft: float
    purchase_price_inr: float
    total_acquisition_cost_inr: float
    gross_monthly_rent_inr: float
    monthly_emi_inr: float
    monthly_net_cash_flow_inr: float
    gross_rental_yield_pct: float
    net_rental_yield_pct: float
    cash_on_cash_roi_pct: float
    investment_score: int
    classification: str
    price_formatted: str
    rent_formatted: str
    is_demo: bool


class PropertyComparisonResponse(BaseModel):
    count: int
    assumptions: Dict[str, Any]
    items: List[ComparisonItem]

