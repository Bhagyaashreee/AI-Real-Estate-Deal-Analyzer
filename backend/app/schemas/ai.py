from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class AIAnalysisVerdict(str, Enum):
    STRONG_POTENTIAL = "Strong Potential"
    POTENTIAL_WITH_CAUTION = "Potential with Caution"
    WEAK_INVESTMENT = "Weak Investment"
    HIGH_RISK = "High Risk"
    INSUFFICIENT_INFORMATION = "Insufficient Information"


class AIRiskBreakdown(BaseModel):
    calculated_risks: List[str] = Field(
        default_factory=list,
        description="Risks identified directly from deterministic numerical calculations (e.g., negative cash flow, high debt burden, compressed yields)",
    )
    information_gap_risks: List[str] = Field(
        default_factory=list,
        description="Risks inferred from missing property records (e.g., missing age, unverified maintenance, absence of listing source)",
    )
    external_verification_required: List[str] = Field(
        default_factory=list,
        description="Crucial factors that cannot be confirmed via data alone and require physical/legal due diligence (e.g., RERA registration, occupancy certificate, encumbrance)",
    )


class AIStructuredAnalysis(BaseModel):
    property_id: int
    property_title: str
    city: str
    locality: str
    verdict: AIAnalysisVerdict
    verdict_rationale: str = Field(..., description="1-2 sentences summarizing why this verdict was assigned based on financial numbers")
    executive_summary: str = Field(..., description="Comprehensive analytical summary of the investment opportunity")
    investment_strengths: List[str] = Field(default_factory=list, description="Top positive factors grounded in the financial data")
    investment_weaknesses: List[str] = Field(default_factory=list, description="Top drawbacks or metric bottlenecks")
    risks: AIRiskBreakdown
    rental_income_analysis: str = Field(..., description="Evaluation of expected rent vs price, gross/net yield viability")
    loan_burden_analysis: str = Field(..., description="Evaluation of EMI debt load relative to operating income")
    cash_flow_interpretation: str = Field(..., description="Detailed explanation of monthly net cash flow and break-even horizon")
    scenario_analysis_summary: str = Field(..., description="Interpretation of stress tests (conservative downturn vs optimistic bull market)")
    recommendations: List[str] = Field(default_factory=list, description="Objective, non-guaranteed investor recommendations")
    missing_information: List[str] = Field(default_factory=list, description="Explicit statement of data points not available in listing")
    disclaimers: List[str] = Field(default_factory=list, description="Mandatory risk disclaimers regarding market risk and legal due diligence")
    generated_at: str
    model_used: str
    inference_time_ms: Optional[float] = None


class AIChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="Text content of the message")


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's query about the property")
    history: Optional[List[AIChatMessage]] = Field(default_factory=list, description="Prior conversation messages for context")
    financial_context: Optional[Dict[str, Any]] = Field(default=None, description="Optional override of property financial metrics")


class AIChatResponse(BaseModel):
    response: str
    property_id: int
    property_title: str
    model_used: str
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up analytical questions")
    inference_time_ms: Optional[float] = None


class AIComparisonRequest(BaseModel):
    property_ids: List[int] = Field(..., min_length=2, max_length=4, description="2 to 4 property IDs to compare")
    user_notes: Optional[str] = Field(default=None, description="Optional user preferences (e.g., 'I prioritize cash flow over appreciation')")


class AIComparisonItemInsight(BaseModel):
    property_id: int
    title: str
    city: str
    primary_strength: str
    primary_risk: str
    investor_suitability: str


class AIComparisonResponse(BaseModel):
    properties_compared: List[Dict[str, Any]]
    top_pick_property_id: Optional[int]
    top_pick_title: Optional[str]
    executive_comparison: str
    comparative_insights: List[AIComparisonItemInsight]
    key_tradeoffs: List[str]
    verdict_summary: str
    disclaimer: str
    model_used: str
    inference_time_ms: Optional[float] = None


class AIStatusResponse(BaseModel):
    status: str = Field(..., description="'online', 'offline', or 'error'")
    model_name: str
    model_available: bool
    inference_ready: bool
    base_url: str
    installed_models: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    guidance: Optional[str] = None

