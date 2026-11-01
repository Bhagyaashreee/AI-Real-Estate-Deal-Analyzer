from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.utils.financial import format_inr


class PropertyBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Property title or heading")
    city: str = Field(..., min_length=2, max_length=100, description="City name (e.g. Hyderabad, Bengaluru)")
    locality: str = Field(..., min_length=2, max_length=150, description="Locality or micro-market (e.g. Gachibowli, Whitefield)")
    state: Optional[str] = Field(None, max_length=100, description="State (e.g. Telangana, Karnataka)")
    property_type: str = Field("Apartment", max_length=50, description="Apartment, Villa, Independent House, Commercial, Plot")
    bedrooms: int = Field(default=1, ge=0, le=50, description="Number of bedrooms / BHK")
    bathrooms: int = Field(default=1, ge=0, le=50, description="Number of bathrooms")
    built_up_area_sqft: float = Field(..., gt=0, description="Built-up area in square feet")
    purchase_price_inr: float = Field(..., gt=0, description="Total purchase price in INR (strictly positive)")
    expected_monthly_rent_inr: float = Field(default=0.0, ge=0, description="Expected monthly rental income in INR")
    monthly_maintenance_inr: float = Field(default=0.0, ge=0, description="Monthly maintenance charge in INR")
    property_age: Optional[str] = Field(None, max_length=50, description="Age of property (e.g. '0-2 years', 'Under Construction')")
    listing_source: Optional[str] = Field(default="Direct Listing", max_length=100, description="Listing source or portal")
    source_url: Optional[str] = Field(None, max_length=500, description="URL of listing source if available")
    listing_date: Optional[str] = Field(None, max_length=50, description="Listing date (YYYY-MM-DD or text)")
    is_demo: bool = Field(default=False, description="Whether this record is simulated demo data")

    @field_validator("title", "city", "locality")
    @classmethod
    def strip_and_validate_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or only whitespace")
        return cleaned


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    locality: Optional[str] = Field(None, min_length=2, max_length=150)
    state: Optional[str] = Field(None, max_length=100)
    property_type: Optional[str] = Field(None, max_length=50)
    bedrooms: Optional[int] = Field(None, ge=0, le=50)
    bathrooms: Optional[int] = Field(None, ge=0, le=50)
    built_up_area_sqft: Optional[float] = Field(None, gt=0)
    purchase_price_inr: Optional[float] = Field(None, gt=0)
    expected_monthly_rent_inr: Optional[float] = Field(None, ge=0)
    monthly_maintenance_inr: Optional[float] = Field(None, ge=0)
    property_age: Optional[str] = Field(None, max_length=50)
    listing_source: Optional[str] = Field(None, max_length=100)
    source_url: Optional[str] = Field(None, max_length=500)
    listing_date: Optional[str] = Field(None, max_length=50)
    is_demo: Optional[bool] = None

    @field_validator("title", "city", "locality")
    @classmethod
    def strip_if_present(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Field cannot be empty or only whitespace")
            return cleaned
        return v


class PropertyResponse(PropertyBase):
    id: int
    price_per_sqft: Optional[float] = None
    gross_rental_yield_pct: Optional[float] = None
    net_rental_yield_pct: Optional[float] = None
    estimated_monthly_cash_flow_inr: Optional[float] = None
    ai_investment_score: Optional[int] = None
    risk_level: Optional[str] = "Moderate"
    valuation_status: Optional[str] = "Fair Value"
    ai_summary: Optional[str] = None
    price_formatted: Optional[str] = None
    rent_formatted: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Convenience aliases for frontend consumption
    bhk: Optional[int] = None
    area_sqft: Optional[float] = None
    price_inr: Optional[float] = None
    monthly_cash_flow_inr: Optional[float] = None
    estimated_monthly_rent_inr: Optional[float] = None

    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    items: List[PropertyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CSVImportRowError(BaseModel):
    row_number: int
    property_title: Optional[str] = None
    error: str
    raw_data: Optional[Dict[str, Any]] = None


class CSVImportResult(BaseModel):
    total_rows: int
    successful_imports: int
    failed_imports: int
    skipped_duplicates: int
    errors: List[CSVImportRowError]

