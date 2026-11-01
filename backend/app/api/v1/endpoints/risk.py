from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.property import Property
from app.models.benchmark import MarketBenchmark
from app.schemas.analysis import AnalysisCalculateRequest
from app.schemas.risk import (
    RiskScoreBreakdown,
    WhatIfSimulationInputs,
    WhatIfSimulationResponse,
    DataConfidenceResponse,
    CompareScenariosRequest,
)
from app.api.v1.endpoints.analysis import perform_full_analysis
from app.services.risk_engine import risk_engine
from app.services.benchmark_service import benchmark_service
from app.services.ai_analysis_service import ai_analysis_service
from app.services.ollama_service import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
)

router = APIRouter()


@router.post("/{property_id}/analyze", response_model=RiskScoreBreakdown)
def analyze_property_risk(
    property_id: int,
    db: Session = Depends(get_db),
):
    """
    Perform a complete multi-dimensional risk assessment on an Indian real estate listing.
    Calculates Financial, Loan, Rental, Data Reliability, and External Due-Diligence risks.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found.",
        )

    # 1. Deterministic Financial Foundation
    fin_analysis = perform_full_analysis(prop, AnalysisCalculateRequest())

    # 2. Corroborating Benchmark (if present in locality)
    benchmark = benchmark_service.get_matching_benchmark(
        db, prop.city, prop.locality, prop.property_type
    )

    # 3. Risk Evaluation
    breakdown = risk_engine.evaluate_risk(prop, fin_analysis, benchmark)
    return breakdown


@router.post("/{property_id}/simulate", response_model=WhatIfSimulationResponse)
def simulate_property_what_if(
    property_id: int,
    inputs: Optional[WhatIfSimulationInputs] = None,
    db: Session = Depends(get_db),
):
    """
    Run 6 preconfigured stress-test simulations (Conservative, Base, Optimistic,
    Rental Decline, Interest Rate Shock, Extended Vacancy) plus custom inputs.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found.",
        )

    sim_res = risk_engine.run_what_if_simulation(prop, inputs)
    return sim_res


@router.post("/compare-scenarios")
def compare_scenarios_across_properties(
    request: CompareScenariosRequest,
    db: Session = Depends(get_db),
):
    """
    Compare stress-test scenario outcomes across 1 to 4 properties under uniform shocks.
    """
    property_ids = request.property_ids
    if len(property_ids) < 1 or len(property_ids) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide between 1 and 4 property IDs to compare.",
        )

    props = db.query(Property).filter(Property.id.in_(property_ids)).all()
    if not props:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching properties found.",
        )

    results = []
    for prop in props:
        sim = risk_engine.run_what_if_simulation(prop, request.inputs)
        results.append(sim)

    return {
        "count": len(results),
        "properties": results,
    }


@router.post("/{property_id}/ai-explain")
async def explain_risk_with_ai(
    property_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate local AI risk commentary explaining key financial sensitivities,
    downside stress scenarios, and legal verification steps using llama3.2:3b.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found.",
        )

    fin_analysis = perform_full_analysis(prop, AnalysisCalculateRequest())
    benchmark = benchmark_service.get_matching_benchmark(
        db, prop.city, prop.locality, prop.property_type
    )
    risk_breakdown = risk_engine.evaluate_risk(prop, fin_analysis, benchmark)
    simulation = risk_engine.run_what_if_simulation(prop)

    try:
        explanation = await ai_analysis_service.explain_risk_intelligence(
            prop, risk_breakdown, simulation, benchmark
        )
        return explanation
    except OllamaConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Local Ollama is offline: {str(e)}.",
        )
    except OllamaModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model unavailable: {str(e)}.",
        )
    except OllamaTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"AI risk explanation timed out: {str(e)}.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error in AI risk explanation: {str(e)}.",
        )


@router.get("/data-confidence/{property_id}", response_model=DataConfidenceResponse)
def get_data_confidence(
    property_id: int,
    db: Session = Depends(get_db),
):
    """
    Inspect the independent data confidence rating for a property.
    Shows positive verification signals vs missing provenance elements.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found.",
        )

    benchmark = benchmark_service.get_matching_benchmark(
        db, prop.city, prop.locality, prop.property_type
    )
    score, level, reasons = risk_engine.calculate_data_confidence(prop, benchmark)

    positive_signals = [r for r in reasons if "identified" in r or "provided" in r or "specified" in r or "Complete" in r or "Corroborated" in r]
    missing_elements = [r for r in reasons if "missing" in r or "No verifiable" in r or "Unidentified" in r or "No micro-market" in r or "DEMO" in r]

    bench_status = (
        f"Corroborated with {benchmark.city} ({benchmark.locality}) data"
        if benchmark
        else "No locality benchmark available"
    )

    return DataConfidenceResponse(
        property_id=prop.id,
        property_title=prop.title,
        confidence_score=score,
        confidence_level=level,
        positive_signals=positive_signals,
        missing_elements=missing_elements,
        benchmark_status=bench_status,
        is_demo=prop.is_demo,
        explanation=f"Data confidence is {level} ({score}/100) based on listing provenance and benchmark corroboration.",
    )
