from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.property import Property
from app.schemas.property import PropertyCreate
from app.services.property_service import PropertyService

# 24 realistic simulated Indian real estate investment listings across the 8 required cities.
# CLEARLY MARKED AS DEMO DATA - simulated for analytics testing purposes only.
DEMO_INDIAN_PROPERTIES: List[Dict[str, Any]] = [
    # 1. Hyderabad (IT Corridor & Financial District)
    {
        "title": "[DEMO] 3 BHK Gated High-Rise in Gachibowli",
        "city": "Hyderabad",
        "locality": "Gachibowli",
        "state": "Telangana",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 1850.0,
        "purchase_price_inr": 16500000.0,  # ₹1.65 Cr
        "expected_monthly_rent_inr": 62000.0,
        "monthly_maintenance_inr": 4800.0,
        "property_age": "0-2 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/hyderabad/gachibowli-highrise",
        "listing_date": "2026-10-15",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 2 BHK Tech Corridor Flat in Hitec City",
        "city": "Hyderabad",
        "locality": "Hitec City",
        "state": "Telangana",
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "built_up_area_sqft": 1250.0,
        "purchase_price_inr": 11500000.0,  # ₹1.15 Cr
        "expected_monthly_rent_inr": 48000.0,
        "monthly_maintenance_inr": 3500.0,
        "property_age": "3-5 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/hyderabad/hiteccity-flat",
        "listing_date": "2026-10-18",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 4 BHK Luxury Villa in Kondapur",
        "city": "Hyderabad",
        "locality": "Kondapur",
        "state": "Telangana",
        "property_type": "Villa",
        "bedrooms": 4,
        "bathrooms": 4,
        "built_up_area_sqft": 3100.0,
        "purchase_price_inr": 32500000.0,  # ₹3.25 Cr
        "expected_monthly_rent_inr": 110000.0,
        "monthly_maintenance_inr": 8000.0,
        "property_age": "1-3 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/hyderabad/kondapur-villa",
        "listing_date": "2026-10-20",
        "is_demo": True,
    },

    # 2. Bengaluru (Tech Hubs & Peripheral Corridors)
    {
        "title": "[DEMO] 3 BHK IT Corridor Apartment in Whitefield",
        "city": "Bengaluru",
        "locality": "Whitefield",
        "state": "Karnataka",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 1680.0,
        "purchase_price_inr": 14500000.0,  # ₹1.45 Cr
        "expected_monthly_rent_inr": 54000.0,
        "monthly_maintenance_inr": 4200.0,
        "property_age": "2-4 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/bengaluru/whitefield-apt",
        "listing_date": "2026-10-12",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 2 BHK Compact Home in Electronic City Phase 1",
        "city": "Bengaluru",
        "locality": "Electronic City",
        "state": "Karnataka",
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "built_up_area_sqft": 1050.0,
        "purchase_price_inr": 7200000.0,  # ₹72 Lakhs
        "expected_monthly_rent_inr": 31000.0,
        "monthly_maintenance_inr": 2800.0,
        "property_age": "4-6 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/bengaluru/ecity-home",
        "listing_date": "2026-10-14",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 3 BHK Premium Duplex in Indiranagar",
        "city": "Bengaluru",
        "locality": "Indiranagar",
        "state": "Karnataka",
        "property_type": "Independent House",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 2400.0,
        "purchase_price_inr": 38000000.0,  # ₹3.80 Cr
        "expected_monthly_rent_inr": 95000.0,
        "monthly_maintenance_inr": 5000.0,
        "property_age": "6-10 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/bengaluru/indiranagar-duplex",
        "listing_date": "2026-10-22",
        "is_demo": True,
    },

    # 3. Chennai (OMR IT Expressway & Core Hubs)
    {
        "title": "[DEMO] 3 BHK Sea-Breeze Flat on OMR IT Expressway",
        "city": "Chennai",
        "locality": "OMR (Sholinganallur)",
        "state": "Tamil Nadu",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 2,
        "built_up_area_sqft": 1520.0,
        "purchase_price_inr": 10500000.0,  # ₹1.05 Cr
        "expected_monthly_rent_inr": 41000.0,
        "monthly_maintenance_inr": 3500.0,
        "property_age": "1-3 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/chennai/omr-sholinganallur",
        "listing_date": "2026-10-10",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 2 BHK Transit-Oriented Home in Velachery",
        "city": "Chennai",
        "locality": "Velachery",
        "state": "Tamil Nadu",
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "built_up_area_sqft": 1100.0,
        "purchase_price_inr": 8800000.0,  # ₹88 Lakhs
        "expected_monthly_rent_inr": 32000.0,
        "monthly_maintenance_inr": 2500.0,
        "property_age": "5-8 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/chennai/velachery-home",
        "listing_date": "2026-10-16",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 3 BHK Prime Residential Residence in Anna Nagar",
        "city": "Chennai",
        "locality": "Anna Nagar",
        "state": "Tamil Nadu",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 1900.0,
        "purchase_price_inr": 26000000.0,  # ₹2.60 Cr
        "expected_monthly_rent_inr": 68000.0,
        "monthly_maintenance_inr": 4500.0,
        "property_age": "3-5 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/chennai/annanagar-residence",
        "listing_date": "2026-10-21",
        "is_demo": True,
    },

    # 4. Pune (Tech Clusters & West Pune)
    {
        "title": "[DEMO] 2 BHK Smart Apartment in Hinjewadi Phase 1",
        "city": "Pune",
        "locality": "Hinjewadi",
        "state": "Maharashtra",
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "built_up_area_sqft": 1050.0,
        "purchase_price_inr": 8200000.0,  # ₹82 Lakhs
        "expected_monthly_rent_inr": 34000.0,
        "monthly_maintenance_inr": 2800.0,
        "property_age": "0-2 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/pune/hinjewadi-smart",
        "listing_date": "2026-10-11",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 3 BHK Luxury Gated Highrise in Wakad",
        "city": "Pune",
        "locality": "Wakad",
        "state": "Maharashtra",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 1480.0,
        "purchase_price_inr": 12200000.0,  # ₹1.22 Cr
        "expected_monthly_rent_inr": 46000.0,
        "monthly_maintenance_inr": 3800.0,
        "property_age": "2-4 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/pune/wakad-highrise",
        "listing_date": "2026-10-19",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 3 BHK Heritage Town Apartment in Kothrud",
        "city": "Pune",
        "locality": "Kothrud",
        "state": "Maharashtra",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 2,
        "built_up_area_sqft": 1380.0,
        "purchase_price_inr": 16000000.0,  # ₹1.60 Cr
        "expected_monthly_rent_inr": 42000.0,
        "monthly_maintenance_inr": 3000.0,
        "property_age": "6-10 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/pune/kothrud-town",
        "listing_date": "2026-10-24",
        "is_demo": True,
    },

    # 5. Mumbai (Western Suburbs & Growth Corridors)
    {
        "title": "[DEMO] 2 BHK Coastal High-Rise in Bandra West",
        "city": "Mumbai",
        "locality": "Bandra West",
        "state": "Maharashtra",
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "built_up_area_sqft": 920.0,
        "purchase_price_inr": 38000000.0,  # ₹3.80 Cr
        "expected_monthly_rent_inr": 88000.0,
        "monthly_maintenance_inr": 6500.0,
        "property_age": "4-7 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/mumbai/bandra-west",
        "listing_date": "2026-10-08",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 2 BHK Lakeview Modern Tower in Powai",
        "city": "Mumbai",
        "locality": "Powai",
        "state": "Maharashtra",
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "built_up_area_sqft": 880.0,
        "purchase_price_inr": 21000000.0,  # ₹2.10 Cr
        "expected_monthly_rent_inr": 62000.0,
        "monthly_maintenance_inr": 4500.0,
        "property_age": "3-5 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/mumbai/powai-tower",
        "listing_date": "2026-10-17",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 3 BHK Master Community in Thane West",
        "city": "Mumbai",
        "locality": "Thane West",
        "state": "Maharashtra",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 1350.0,
        "purchase_price_inr": 17500000.0,  # ₹1.75 Cr
        "expected_monthly_rent_inr": 50000.0,
        "monthly_maintenance_inr": 4000.0,
        "property_age": "1-3 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/mumbai/thane-west-community",
        "listing_date": "2026-10-23",
        "is_demo": True,
    },

    # 6. Guntur (Andhra Pradesh Growth Region)
    {
        "title": "[DEMO] 3 BHK Spacious Apartment on Amaravati Road",
        "city": "Guntur",
        "locality": "Amaravati Road",
        "state": "Andhra Pradesh",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 1650.0,
        "purchase_price_inr": 6800000.0,  # ₹68 Lakhs
        "expected_monthly_rent_inr": 24000.0,
        "monthly_maintenance_inr": 1800.0,
        "property_age": "0-2 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/guntur/amaravati-rd",
        "listing_date": "2026-10-09",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 2 BHK Residential Flat in Lakshmipuram",
        "city": "Guntur",
        "locality": "Lakshmipuram",
        "state": "Andhra Pradesh",
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "built_up_area_sqft": 1150.0,
        "purchase_price_inr": 4800000.0,  # ₹48 Lakhs
        "expected_monthly_rent_inr": 18000.0,
        "monthly_maintenance_inr": 1400.0,
        "property_age": "3-5 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/guntur/lakshmipuram-flat",
        "listing_date": "2026-10-13",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 3 BHK Independent House in Gujanagundla",
        "city": "Guntur",
        "locality": "Gujanagundla",
        "state": "Andhra Pradesh",
        "property_type": "Independent House",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 2100.0,
        "purchase_price_inr": 9200000.0,  # ₹92 Lakhs
        "expected_monthly_rent_inr": 30000.0,
        "monthly_maintenance_inr": 1500.0,
        "property_age": "2-4 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/guntur/gujanagundla-house",
        "listing_date": "2026-10-25",
        "is_demo": True,
    },

    # 7. Vijayawada (Commercial & Capital Region Hub)
    {
        "title": "[DEMO] 3 BHK Premium Residence near Benz Circle",
        "city": "Vijayawada",
        "locality": "Benz Circle",
        "state": "Andhra Pradesh",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 1780.0,
        "purchase_price_inr": 11800000.0,  # ₹1.18 Cr
        "expected_monthly_rent_inr": 38000.0,
        "monthly_maintenance_inr": 2500.0,
        "property_age": "1-3 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/vijayawada/benz-circle",
        "listing_date": "2026-10-15",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 2 BHK Suburban Apartment in Poranki",
        "city": "Vijayawada",
        "locality": "Poranki",
        "state": "Andhra Pradesh",
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "built_up_area_sqft": 1200.0,
        "purchase_price_inr": 5500000.0,  # ₹55 Lakhs
        "expected_monthly_rent_inr": 20000.0,
        "monthly_maintenance_inr": 1500.0,
        "property_age": "2-4 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/vijayawada/poranki-suburban",
        "listing_date": "2026-10-18",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 4 BHK Gated Villa near Enikepadu",
        "city": "Vijayawada",
        "locality": "Enikepadu",
        "state": "Andhra Pradesh",
        "property_type": "Villa",
        "bedrooms": 4,
        "bathrooms": 4,
        "built_up_area_sqft": 2800.0,
        "purchase_price_inr": 18500000.0,  # ₹1.85 Cr
        "expected_monthly_rent_inr": 55000.0,
        "monthly_maintenance_inr": 3500.0,
        "property_age": "0-2 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/vijayawada/enikepadu-villa",
        "listing_date": "2026-10-22",
        "is_demo": True,
    },

    # 8. Visakhapatnam (Coastal Tech & Port City)
    {
        "title": "[DEMO] 3 BHK IT Corridor Residence in Madhurawada",
        "city": "Visakhapatnam",
        "locality": "Madhurawada",
        "state": "Andhra Pradesh",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 2,
        "built_up_area_sqft": 1550.0,
        "purchase_price_inr": 7800000.0,  # ₹78 Lakhs
        "expected_monthly_rent_inr": 28000.0,
        "monthly_maintenance_inr": 2000.0,
        "property_age": "1-3 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/visakhapatnam/madhurawada-it",
        "listing_date": "2026-10-14",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 3 BHK Ocean-View Home along Beach Road",
        "city": "Visakhapatnam",
        "locality": "Beach Road",
        "state": "Andhra Pradesh",
        "property_type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "built_up_area_sqft": 1950.0,
        "purchase_price_inr": 19000000.0,  # ₹1.90 Cr
        "expected_monthly_rent_inr": 58000.0,
        "monthly_maintenance_inr": 3500.0,
        "property_age": "4-6 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/visakhapatnam/beach-road-view",
        "listing_date": "2026-10-19",
        "is_demo": True,
    },
    {
        "title": "[DEMO] 2 BHK Prime Colony Flat in MVP Colony",
        "city": "Visakhapatnam",
        "locality": "MVP Colony",
        "state": "Andhra Pradesh",
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "built_up_area_sqft": 1180.0,
        "purchase_price_inr": 8200000.0,  # ₹82 Lakhs
        "expected_monthly_rent_inr": 26000.0,
        "monthly_maintenance_inr": 1800.0,
        "property_age": "5-8 years",
        "listing_source": "DEMO DATA",
        "source_url": "https://demo.local/visakhapatnam/mvp-colony",
        "listing_date": "2026-10-26",
        "is_demo": True,
    },
]


def seed_demo_properties(db: Session) -> Dict[str, int]:
    """
    Safely seed demo Indian property listings.
    Prevents duplicates by checking existing property titles in the city.
    """
    inserted = 0
    skipped = 0

    for item in DEMO_INDIAN_PROPERTIES:
        existing = db.query(Property).filter(
            func.lower(Property.title) == item["title"].lower(),
            func.lower(Property.city) == item["city"].lower(),
        ).first()

        if existing:
            skipped += 1
            continue

        dto = PropertyCreate(**item)
        PropertyService.create_property(db, dto)
        inserted += 1

    return {"inserted": inserted, "skipped": skipped, "total_demo_catalog": len(DEMO_INDIAN_PROPERTIES)}

