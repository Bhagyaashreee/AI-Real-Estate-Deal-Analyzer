from fastapi import APIRouter
from app.api.v1.endpoints import health, properties, analysis, ai, risk, benchmarks, reports

api_router = APIRouter()

# Health & diagnostic routes
api_router.include_router(health.router, tags=["Health"])

# Real estate properties & analytics routes
api_router.include_router(properties.router, prefix="/properties", tags=["Properties"])

# Financial modeling & deal analytics routes
api_router.include_router(analysis.router, prefix="/analysis", tags=["Financial Analysis"])

# Local Ollama AI intelligence routes
api_router.include_router(ai.router, prefix="/ai", tags=["AI Intelligence"])

# Advanced Risk Detection & What-If Simulation routes
api_router.include_router(risk.router, prefix="/risk", tags=["Risk Intelligence"])

# Direct Data Confidence route alias
api_router.add_api_route(
    "/data-confidence/{property_id}",
    risk.get_data_confidence,
    methods=["GET"],
    tags=["Risk Intelligence"],
    response_model=risk.DataConfidenceResponse,
)

# Market Benchmarking routes
api_router.include_router(benchmarks.router, prefix="/benchmarks", tags=["Market Benchmarks"])

# Professional PDF Investment Report routes
api_router.include_router(reports.router, prefix="/reports", tags=["PDF Reports"])

