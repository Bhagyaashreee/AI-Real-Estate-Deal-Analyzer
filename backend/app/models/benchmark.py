from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index
from app.core.database import Base


class MarketBenchmark(Base):
    __tablename__ = "market_benchmarks"

    id = Column(Integer, primary_key=True, index=True)

    # Geographic and segment identification
    city = Column(String(100), nullable=False, index=True)
    locality = Column(String(150), nullable=False, index=True)
    property_type = Column(String(50), nullable=False, default="Apartment", index=True)

    # Valuation & Pricing Benchmarks (in INR)
    avg_price_per_sqft = Column(Float, nullable=False)
    min_price_per_sqft = Column(Float, nullable=False)
    max_price_per_sqft = Column(Float, nullable=False)

    # Rental Benchmarks (in INR)
    avg_monthly_rent_inr = Column(Float, nullable=False)
    avg_gross_rental_yield_pct = Column(Float, nullable=False, index=True)

    # Provenance & Verification
    data_source = Column(String(150), nullable=False, default="Simulated Market Index")
    collection_date = Column(String(50), nullable=False, default="2026-Q1")
    verification_status = Column(
        String(50),
        nullable=False,
        default="simulated_demo",  # 'verified_market', 'user_submitted', 'simulated_demo'
        index=True,
    )
    is_demo = Column(Boolean, nullable=False, default=True, index=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# Explicit composite indexes for rapid micro-market queries
Index("idx_benchmark_city_locality", MarketBenchmark.city, MarketBenchmark.locality)
Index("idx_benchmark_city_type", MarketBenchmark.city, MarketBenchmark.property_type)

