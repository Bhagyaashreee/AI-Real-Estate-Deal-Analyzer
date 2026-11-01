from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.property import Property
from app.schemas.property import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyListResponse,
    CSVImportResult,
)
from app.services.property_service import PropertyService, to_response_dto
from app.services.csv_service import csv_service
from app.services.seed_data import seed_demo_properties
from app.utils.financial import format_inr

router = APIRouter()


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Return aggregated KPI metrics for the Indian Real Estate investment dashboard.
    Calculates live statistics directly from the SQLite database.
    """
    total_deals = db.query(Property).count()

    if total_deals == 0:
        return {
            "kpis": {
                "total_deals_analyzed": 0,
                "average_rental_yield_pct": 0.0,
                "undervalued_opportunities": 0,
                "average_portfolio_ticket_inr": 0.0,
                "average_portfolio_ticket_formatted": "₹0",
                "top_yielding_city": "N/A",
                "benchmark_national_yield_pct": 3.25,
            },
            "supported_cities": [],
            "currency": "INR (₹)",
        }

    # Calculations from DB
    avg_yield = db.query(func.avg(Property.gross_rental_yield_pct)).scalar() or 0.0
    avg_price = db.query(func.avg(Property.purchase_price_inr)).scalar() or 0.0
    undervalued_count = db.query(Property).filter(Property.valuation_status == "Undervalued").count()

    # Top yielding city
    city_yields = (
        db.query(Property.city, func.avg(Property.gross_rental_yield_pct).label("avg_y"))
        .group_by(Property.city)
        .order_by(func.avg(Property.gross_rental_yield_pct).desc())
        .first()
    )
    top_city = city_yields[0] if city_yields else "Pune"

    distinct_cities = [c[0] for c in db.query(Property.city).distinct().order_by(Property.city).all()]

    return {
        "kpis": {
            "total_deals_analyzed": total_deals,
            "average_rental_yield_pct": round(float(avg_yield), 2),
            "undervalued_opportunities": undervalued_count,
            "average_portfolio_ticket_inr": round(float(avg_price), 2),
            "average_portfolio_ticket_formatted": format_inr(avg_price),
            "top_yielding_city": top_city,
            "benchmark_national_yield_pct": 3.25,
        },
        "supported_cities": distinct_cities,
        "currency": "INR (₹)",
    }


@router.get("/template-csv")
def download_csv_template():
    """Download a pre-formatted sample CSV template for property ingestion."""
    content = csv_service.get_sample_csv_content()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="indian_properties_template.csv"'},
    )


@router.post("/import-csv", response_model=CSVImportResult)
async def import_properties_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Import properties from a CSV file.
    Validates column headers, checks data types, prevents accidental duplicates,
    and returns granular row-by-row error diagnostics without silent data drops.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a CSV file with a .csv extension",
        )

    content_bytes = await file.read()
    if len(content_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="CSV file exceeds maximum allowed size of 5 MB",
        )

    try:
        content_str = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            content_str = content_bytes.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to decode CSV file. Please ensure it is saved in UTF-8 format.",
            )

    result = csv_service.parse_and_import(db, content_str)
    return result


@router.post("/seed")
def seed_properties(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Seed the database with ~20 simulated Indian property listings (idempotent)."""
    result = seed_demo_properties(db)
    return {
        "message": f"Successfully processed seed catalog. {result['inserted']} new properties added, {result['skipped']} duplicates skipped.",
        "details": result,
    }


@router.post("", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_property(
    prop_in: PropertyCreate,
    db: Session = Depends(get_db),
):
    """Create a new Indian real estate property with computed financial and valuation metrics."""
    # Check duplicate
    existing = db.query(Property).filter(
        func.lower(Property.title) == prop_in.title.lower(),
        func.lower(Property.city) == prop_in.city.lower(),
        func.lower(Property.locality) == prop_in.locality.lower(),
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property with title '{prop_in.title}' already exists in {prop_in.city} ({prop_in.locality}) with ID #{existing.id}.",
        )

    db_prop = PropertyService.create_property(db, prop_in)
    return to_response_dto(db_prop)


@router.get("", response_model=PropertyListResponse)
def list_properties(
    city: Optional[str] = Query(None, description="Filter by city name"),
    locality: Optional[str] = Query(None, description="Filter by locality or micro-market"),
    state: Optional[str] = Query(None, description="Filter by state"),
    property_type: Optional[str] = Query(None, description="Filter by property type (Apartment, Villa, etc.)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum purchase price in INR"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum purchase price in INR"),
    min_bedrooms: Optional[int] = Query(None, ge=0, description="Minimum bedrooms / BHK"),
    max_bedrooms: Optional[int] = Query(None, ge=0, description="Maximum bedrooms / BHK"),
    min_area: Optional[float] = Query(None, ge=0, description="Minimum built-up area in sq.ft"),
    max_area: Optional[float] = Query(None, ge=0, description="Maximum built-up area in sq.ft"),
    min_yield: Optional[float] = Query(None, ge=0, description="Minimum gross rental yield (%)"),
    valuation_status: Optional[str] = Query(None, description="Undervalued, Fair Value, Overpriced"),
    is_demo: Optional[bool] = Query(None, description="Filter demo vs user properties"),
    sort_by: str = Query("created_at", description="Field to sort by: created_at, price_inr, expected_monthly_rent_inr, gross_rental_yield_pct, built_up_area_sqft, bedrooms"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List properties with comprehensive multi-criteria filtering, sensible sorting, and pagination."""
    items, total, total_pages = PropertyService.search_properties(
        db=db,
        city=city,
        locality=locality,
        state=state,
        property_type=property_type,
        min_price=min_price,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
        max_bedrooms=max_bedrooms,
        min_area=min_area,
        max_area=max_area,
        min_yield=min_yield,
        valuation_status=valuation_status,
        is_demo=is_demo,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    response_items = [to_response_dto(p) for p in items]
    return PropertyListResponse(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: int,
    db: Session = Depends(get_db),
):
    """Get full details of a property by ID."""
    prop = PropertyService.get_property(db, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} was not found",
        )
    return to_response_dto(prop)


@router.put("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: int,
    prop_update: PropertyUpdate,
    db: Session = Depends(get_db),
):
    """Update property details and recalculate financial metrics."""
    updated = PropertyService.update_property(db, property_id, prop_update)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} was not found",
        )
    return to_response_dto(updated)


@router.delete("/{property_id}")
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
):
    """Delete a property by ID."""
    deleted = PropertyService.delete_property(db, property_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} was not found",
        )
    return {
        "message": "Property deleted successfully",
        "id": property_id,
        "status": "success",
    }
