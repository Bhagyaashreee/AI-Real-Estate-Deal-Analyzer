from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.property import Property
from app.schemas.analysis import AnalysisCalculateRequest, ComparisonItem
from app.schemas.ai import (
    AIStatusResponse,
    AIStructuredAnalysis,
    AIChatRequest,
    AIChatResponse,
    AIComparisonRequest,
    AIComparisonResponse,
)
from app.services.ollama_service import (
    ollama_service,
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    OllamaResponseError,
)
from app.services.ai_analysis_service import ai_analysis_service
from app.api.v1.endpoints.analysis import perform_full_analysis
from app.utils.financial import format_inr

router = APIRouter()


@router.get("/status", response_model=AIStatusResponse)
async def get_ai_status():
    """
    Check status of the local Ollama daemon and verify llama3.2:3b readiness.
    """
    health = await ollama_service.check_health()
    is_ready = health.get("status") == "online" and health.get("model_ready", False)

    return AIStatusResponse(
        status=health.get("status", "offline"),
        model_name=ollama_service.model,
        model_available=health.get("model_ready", False),
        inference_ready=is_ready,
        base_url=ollama_service.base_url,
        installed_models=health.get("installed_models", []),
        error_message=health.get("error"),
        guidance=health.get("guidance"),
    )


@router.post("/analyze/{property_id}", response_model=AIStructuredAnalysis)
async def analyze_property_with_ai(
    property_id: int,
    db: Session = Depends(get_db),
):
    """
    Run an end-to-end grounded AI investment analysis on an Indian property listing.
    Combines deterministic calculations with llama3.2:3b interpretation.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found in database.",
        )

    # 1. Deterministic Financial Foundation
    fin_analysis = perform_full_analysis(prop, AnalysisCalculateRequest())

    # 2. Local AI Interpretation
    try:
        analysis = await ai_analysis_service.analyze_property(prop, fin_analysis)
        return analysis
    except OllamaConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Local Ollama service offline: {str(e)}. Please start Ollama via 'ollama serve'.",
        )
    except OllamaModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Local model unavailable: {str(e)}. Run 'ollama pull {ollama_service.model}'.",
        )
    except OllamaTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"AI inference timed out: {str(e)}. System may be under heavy CPU load.",
        )
    except OllamaResponseError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI generation parsing error: {str(e)}.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during AI analysis: {str(e)}.",
        )


@router.post("/chat/{property_id}", response_model=AIChatResponse)
async def chat_with_property_ai(
    property_id: int,
    request: AIChatRequest,
    db: Session = Depends(get_db),
):
    """
    Property-specific conversational AI assistant for deal queries.
    Grounds answers in deterministic financial metrics and preserves conversation context.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found.",
        )

    fin_analysis = perform_full_analysis(prop, AnalysisCalculateRequest())

    try:
        chat_resp = await ai_analysis_service.chat_with_property_advisor(
            prop, fin_analysis, request
        )
        return chat_resp
    except OllamaConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama offline: {str(e)}. Ensure 'ollama serve' is running.",
        )
    except OllamaModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model '{ollama_service.model}' not found in local Ollama.",
        )
    except OllamaTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Chat inference timed out: {str(e)}.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}.",
        )


@router.post("/compare-analysis", response_model=AIComparisonResponse)
async def compare_properties_with_ai(
    request: AIComparisonRequest,
    db: Session = Depends(get_db),
):
    """
    Compare 2 to 4 properties using local AI to explain trade-offs and score divergence.
    """
    props = db.query(Property).filter(Property.id.in_(request.property_ids)).all()
    if len(props) != len(request.property_ids):
        found_ids = {p.id for p in props}
        missing_ids = set(request.property_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Properties with IDs {list(missing_ids)} not found.",
        )

    # Perform deterministic calculations for all properties
    comparison_items: List[ComparisonItem] = []
    for prop in props:
        fin = perform_full_analysis(prop, AnalysisCalculateRequest())
        comparison_items.append(
            ComparisonItem(
                property_id=prop.id,
                title=prop.title,
                city=prop.city,
                locality=prop.locality,
                property_type=prop.property_type,
                bedrooms=prop.bedrooms,
                built_up_area_sqft=prop.built_up_area_sqft,
                price_per_sqft=fin.price_per_sqft,
                purchase_price_inr=prop.purchase_price_inr,
                total_acquisition_cost_inr=fin.acquisition_costs["total_acquisition_cost_inr"],
                gross_monthly_rent_inr=prop.expected_monthly_rent_inr,
                monthly_emi_inr=fin.loan_metrics["monthly_emi_inr"],
                monthly_net_cash_flow_inr=fin.returns["monthly_net_cash_flow_inr"],
                gross_rental_yield_pct=fin.returns["gross_rental_yield_pct"],
                net_rental_yield_pct=fin.returns["net_rental_yield_pct"],
                cash_on_cash_roi_pct=fin.returns["cash_on_cash_roi_pct"],
                investment_score=fin.deal_score["overall_score"],
                classification=fin.deal_score["classification"],
                price_formatted=format_inr(prop.purchase_price_inr),
                rent_formatted=f"{format_inr(prop.expected_monthly_rent_inr)}/mo",
                is_demo=prop.is_demo,
            )
        )

    try:
        comp_response = await ai_analysis_service.compare_properties_ai(
            props, comparison_items, request.user_notes
        )
        return comp_response
    except OllamaConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama offline: {str(e)}.",
        )
    except OllamaModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model unavailable: {str(e)}.",
        )
    except OllamaTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Comparison inference timed out: {str(e)}.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing AI comparison: {str(e)}.",
        )
