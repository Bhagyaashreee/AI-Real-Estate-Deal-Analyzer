import csv
import io
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.benchmark import MarketBenchmark
from app.schemas.benchmark import BenchmarkCreate, BenchmarkResponse


class BenchmarkService:
    @staticmethod
    def get_benchmarks(
        db: Session,
        city: Optional[str] = None,
        locality: Optional[str] = None,
        property_type: Optional[str] = None,
        verification_status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[MarketBenchmark], int, Dict[str, int]]:
        """List benchmarks with optional filters and provenance breakdown."""
        query = db.query(MarketBenchmark)

        if city and city != "All Cities":
            query = query.filter(func.lower(MarketBenchmark.city) == city.lower())
        if locality:
            query = query.filter(func.lower(MarketBenchmark.locality).contains(locality.lower()))
        if property_type and property_type != "All":
            query = query.filter(MarketBenchmark.property_type == property_type)
        if verification_status and verification_status != "All":
            query = query.filter(MarketBenchmark.verification_status == verification_status)

        total = query.count()
        items = query.order_by(MarketBenchmark.city, MarketBenchmark.locality).offset(skip).limit(limit).all()

        # Provenance summary count
        provenance: Dict[str, int] = {}
        counts = (
            db.query(MarketBenchmark.verification_status, func.count(MarketBenchmark.id))
            .group_by(MarketBenchmark.verification_status)
            .all()
        )
        for status_val, c in counts:
            provenance[status_val] = c

        return items, total, provenance

    @staticmethod
    def get_matching_benchmark(
        db: Session,
        city: str,
        locality: Optional[str] = None,
        property_type: Optional[str] = "Apartment",
    ) -> Optional[MarketBenchmark]:
        """
        Find closest matching benchmark.
        First attempts exact locality match, then city-level fallback.
        Never fabricates numbers if no records match.
        """
        # 1. Try exact city + locality + property_type match
        if locality:
            bench = (
                db.query(MarketBenchmark)
                .filter(
                    func.lower(MarketBenchmark.city) == city.lower(),
                    func.lower(MarketBenchmark.locality) == locality.lower(),
                    MarketBenchmark.property_type == property_type,
                )
                .first()
            )
            if bench:
                return bench

            # 2. Try city + partial locality match
            bench = (
                db.query(MarketBenchmark)
                .filter(
                    func.lower(MarketBenchmark.city) == city.lower(),
                    func.lower(MarketBenchmark.locality).contains(locality.lower()[:5]),
                )
                .first()
            )
            if bench:
                return bench

        # 3. Fallback to city-wide average benchmark for that property_type
        bench = (
            db.query(MarketBenchmark)
            .filter(
                func.lower(MarketBenchmark.city) == city.lower(),
                MarketBenchmark.property_type == property_type,
            )
            .first()
        )
        return bench

    @staticmethod
    def create_benchmark(db: Session, b: BenchmarkCreate) -> MarketBenchmark:
        """Create a new user-entered or verified benchmark record."""
        bench = MarketBenchmark(
            city=b.city.strip(),
            locality=b.locality.strip(),
            property_type=b.property_type,
            avg_price_per_sqft=b.avg_price_per_sqft,
            min_price_per_sqft=b.min_price_per_sqft,
            max_price_per_sqft=b.max_price_per_sqft,
            avg_monthly_rent_inr=b.avg_monthly_rent_inr,
            avg_gross_rental_yield_pct=b.avg_gross_rental_yield_pct,
            data_source=b.data_source,
            collection_date=b.collection_date,
            verification_status=b.verification_status,
            is_demo=b.is_demo,
            notes=b.notes,
        )
        db.add(bench)
        db.commit()
        db.refresh(bench)
        return bench

    @staticmethod
    def import_benchmarks_csv(db: Session, file_contents: bytes) -> Dict[str, Any]:
        """
        Import benchmark data from CSV with strict column validation and deduplication.
        """
        text = file_contents.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        required_cols = {
            "city",
            "locality",
            "property_type",
            "avg_price_per_sqft",
            "avg_monthly_rent_inr",
            "avg_gross_rental_yield_pct",
        }
        if not reader.fieldnames or not required_cols.issubset(set(reader.fieldnames)):
            missing = required_cols - set(reader.fieldnames or [])
            return {
                "total_rows": 0,
                "successful_imports": 0,
                "failed_rows": 0,
                "errors": [{"row": 0, "error": f"Missing required CSV columns: {list(missing)}"}],
            }

        successful = 0
        failed = 0
        errors = []

        for row_num, row in enumerate(reader, start=1):
            try:
                city = row.get("city", "").strip()
                locality = row.get("locality", "").strip()
                p_type = row.get("property_type", "Apartment").strip()
                avg_psqft = float(row.get("avg_price_per_sqft", 0))
                min_psqft = float(row.get("min_price_per_sqft", avg_psqft * 0.85))
                max_psqft = float(row.get("max_price_per_sqft", avg_psqft * 1.15))
                rent = float(row.get("avg_monthly_rent_inr", 0))
                yield_pct = float(row.get("avg_gross_rental_yield_pct", 0))
                source = row.get("data_source", "Uploaded CSV Dataset").strip()
                date_val = row.get("collection_date", "2026-Q1").strip()
                status_val = row.get("verification_status", "user_submitted").strip()
                is_demo_val = row.get("is_demo", "false").lower() in ["true", "1", "yes"]

                if not city or not locality or avg_psqft <= 0:
                    errors.append({"row": row_num, "error": "City, locality and positive avg_price_per_sqft are required."})
                    failed += 1
                    continue

                # Deduplicate by updating or inserting
                existing = (
                    db.query(MarketBenchmark)
                    .filter(
                        func.lower(MarketBenchmark.city) == city.lower(),
                        func.lower(MarketBenchmark.locality) == locality.lower(),
                        MarketBenchmark.property_type == p_type,
                    )
                    .first()
                )

                if existing:
                    existing.avg_price_per_sqft = avg_psqft
                    existing.min_price_per_sqft = min_psqft
                    existing.max_price_per_sqft = max_psqft
                    existing.avg_monthly_rent_inr = rent
                    existing.avg_gross_rental_yield_pct = yield_pct
                    existing.data_source = source
                    existing.collection_date = date_val
                    existing.verification_status = status_val
                    existing.is_demo = is_demo_val
                else:
                    new_b = MarketBenchmark(
                        city=city,
                        locality=locality,
                        property_type=p_type,
                        avg_price_per_sqft=avg_psqft,
                        min_price_per_sqft=min_psqft,
                        max_price_per_sqft=max_psqft,
                        avg_monthly_rent_inr=rent,
                        avg_gross_rental_yield_pct=yield_pct,
                        data_source=source,
                        collection_date=date_val,
                        verification_status=status_val,
                        is_demo=is_demo_val,
                    )
                    db.add(new_b)

                successful += 1
            except Exception as e:
                failed += 1
                errors.append({"row": row_num, "error": str(e)})

        db.commit()
        return {
            "total_rows": successful + failed,
            "successful_imports": successful,
            "failed_rows": failed,
            "errors": errors,
        }

    @staticmethod
    def seed_demo_benchmarks(db: Session) -> int:
        """
        Idempotently populate simulated demonstration benchmarks across key Indian hubs.
        Clearly marked as 'simulated_demo' and is_demo=True.
        """
        demo_benchmarks = [
            # Hyderabad
            {"city": "Hyderabad", "locality": "Gachibowli", "property_type": "Apartment", "avg_price_per_sqft": 8800.0, "min_price_per_sqft": 7500.0, "max_price_per_sqft": 10500.0, "avg_monthly_rent_inr": 42000.0, "avg_gross_rental_yield_pct": 4.60, "data_source": "SIMULATED DEMO: Hyderabad IT Hub Index 2026"},
            {"city": "Hyderabad", "locality": "Hitec City", "property_type": "Apartment", "avg_price_per_sqft": 9200.0, "min_price_per_sqft": 8000.0, "max_price_per_sqft": 11500.0, "avg_monthly_rent_inr": 45000.0, "avg_gross_rental_yield_pct": 4.55, "data_source": "SIMULATED DEMO: Cyberabad Tech Corridor"},
            {"city": "Hyderabad", "locality": "Kondapur", "property_type": "Apartment", "avg_price_per_sqft": 8100.0, "min_price_per_sqft": 7000.0, "max_price_per_sqft": 9800.0, "avg_monthly_rent_inr": 36000.0, "avg_gross_rental_yield_pct": 4.40, "data_source": "SIMULATED DEMO: West Hyderabad Micro-Index"},
            # Bengaluru
            {"city": "Bengaluru", "locality": "Whitefield", "property_type": "Apartment", "avg_price_per_sqft": 8900.0, "min_price_per_sqft": 7600.0, "max_price_per_sqft": 11000.0, "avg_monthly_rent_inr": 48000.0, "avg_gross_rental_yield_pct": 4.25, "data_source": "SIMULATED DEMO: East Bengaluru IT Corridor"},
            {"city": "Bengaluru", "locality": "Bellandur", "property_type": "Apartment", "avg_price_per_sqft": 10500.0, "min_price_per_sqft": 9000.0, "max_price_per_sqft": 13000.0, "avg_monthly_rent_inr": 55000.0, "avg_gross_rental_yield_pct": 4.10, "data_source": "SIMULATED DEMO: Outer Ring Road Tech Belt"},
            {"city": "Bengaluru", "locality": "Electronic City", "property_type": "Apartment", "avg_price_per_sqft": 5800.0, "min_price_per_sqft": 4800.0, "max_price_per_sqft": 7200.0, "avg_monthly_rent_inr": 28000.0, "avg_gross_rental_yield_pct": 4.75, "data_source": "SIMULATED DEMO: South Bengaluru Tech Zone"},
            # Pune
            {"city": "Pune", "locality": "Hinjewadi", "property_type": "Apartment", "avg_price_per_sqft": 7600.0, "min_price_per_sqft": 6400.0, "max_price_per_sqft": 9200.0, "avg_monthly_rent_inr": 32000.0, "avg_gross_rental_yield_pct": 4.95, "data_source": "SIMULATED DEMO: Pune Tech Park Index"},
            {"city": "Pune", "locality": "Kharadi", "property_type": "Apartment", "avg_price_per_sqft": 8400.0, "min_price_per_sqft": 7200.0, "max_price_per_sqft": 10200.0, "avg_monthly_rent_inr": 36000.0, "avg_gross_rental_yield_pct": 4.45, "data_source": "SIMULATED DEMO: East Pune Commercial Hub"},
            # Mumbai
            {"city": "Mumbai", "locality": "Bandra West", "property_type": "Apartment", "avg_price_per_sqft": 42000.0, "min_price_per_sqft": 35000.0, "max_price_per_sqft": 58000.0, "avg_monthly_rent_inr": 85000.0, "avg_gross_rental_yield_pct": 2.75, "data_source": "SIMULATED DEMO: Mumbai Prime Western Suburbs"},
            {"city": "Mumbai", "locality": "Andheri East", "property_type": "Apartment", "avg_price_per_sqft": 21000.0, "min_price_per_sqft": 18000.0, "max_price_per_sqft": 26000.0, "avg_monthly_rent_inr": 48000.0, "avg_gross_rental_yield_pct": 3.10, "data_source": "SIMULATED DEMO: Mumbai Commercial Hub"},
            # Chennai
            {"city": "Chennai", "locality": "OMR (Old Mahabalipuram Rd)", "property_type": "Apartment", "avg_price_per_sqft": 6200.0, "min_price_per_sqft": 5200.0, "max_price_per_sqft": 7800.0, "avg_monthly_rent_inr": 28000.0, "avg_gross_rental_yield_pct": 4.35, "data_source": "SIMULATED DEMO: Chennai IT Expressway"},
            {"city": "Chennai", "locality": "Anna Nagar", "property_type": "Apartment", "avg_price_per_sqft": 13500.0, "min_price_per_sqft": 11500.0, "max_price_per_sqft": 17000.0, "avg_monthly_rent_inr": 45000.0, "avg_gross_rental_yield_pct": 3.20, "data_source": "SIMULATED DEMO: Central Chennai Prime"},
            # Tier-2 AP Hubs
            {"city": "Visakhapatnam", "locality": "Madhurawada", "property_type": "Apartment", "avg_price_per_sqft": 4800.0, "min_price_per_sqft": 4000.0, "max_price_per_sqft": 5800.0, "avg_monthly_rent_inr": 20000.0, "avg_gross_rental_yield_pct": 4.65, "data_source": "SIMULATED DEMO: Vizag IT Special Economic Zone"},
            {"city": "Vijayawada", "locality": "Tadigadapa / Poranki", "property_type": "Apartment", "avg_price_per_sqft": 4300.0, "min_price_per_sqft": 3600.0, "max_price_per_sqft": 5200.0, "avg_monthly_rent_inr": 18000.0, "avg_gross_rental_yield_pct": 4.50, "data_source": "SIMULATED DEMO: Amaravati Capital Region"},
            {"city": "Guntur", "locality": "Chandramouli Nagar", "property_type": "Apartment", "avg_price_per_sqft": 3900.0, "min_price_per_sqft": 3200.0, "max_price_per_sqft": 4800.0, "avg_monthly_rent_inr": 15000.0, "avg_gross_rental_yield_pct": 4.40, "data_source": "SIMULATED DEMO: Central Guntur Residential"},
        ]

        count = 0
        for b in demo_benchmarks:
            existing = (
                db.query(MarketBenchmark)
                .filter(
                    func.lower(MarketBenchmark.city) == b["city"].lower(),
                    func.lower(MarketBenchmark.locality) == b["locality"].lower(),
                    MarketBenchmark.property_type == b["property_type"],
                )
                .first()
            )
            if not existing:
                record = MarketBenchmark(
                    city=b["city"],
                    locality=b["locality"],
                    property_type=b["property_type"],
                    avg_price_per_sqft=b["avg_price_per_sqft"],
                    min_price_per_sqft=b["min_price_per_sqft"],
                    max_price_per_sqft=b["max_price_per_sqft"],
                    avg_monthly_rent_inr=b["avg_monthly_rent_inr"],
                    avg_gross_rental_yield_pct=b["avg_gross_rental_yield_pct"],
                    data_source=b["data_source"],
                    collection_date="2026-Q1",
                    verification_status="simulated_demo",
                    is_demo=True,
                    notes="Demonstration benchmark dataset for analytical comparison.",
                )
                db.add(record)
                count += 1

        db.commit()
        return count


benchmark_service = BenchmarkService()

