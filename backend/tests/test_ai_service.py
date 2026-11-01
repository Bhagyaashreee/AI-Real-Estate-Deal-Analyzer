import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.ollama_service import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
)

client = TestClient(app)


# ----------------------------------------------------------------------
# 1. AI Status & Diagnostics Tests
# ----------------------------------------------------------------------

def test_ai_status_endpoint_live():
    """Verify the AI status endpoint returns real status or structured offline info."""
    res = client.get("/api/v1/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "model_name" in data
    assert data["model_name"] == "llama3.2:3b"
    assert "inference_ready" in data


def test_ai_status_offline_handling():
    """Verify offline handling when Ollama daemon is unreachable."""
    with patch(
        "app.services.ollama_service.ollama_service.check_health",
        new_callable=AsyncMock,
    ) as mock_health:
        mock_health.return_value = {
            "status": "offline",
            "base_url": "http://127.0.0.1:11434",
            "target_model": "llama3.2:3b",
            "model_ready": False,
            "installed_models": [],
            "error": "Connection refused",
            "guidance": "Start Ollama locally",
        }
        res = client.get("/api/v1/ai/status")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "offline"
        assert data["model_available"] is False
        assert data["inference_ready"] is False
        assert "Connection refused" in data["error_message"]


# ----------------------------------------------------------------------
# 2. AI Structured Property Analysis Tests
# ----------------------------------------------------------------------

MOCK_AI_STRUCTURED_RESPONSE = {
    "verdict": "Strong Potential",
    "verdict_rationale": "High gross yield of 4.98% combined with positive cash flow makes this deal attractive.",
    "executive_summary": "The property in Hinjewadi, Pune is an attractive high-yield investment. It exhibits stable operational yields and covers its EMI obligations.",
    "investment_strengths": [
        "Gross rental yield of 4.98% exceeds Indian residential average",
        "Positive monthly cash flow cushion of ₹11,500/mo",
    ],
    "investment_weaknesses": [
        "Tenure commitment of 20 years on debt service",
    ],
    "risks": {
        "calculated_risks": ["Debt coverage ratio sensitive to rate increases"],
        "information_gap_risks": ["Property age not explicitly confirmed in listing"],
        "external_verification_required": [
            "Encumbrance Certificate verification",
            "Society maintenance escalation policy review",
        ],
    },
    "rental_income_analysis": "Rental income yields 4.98% gross, placing it in the top tier of Pune tech hub assets.",
    "loan_burden_analysis": "Monthly EMI of ₹48,000 is comfortably serviced by the expected rent of ₹55,000.",
    "cash_flow_interpretation": "Healthy positive net cash flow ensures immediate operating solvency.",
    "scenario_analysis_summary": "Under a 10% rent reduction stress test, cash flow remains positive.",
    "recommendations": [
        "Conduct physical inspection of society amenities.",
        "Obtain copy of occupancy certificate (OC).",
    ],
    "missing_information": [
        "Detailed municipal property tax receipts",
    ],
    "disclaimers": [
        "Educational AI analysis; independent physical inspection required.",
    ],
}


def test_ai_analyze_property_success():
    """Verify structured AI analysis endpoint with mocked Ollama JSON generation."""
    # Fetch a valid property ID
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    with patch(
        "app.services.ollama_service.ollama_service.generate_json",
        new_callable=AsyncMock,
    ) as mock_gen_json, patch(
        "app.services.ollama_service.ollama_service.verify_model_available",
        new_callable=AsyncMock,
    ):
        mock_gen_json.return_value = {
            "data": MOCK_AI_STRUCTURED_RESPONSE,
            "total_duration_ms": 1250.0,
            "model": "llama3.2:3b",
        }

        res = client.post(f"/api/v1/ai/analyze/{prop_id}")
        assert res.status_code == 200
        data = res.json()

        # Validate schema fields
        assert data["property_id"] == prop_id
        assert data["verdict"] in [
            "Strong Potential",
            "Potential with Caution",
            "Weak Investment",
            "High Risk",
            "Insufficient Information",
        ]
        assert "verdict_rationale" in data
        assert "executive_summary" in data
        assert len(data["investment_strengths"]) >= 1
        assert "risks" in data
        assert "calculated_risks" in data["risks"]
        assert "information_gap_risks" in data["risks"]
        assert "external_verification_required" in data["risks"]
        assert "recommendations" in data
        assert "disclaimers" in data
        assert data["model_used"] == "llama3.2:3b"


def test_ai_analyze_nonexistent_property():
    """Nonexistent property should return HTTP 404."""
    res = client.post("/api/v1/ai/analyze/999999")
    assert res.status_code == 404


def test_ai_analyze_ollama_offline_error():
    """When Ollama is unreachable, return HTTP 503."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    with patch(
        "app.services.ollama_service.ollama_service.generate_json",
        new_callable=AsyncMock,
        side_effect=OllamaConnectionError("Connection refused at 11434"),
    ):
        res = client.post(f"/api/v1/ai/analyze/{prop_id}")
        assert res.status_code == 503
        assert "offline" in res.json()["detail"].lower()


def test_ai_analyze_model_missing_error():
    """When target model is not pulled, return HTTP 503."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    with patch(
        "app.services.ollama_service.ollama_service.generate_json",
        new_callable=AsyncMock,
        side_effect=OllamaModelNotFoundError("Model llama3.2:3b not found"),
    ):
        res = client.post(f"/api/v1/ai/analyze/{prop_id}")
        assert res.status_code == 503
        assert "unavailable" in res.json()["detail"].lower()


def test_ai_analyze_timeout_error():
    """When inference times out, return HTTP 504."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    with patch(
        "app.services.ollama_service.ollama_service.generate_json",
        new_callable=AsyncMock,
        side_effect=OllamaTimeoutError("Timed out after 90s"),
    ):
        res = client.post(f"/api/v1/ai/analyze/{prop_id}")
        assert res.status_code == 504
        assert "timed out" in res.json()["detail"].lower()


# ----------------------------------------------------------------------
# 3. Property AI Chat Tests
# ----------------------------------------------------------------------

def test_ai_chat_success_and_context():
    """Verify property AI chat assistant grounded in financial metrics."""
    list_res = client.get("/api/v1/properties?page=1&page_size=1")
    prop_id = list_res.json()["items"][0]["id"]

    with patch(
        "app.services.ollama_service.ollama_service.generate_chat",
        new_callable=AsyncMock,
    ) as mock_gen_chat, patch(
        "app.services.ollama_service.ollama_service.verify_model_available",
        new_callable=AsyncMock,
    ):
        mock_gen_chat.return_value = {
            "response": "The monthly cash flow is positive at ₹14,500/mo because the expected rent of ₹52,000 exceeds the monthly EMI of ₹34,500 plus maintenance.",
            "role": "assistant",
            "total_duration_ms": 680.0,
            "model": "llama3.2:3b",
        }

        chat_payload = {
            "message": "Why is the cash flow positive on this property?",
            "history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hello! I am ready to analyze this property."},
            ],
        }

        res = client.post(f"/api/v1/ai/chat/{prop_id}", json=chat_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["property_id"] == prop_id
        assert "cash flow" in data["response"].lower()
        assert len(data["follow_up_suggestions"]) > 0
        assert data["model_used"] == "llama3.2:3b"


def test_ai_chat_nonexistent_property():
    res = client.post(
        "/api/v1/ai/chat/999999",
        json={"message": "Is this a good deal?"},
    )
    assert res.status_code == 404


# ----------------------------------------------------------------------
# 4. AI Multi-Property Comparison Tests
# ----------------------------------------------------------------------

def test_ai_compare_analysis_success():
    """Verify AI comparison of up to 4 properties with trade-offs."""
    list_res = client.get("/api/v1/properties?page=1&page_size=3")
    items = list_res.json()["items"]
    ids = [p["id"] for p in items[:2]]

    mock_comp_json = {
        "top_pick_property_id": ids[0],
        "top_pick_title": items[0]["title"],
        "executive_comparison": "Property 1 demonstrates superior rental yield efficiency (4.80%) compared to Property 2 (2.78%), while Property 2 represents prime capital value in Mumbai.",
        "comparative_insights": [
            {
                "property_id": ids[0],
                "title": items[0]["title"],
                "city": items[0]["city"],
                "primary_strength": "High rental yield and positive cash flow.",
                "primary_risk": "Moderate capital barrier.",
                "investor_suitability": "Income-focused investor",
            },
            {
                "property_id": ids[1],
                "title": items[1]["title"],
                "city": items[1]["city"],
                "primary_strength": "Premium high-demand locality.",
                "primary_risk": "Sub-3% rental yield and negative cash flow under leverage.",
                "investor_suitability": "Long-term appreciation investor",
            },
        ],
        "key_tradeoffs": [
            "Yield efficiency vs Locality prestige",
            "Immediate cash flow vs Long-term capital growth",
        ],
        "verdict_summary": f"Property #{ids[0]} is the better pick for cash-flowing rental portfolios.",
    }

    with patch(
        "app.services.ollama_service.ollama_service.generate_json",
        new_callable=AsyncMock,
    ) as mock_gen_json, patch(
        "app.services.ollama_service.ollama_service.verify_model_available",
        new_callable=AsyncMock,
    ):
        mock_gen_json.return_value = {
            "data": mock_comp_json,
            "total_duration_ms": 1100.0,
            "model": "llama3.2:3b",
        }

        res = client.post(
            "/api/v1/ai/compare-analysis",
            json={
                "property_ids": ids,
                "user_notes": "Prioritize higher monthly rental yield.",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["properties_compared"]) == 2
        assert data["top_pick_property_id"] == ids[0]
        assert len(data["comparative_insights"]) == 2
        assert len(data["key_tradeoffs"]) >= 2
        assert "disclaimer" in data

