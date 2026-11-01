from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BenchmarkBase(BaseModel):
    city: str = Field(..., min_length=2, max_length=100, description="City name (e.g. Hyderabad, Bengaluru, Pune)")
    locality: str = Field(..., min_length=2, max_length=150, description="Micro-market or locality name")
    property_type: str = Field(default="Apartment", description="Apartment, Villa, Independent House, Commercial, Plot")
    avg_price_per_sqft: float = Field(..., gt=0, description="Average benchmark capital price per sq ft in INR")
    min_price_per_sqft: float = Field(..., gt=0, description="Lower band of price per sq ft in INR")
    max_price_per_sqft: float = Field(..., gt=0, description="Upper band of price per sq ft in INR")
    avg_monthly_rent_inr: float = Field(..., ge=0, description="Average monthly rental benchmark for typical unit")
    avg_gross_rental_yield_pct: float = Field(..., ge=0, le=30, description="Benchmark gross rental yield percentage")
    data_source: str = Field(default="Local Micro-Market Survey", description="Provenance of benchmark dataset")
    collection_date: str = Field(default="2026-Q1", description="Date or quarter of collection")
    verification_status: str = Field(default="user_submitted", description="'verified_market', 'user_submitted', 'simulated_demo'")
    is_demo: bool = Field(default=False, description="Flag indicating simulated demonstration data")
    notes: Optional[str] = Field(default=None, description="Additional context or survey methodology")


class BenchmarkCreate(BenchmarkBase):
    pass


class BenchmarkResponse(BenchmarkBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BenchmarkListResponse(BaseModel):
    total: int
    items: List[BenchmarkResponse]
    provenance_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Count breakdown of verified vs user-submitted vs simulated benchmark entries",
    )


class BenchmarkImportResponse(BaseModel):
    total_rows: int
    successful_imports: int
    failed_rows: int
    errors: List[Dict[str, Any]]

