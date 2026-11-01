from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RiskCategoryDetail(BaseModel):
    category_id: str
    category_name: str
    score: float = Field(..., ge=0, le=100, description="Risk score 0-100 where higher means higher risk exposure")
    risk_level: str = Field(..., description="'Low', 'Moderate', 'Elevated', 'Severe'")
    factors: List[str] = Field(default_factory=list, description="Specific identified risks in this category")
    mitigation_steps: List[str] = Field(default_factory=list, description="Actionable recommendations to mitigate this risk")


class RiskScoreBreakdown(BaseModel):
    property_id: int
    property_title: str
    city: str
    locality: str

    # Three Independent Core Scores
    investment_attractiveness_score: float = Field(..., ge=0, le=100, description="Deal return attractiveness (0-100, higher is better)")
    risk_exposure_score: float = Field(..., ge=0, le=100, description="Comprehensive risk exposure (0-100, higher is riskier)")
    data_confidence_score: float = Field(..., ge=0, le=100, description="Data reliability & provenance confidence (0-100, higher is more reliable)")

    overall_risk_level: str = Field(..., description="'Low Risk', 'Moderate Risk', 'Elevated Risk', 'High Risk', 'Critical Risk'")
    data_confidence_level: str = Field(..., description="'High Confidence', 'Moderate Confidence', 'Low Confidence', 'Unverified'")

    # Category Subscores
    categories: Dict[str, RiskCategoryDetail]
    critical_red_flags: List[str] = Field(default_factory=list, description="Severe financial, debt, or legal deal-breaker risks")
    data_confidence_reasons: List[str] = Field(default_factory=list, description="Explanation for confidence rating")
    external_verification_checklist: List[str] = Field(default_factory=list, description="Real-world due diligence checklist before transacting")

    scoring_methodology: Dict[str, Any] = Field(default_factory=dict, description="Configurable weights and formula transparency")
    disclaimer: str


class WhatIfSimulationInputs(BaseModel):
    purchase_price_inr: Optional[float] = Field(None, gt=0, description="Override purchase price in INR")
    expected_monthly_rent_inr: Optional[float] = Field(None, ge=0, description="Override expected monthly rent in INR")
    vacancy_rate_pct: Optional[float] = Field(None, ge=0, le=50, description="Override vacancy rate percentage (e.g. 8.0%)")
    annual_maintenance_inr: Optional[float] = Field(None, ge=0, description="Override annual maintenance expenses in INR")
    annual_interest_rate_pct: Optional[float] = Field(None, ge=0, le=30, description="Override loan interest rate % (e.g. 9.5%)")
    down_payment_pct: Optional[float] = Field(None, ge=0, le=100, description="Override down payment percentage (e.g. 25%)")
    tenure_years: Optional[int] = Field(None, ge=1, le=40, description="Override loan tenure in years")
    acquisition_expenses_inr: Optional[float] = Field(None, ge=0, description="Override closing costs and renovation in INR")


class ScenarioOutcome(BaseModel):
    scenario_id: str
    scenario_name: str
    description: str
    badge: str

    purchase_price_inr: float
    monthly_rent_inr: float
    vacancy_rate_pct: float
    interest_rate_pct: float
    down_payment_pct: float
    tenure_years: int

    monthly_emi_inr: float
    monthly_noi_inr: float
    monthly_cash_flow_inr: float
    gross_rental_yield_pct: float
    net_rental_yield_pct: float
    cash_on_cash_roi_pct: float
    risk_score: float
    risk_level: str
    break_even_summary: str


class WhatIfSimulationResponse(BaseModel):
    property_id: int
    property_title: str
    base_case: ScenarioOutcome
    scenarios: List[ScenarioOutcome]
    custom_simulation: Optional[ScenarioOutcome] = None
    insights: List[str] = Field(default_factory=list, description="Key analytical conclusions from stress-testing")


class DataConfidenceResponse(BaseModel):
    property_id: int
    property_title: str
    confidence_score: float = Field(..., ge=0, le=100)
    confidence_level: str = Field(..., description="'High Confidence', 'Moderate Confidence', 'Low Confidence', 'Unverified'")
    positive_signals: List[str]
    missing_elements: List[str]
    benchmark_status: str
    is_demo: bool
    explanation: str


class CompareScenariosRequest(BaseModel):
    property_ids: List[int] = Field(..., min_length=1, max_length=4, description="List of 1 to 4 property IDs to simulate")
    inputs: Optional[WhatIfSimulationInputs] = Field(None, description="Optional custom financial parameter overrides")
