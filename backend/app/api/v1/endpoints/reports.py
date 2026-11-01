import re
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.property import Property
from app.models.benchmark import MarketBenchmark
from app.services.pdf_report_service import pdf_report_service
from app.services.ai_analysis_service import ai_analysis_service
from app.services.benchmark_service import benchmark_service
from app.schemas.report import ReportGenerateRequest, ReportMetadataResponse

router = APIRouter()


def _sanitize_filename(title: str, property_id: int) -> str:
    """Sanitize property title for clean, RFC-compliant Content-Disposition filename."""
    clean_title = re.sub(r"[^a-zA-Z0-9_\-]", "_", title)
    clean_title = re.sub(r"_+", "_", clean_title).strip("_")[:30]
    return f"DealAnalyzer_Report_Prop_{property_id}_{clean_title}.pdf"


def _resolve_property_and_benchmark(property_id: int, db: Session):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found.",
        )

    # Match benchmark if available
    benchmark_obj = benchmark_service.get_matching_benchmark(
        db=db,
        city=prop.city,
        locality=prop.locality,
        property_type=prop.property_type,
    )

    return prop, benchmark_obj


@router.get(
    "/{property_id}/pdf",
    summary="Download or stream PDF investment report",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Multi-page professional PDF investment report",
        },
        404: {"description": "Property not found"},
    },
)
def get_property_pdf_report(
    property_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate and stream a professional 10-page PDF investment report for a property.
    Streams directly with Content-Type: application/pdf and Content-Disposition inline.
    """
    prop, benchmark_obj = _resolve_property_and_benchmark(property_id, db)
    ai_cached = ai_analysis_service.get_cached_analysis(property_id)

    pdf_bytes = pdf_report_service.generate_pdf_report(
        prop=prop,
        ai_analysis=ai_cached,
        benchmark=benchmark_obj,
    )

    filename = _sanitize_filename(prop.title, property_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.post(
    "/{property_id}/generate",
    summary="Generate custom PDF report with configuration options",
    response_model=Optional[ReportMetadataResponse],
    responses={
        200: {
            "description": "Report metadata or direct PDF stream depending on return_pdf_direct flag",
        },
        404: {"description": "Property not found"},
    },
)
def generate_property_report(
    property_id: int,
    request: Optional[ReportGenerateRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Generate a PDF report with custom financial parameters (e.g. customized down payment,
    interest rate, vacancy rate, stamp duty).
    Returns either report metadata or direct PDF stream based on return_pdf_direct.
    """
    req = request or ReportGenerateRequest()
    prop, benchmark_obj = _resolve_property_and_benchmark(property_id, db)

    ai_analysis = None
    if req.include_ai:
        ai_analysis = ai_analysis_service.get_cached_analysis(property_id)

    custom_params = {
        "down_payment_pct": req.down_payment_pct,
        "annual_interest_rate_pct": req.annual_interest_rate_pct,
        "tenure_years": req.tenure_years,
        "vacancy_rate_pct": req.vacancy_rate_pct,
        "stamp_duty_pct": req.custom_stamp_duty_pct,
    }

    pdf_bytes = pdf_report_service.generate_pdf_report(
        prop=prop,
        ai_analysis=ai_analysis,
        custom_loan_params=custom_params,
        benchmark=benchmark_obj,
    )

    filename = _sanitize_filename(prop.title, property_id)

    if req.return_pdf_direct:
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    return ReportMetadataResponse(
        property_id=prop.id,
        property_title=prop.title,
        city=prop.city,
        locality=prop.locality,
        page_count=10,
        file_size_bytes=len(pdf_bytes),
        file_name=filename,
        download_url=f"/api/v1/reports/{property_id}/pdf",
        preview_url=f"/api/v1/reports/{property_id}/preview?stream=true",
        generated_at=now_iso,
        ai_included=bool(ai_analysis),
        sections_included=[
            "Cover Page & Tri-Score Summary",
            "Executive Investment Summary",
            "Property Overview & Physical Attributes",
            "Financial Modeling & Return Projections",
            "Financing, Leverage & Loan Amortization",
            "Comprehensive 5-Category Risk Intelligence",
            "Micro-Market Benchmarking & Regional Alignment",
            "Stress Testing & What-If Scenario Matrix",
            "AI Deal Intelligence & Due-Diligence Roadmap",
            "Methodology, Financial Formulas & Legal Disclaimers",
        ],
        disclaimer="Analytical estimate based on deterministic financial algorithms. Not a legal valuation certificate or appraisal.",
    )


@router.get(
    "/{property_id}/preview",
    summary="Preview PDF report or fetch preview metadata",
    responses={
        200: {
            "description": "Streamed PDF or Report metadata",
        },
        404: {"description": "Property not found"},
    },
)
def preview_property_report(
    property_id: int,
    stream: bool = Query(default=True, description="If True, stream PDF for inline preview; if False, return metadata"),
    db: Session = Depends(get_db),
):
    """
    Preview endpoint designed for the Next.js frontend PDF viewer.
    When stream=true, returns the PDF directly with inline Content-Disposition.
    When stream=false, returns JSON summary metadata.
    """
    if stream:
        return get_property_pdf_report(property_id=property_id, db=db)

    prop, benchmark_obj = _resolve_property_and_benchmark(property_id, db)
    ai_cached = ai_analysis_service.get_cached_analysis(property_id)
    filename = _sanitize_filename(prop.title, property_id)
    now_iso = datetime.now(timezone.utc).isoformat()

    return ReportMetadataResponse(
        property_id=prop.id,
        property_title=prop.title,
        city=prop.city,
        locality=prop.locality,
        page_count=10,
        file_size_bytes=173416,
        file_name=filename,
        download_url=f"/api/v1/reports/{property_id}/pdf",
        preview_url=f"/api/v1/reports/{property_id}/preview?stream=true",
        generated_at=now_iso,
        ai_included=bool(ai_cached),
        sections_included=[
            "Cover Page",
            "Executive Summary",
            "Property Overview",
            "Financial Analysis",
            "Loan Analysis",
            "Risk Intelligence",
            "Market Benchmarking",
            "Scenario Analysis",
            "AI Investment Insights",
            "Disclaimer & Methodology",
        ],
        disclaimer="Analytical estimate based on deterministic algorithms. Not an appraisal certificate.",
    )
