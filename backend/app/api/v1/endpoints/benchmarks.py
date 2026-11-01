from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.benchmark import (
    BenchmarkResponse,
    BenchmarkCreate,
    BenchmarkListResponse,
    BenchmarkImportResponse,
)
from app.services.benchmark_service import benchmark_service

router = APIRouter()


@router.get("", response_model=BenchmarkListResponse)
def list_benchmarks(
    city: Optional[str] = Query(None, description="Filter by city name"),
    locality: Optional[str] = Query(None, description="Filter by locality substring"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    verification_status: Optional[str] = Query(None, description="'verified_market', 'user_submitted', 'simulated_demo'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List market benchmarks with provenance and verification status breakdown.
    Demo benchmarks are distinctly tagged from user-submitted or verified market data.
    """
    skip = (page - 1) * page_size
    items, total, provenance = benchmark_service.get_benchmarks(
        db,
        city=city,
        locality=locality,
        property_type=property_type,
        verification_status=verification_status,
        skip=skip,
        limit=page_size,
    )

    return BenchmarkListResponse(
        total=total,
        items=items,
        provenance_summary=provenance,
    )


@router.post("", response_model=BenchmarkResponse, status_code=status.HTTP_201_CREATED)
def create_benchmark(
    benchmark: BenchmarkCreate,
    db: Session = Depends(get_db),
):
    """
    Add a new benchmark dataset record manually.
    """
    created = benchmark_service.create_benchmark(db, benchmark)
    return created


@router.post("/import-csv", response_model=BenchmarkImportResponse)
async def import_benchmarks_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Bulk import market benchmark datasets via CSV upload with duplicate prevention.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid .csv file.",
        )

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="CSV file exceeds maximum allowed size of 5 MB",
        )
    result = benchmark_service.import_benchmarks_csv(db, contents)
    return BenchmarkImportResponse(**result)


@router.get("/match", response_model=Optional[BenchmarkResponse])
def get_matching_benchmark(
    city: str = Query(..., description="Target property city"),
    locality: Optional[str] = Query(None, description="Target property locality"),
    property_type: Optional[str] = Query("Apartment", description="Target property type"),
    db: Session = Depends(get_db),
):
    """
    Query the nearest matching benchmark for a given property locality.
    Returns null with 200 OK if insufficient market data is available.
    """
    match = benchmark_service.get_matching_benchmark(db, city, locality, property_type)
    return match

