import csv
import io
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.property import Property
from app.schemas.property import CSVImportResult, CSVImportRowError, PropertyCreate
from app.services.property_service import PropertyService


# Flexible column header mappings (case-insensitive & stripped)
HEADER_MAPPINGS = {
    "title": ["title", "property_title", "property title", "name", "listing_title"],
    "city": ["city", "city_name", "location_city"],
    "locality": ["locality", "suburb", "area", "neighborhood", "micro_market", "micromarket"],
    "state": ["state", "province", "region"],
    "property_type": ["property_type", "type", "property type", "category"],
    "bedrooms": ["bedrooms", "bhk", "bedroom", "beds", "bed_count"],
    "bathrooms": ["bathrooms", "baths", "bathroom", "bath_count"],
    "built_up_area_sqft": ["built_up_area_sqft", "area_sqft", "area", "sqft", "built_up_area", "carpet_area"],
    "purchase_price_inr": ["purchase_price_inr", "price_inr", "price", "purchase_price", "cost_inr", "cost"],
    "expected_monthly_rent_inr": ["expected_monthly_rent_inr", "monthly_rent", "rent", "rent_inr", "expected_rent"],
    "monthly_maintenance_inr": ["monthly_maintenance_inr", "maintenance", "maintenance_inr", "maintenance_fee"],
    "property_age": ["property_age", "age", "construction_age", "age_of_property"],
    "listing_source": ["listing_source", "source", "portal"],
    "source_url": ["source_url", "url", "link", "listing_url"],
    "listing_date": ["listing_date", "date", "created_date"],
    "is_demo": ["is_demo", "demo", "simulated"],
}


def sanitize_csv_text(val: Optional[str]) -> Optional[str]:
    """Sanitize strings against CSV Formula Injection (=, @, +, -, tab, CR)."""
    if not val:
        return val
    s = val.strip()
    if s.startswith(("=", "@", "\t", "\r")):
        return "'" + s
    if s.startswith(("+", "-")):
        try:
            float(s)
            return s
        except ValueError:
            return "'" + s
    return s


class CSVService:
    @staticmethod
    def get_sample_csv_content() -> str:
        """Generate a valid sample CSV string that users can download as a template."""
        output = io.StringIO()
        fieldnames = [
            "title",
            "city",
            "locality",
            "state",
            "property_type",
            "bedrooms",
            "bathrooms",
            "built_up_area_sqft",
            "purchase_price_inr",
            "expected_monthly_rent_inr",
            "monthly_maintenance_inr",
            "property_age",
            "listing_source",
            "source_url",
            "listing_date",
            "is_demo",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # Add 2 sample rows
        writer.writerow({
            "title": "3 BHK Premium Flat in Gachibowli",
            "city": "Hyderabad",
            "locality": "Gachibowli",
            "state": "Telangana",
            "property_type": "Apartment",
            "bedrooms": "3",
            "bathrooms": "3",
            "built_up_area_sqft": "1850",
            "purchase_price_inr": "14500000",
            "expected_monthly_rent_inr": "55000",
            "monthly_maintenance_inr": "4500",
            "property_age": "0-2 years",
            "listing_source": "Direct Owner",
            "source_url": "https://example.com/listing/hyd-101",
            "listing_date": "2026-10-25",
            "is_demo": "True",
        })
        writer.writerow({
            "title": "2 BHK Modern Apartment in Whitefield",
            "city": "Bengaluru",
            "locality": "Whitefield",
            "state": "Karnataka",
            "property_type": "Apartment",
            "bedrooms": "2",
            "bathrooms": "2",
            "built_up_area_sqft": "1200",
            "purchase_price_inr": "9500000",
            "expected_monthly_rent_inr": "42000",
            "monthly_maintenance_inr": "3200",
            "property_age": "3-5 years",
            "listing_source": "Builder Direct",
            "source_url": "https://example.com/listing/blr-202",
            "listing_date": "2026-10-28",
            "is_demo": "True",
        })
        return output.getvalue()

    @staticmethod
    def parse_and_import(db: Session, csv_content: str) -> CSVImportResult:
        """
        Parse CSV content, validate rows, check for duplicates, and commit valid entries.
        Never silently discards invalid rows.
        """
        # Handle UTF-8 with BOM or carriage returns
        cleaned_content = csv_content.strip()
        if not cleaned_content:
            return CSVImportResult(
                total_rows=0,
                successful_imports=0,
                failed_imports=0,
                skipped_duplicates=0,
                errors=[CSVImportRowError(row_number=0, error="CSV file is empty")],
            )

        reader = csv.reader(io.StringIO(cleaned_content))
        rows = list(reader)

        if not rows:
            return CSVImportResult(
                total_rows=0,
                successful_imports=0,
                failed_imports=0,
                skipped_duplicates=0,
                errors=[CSVImportRowError(row_number=0, error="No rows found in CSV")],
            )

        raw_headers = [h.strip().lower() for h in rows[0]]
        
        # Map raw header names to canonical schema keys
        header_map: Dict[str, int] = {}
        for canonical_key, aliases in HEADER_MAPPINGS.items():
            for idx, raw_h in enumerate(raw_headers):
                if raw_h in aliases:
                    header_map[canonical_key] = idx
                    break

        # Check required columns
        required_keys = ["title", "city", "locality", "built_up_area_sqft", "purchase_price_inr"]
        missing_required = [k for k in required_keys if k not in header_map]
        if missing_required:
            return CSVImportResult(
                total_rows=len(rows) - 1,
                successful_imports=0,
                failed_imports=len(rows) - 1,
                skipped_duplicates=0,
                errors=[
                    CSVImportRowError(
                        row_number=1,
                        error=f"Missing essential header columns: {', '.join(missing_required)}. Found headers: {', '.join(raw_headers)}",
                    )
                ],
            )

        successful_count = 0
        failed_count = 0
        duplicate_count = 0
        errors: List[CSVImportRowError] = []

        # Process each data row
        for row_idx, row_values in enumerate(rows[1:], start=2):
            if not row_values or all(not str(v).strip() for v in row_values):
                continue  # skip completely blank rows

            row_data: Dict[str, Any] = {}
            for canonical_key, col_idx in header_map.items():
                if col_idx < len(row_values):
                    row_data[canonical_key] = row_values[col_idx].strip()
                else:
                    row_data[canonical_key] = ""

            # Row Validation
            row_title = row_data.get("title", f"Row {row_idx}")
            try:
                # 1. Text validations
                title = row_data.get("title", "").strip()
                if not title or len(title) < 3:
                    raise ValueError("Property title must be at least 3 characters long")

                city = row_data.get("city", "").strip()
                if not city or len(city) < 2:
                    raise ValueError("City must be at least 2 characters long")

                locality = row_data.get("locality", "").strip()
                if not locality or len(locality) < 2:
                    raise ValueError("Locality must be at least 2 characters long")

                state = row_data.get("state", "").strip() or None
                property_type = row_data.get("property_type", "").strip() or "Apartment"

                # 2. Numeric & financial validations
                try:
                    area = float(row_data.get("built_up_area_sqft", 0))
                    if area <= 0:
                        raise ValueError()
                except Exception:
                    raise ValueError("Built-up area (sqft) must be a strictly positive number")

                try:
                    price = float(row_data.get("purchase_price_inr", 0))
                    if price <= 0:
                        raise ValueError()
                except Exception:
                    raise ValueError("Purchase price (INR) must be a strictly positive number (> 0)")

                try:
                    raw_rent = row_data.get("expected_monthly_rent_inr", "0")
                    rent = float(raw_rent) if raw_rent else 0.0
                    if rent < 0:
                        raise ValueError()
                except Exception:
                    raise ValueError("Expected monthly rent cannot be negative")

                try:
                    raw_maint = row_data.get("monthly_maintenance_inr", "0")
                    maint = float(raw_maint) if raw_maint else 0.0
                    if maint < 0:
                        raise ValueError()
                except Exception:
                    raise ValueError("Monthly maintenance cannot be negative")

                try:
                    raw_beds = row_data.get("bedrooms", "1")
                    bedrooms = int(float(raw_beds)) if raw_beds else 1
                    if bedrooms < 0:
                        raise ValueError()
                except Exception:
                    raise ValueError("Bedrooms count cannot be negative")

                try:
                    raw_baths = row_data.get("bathrooms", "1")
                    bathrooms = int(float(raw_baths)) if raw_baths else 1
                    if bathrooms < 0:
                        raise ValueError()
                except Exception:
                    raise ValueError("Bathrooms count cannot be negative")

                property_age = sanitize_csv_text(row_data.get("property_age", "").strip() or None)
                listing_source = sanitize_csv_text(row_data.get("listing_source", "").strip() or "CSV Import")
                source_url = sanitize_csv_text(row_data.get("source_url", "").strip() or None)
                listing_date = sanitize_csv_text(row_data.get("listing_date", "").strip() or None)
                title = sanitize_csv_text(title)
                city = sanitize_csv_text(city)
                locality = sanitize_csv_text(locality)
                if state:
                    state = sanitize_csv_text(state)
                
                raw_demo = str(row_data.get("is_demo", "")).lower()
                is_demo = raw_demo in ["true", "1", "yes", "demo"]

                # 3. Duplicate Prevention
                # Check for existing property with identical title + city + locality
                existing = db.query(Property).filter(
                    func.lower(Property.title) == title.lower(),
                    func.lower(Property.city) == city.lower(),
                    func.lower(Property.locality) == locality.lower(),
                ).first()

                if existing:
                    duplicate_count += 1
                    errors.append(
                        CSVImportRowError(
                            row_number=row_idx,
                            property_title=title,
                            error=f"Duplicate detected: Property '{title}' already exists in {city} ({locality}) with ID #{existing.id}",
                            raw_data=row_data,
                        )
                    )
                    continue

                # 4. Create property
                create_dto = PropertyCreate(
                    title=title,
                    city=city,
                    locality=locality,
                    state=state,
                    property_type=property_type,
                    bedrooms=bedrooms,
                    bathrooms=bathrooms,
                    built_up_area_sqft=area,
                    purchase_price_inr=price,
                    expected_monthly_rent_inr=rent,
                    monthly_maintenance_inr=maint,
                    property_age=property_age,
                    listing_source=listing_source,
                    source_url=source_url,
                    listing_date=listing_date,
                    is_demo=is_demo,
                )
                PropertyService.create_property(db, create_dto)
                successful_count += 1

            except Exception as e:
                failed_count += 1
                errors.append(
                    CSVImportRowError(
                        row_number=row_idx,
                        property_title=row_title,
                        error=str(e),
                        raw_data=row_data,
                    )
                )

        total_processed = len(rows) - 1
        return CSVImportResult(
            total_rows=total_processed,
            successful_imports=successful_count,
            failed_imports=failed_count + duplicate_count,
            skipped_duplicates=duplicate_count,
            errors=errors,
        )


csv_service = CSVService()

