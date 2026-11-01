from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    include_ai: bool = Field(default=True, description="Whether to include AI investment narrative if available")
    down_payment_pct: Optional[float] = Field(default=20.0, ge=0.0, le=100.0, description="Override down payment percentage")
    annual_interest_rate_pct: Optional[float] = Field(default=8.5, ge=0.0, le=30.0, description="Override home loan interest rate %")
    tenure_years: Optional[int] = Field(default=20, ge=1, le=40, description="Override loan tenure in years")
    vacancy_rate_pct: Optional[float] = Field(default=5.0, ge=0.0, le=50.0, description="Override vacancy rate %")
    custom_stamp_duty_pct: Optional[float] = Field(default=6.0, ge=0.0, le=25.0, description="Override stamp duty %")
    return_pdf_direct: bool = Field(default=False, description="If True, directly return application/pdf stream")


class ReportMetadataResponse(BaseModel):
    property_id: int
    property_title: str
    city: str
    locality: str
    page_count: int
    file_size_bytes: int
    file_name: str
    download_url: str
    preview_url: str
    generated_at: str
    ai_included: bool
    sections_included: List[str]
    disclaimer: str

