from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index
from app.core.database import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Property Information
    title = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    locality = Column(String(150), nullable=False, index=True)
    state = Column(String(100), nullable=True, index=True)
    property_type = Column(String(50), nullable=False, default="Apartment", index=True)  # Apartment, Villa, Independent House, Commercial, Plot
    bedrooms = Column(Integer, nullable=False, default=1, index=True)  # 0 for plot/studio, 1, 2, 3, 4, etc.
    bathrooms = Column(Integer, nullable=False, default=1)
    built_up_area_sqft = Column(Float, nullable=False, index=True)
    
    # Financials (in Indian Rupees ₹)
    purchase_price_inr = Column(Float, nullable=False, index=True)
    expected_monthly_rent_inr = Column(Float, nullable=False, default=0.0)
    monthly_maintenance_inr = Column(Float, nullable=False, default=0.0)
    
    # Metadata & Provenance
    property_age = Column(String(50), nullable=True)  # e.g. "New / Under Construction", "0-2 years", "5-10 years"
    listing_source = Column(String(100), nullable=False, default="Direct Listing", index=True)  # e.g. "MagicBricks", "99acres", "Owner", "DEMO DATA"
    source_url = Column(String(500), nullable=True)
    listing_date = Column(String(50), nullable=True)
    is_demo = Column(Boolean, nullable=False, default=False, index=True)
    
    # Calculated Financial & Analysis Metrics
    price_per_sqft = Column(Float, nullable=True)
    gross_rental_yield_pct = Column(Float, nullable=True, index=True)
    net_rental_yield_pct = Column(Float, nullable=True)
    estimated_monthly_cash_flow_inr = Column(Float, nullable=True)
    ai_investment_score = Column(Integer, nullable=True)  # 1 to 100
    risk_level = Column(String(50), default="Moderate")  # Low, Moderate, High
    valuation_status = Column(String(50), default="Fair Value")  # Undervalued, Fair Value, Overpriced
    ai_summary = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Backward compatibility properties for Phase 1 naming conventions
    @property
    def bhk(self) -> int:
        return self.bedrooms

    @bhk.setter
    def bhk(self, value: int):
        self.bedrooms = value

    @property
    def area_sqft(self) -> float:
        return self.built_up_area_sqft

    @area_sqft.setter
    def area_sqft(self, value: float):
        self.built_up_area_sqft = value

    @property
    def price_inr(self) -> float:
        return self.purchase_price_inr

    @price_inr.setter
    def price_inr(self, value: float):
        self.purchase_price_inr = value

    @property
    def estimated_monthly_rent_inr(self) -> float:
        return self.expected_monthly_rent_inr

    @estimated_monthly_rent_inr.setter
    def estimated_monthly_rent_inr(self, value: float):
        self.expected_monthly_rent_inr = value


# Explicit composite indexes for high-frequency filtering combinations
Index("idx_city_property_type", Property.city, Property.property_type)
Index("idx_city_price", Property.city, Property.purchase_price_inr)
Index("idx_city_yield", Property.city, Property.gross_rental_yield_pct)
