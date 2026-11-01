import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.models.property import Property
from app.models.benchmark import MarketBenchmark
from app.schemas.analysis import FinancialAnalysisResponse, ComparisonItem
from app.schemas.risk import RiskScoreBreakdown, WhatIfSimulationResponse
from app.schemas.ai import (
    AIStructuredAnalysis,
    AIAnalysisVerdict,
    AIRiskBreakdown,
    AIChatRequest,
    AIChatResponse,
    AIComparisonResponse,
    AIComparisonItemInsight,
)
from app.services.ollama_service import ollama_service
from app.utils.financial import format_inr


class AIAnalysisService:
    def __init__(self):
        self.ollama = ollama_service
        self._analysis_cache: Dict[int, AIStructuredAnalysis] = {}

    def get_cached_analysis(self, property_id: int) -> Optional[AIStructuredAnalysis]:
        """Retrieve pre-computed in-memory structured AI analysis without re-running Ollama."""
        return self._analysis_cache.get(property_id)

    def set_cached_analysis(self, property_id: int, analysis: AIStructuredAnalysis):
        """Cache structured AI analysis for immediate reuse in PDF generation."""
        self._analysis_cache[property_id] = analysis

    async def analyze_property(
        self,
        prop: Property,
        fin: FinancialAnalysisResponse,
    ) -> AIStructuredAnalysis:
        """
        Produce a grounded, structured investment report explaining the deterministic
        financial metrics and evaluating investment risk without inventing data.
        """
        # 1. Prepare grounded data payload for the prompt
        system_prompt = (
            "You are an expert Indian Real Estate Investment Analyst operating inside a local analysis engine. "
            "You evaluate investment deals strictly based on the supplied deterministic financial calculations.\n\n"
            "CRITICAL RULES:\n"
            "1. ONLY interpret and explain the supplied financial metrics. Never fabricate prices, yields, rent, appreciation, or ownership details.\n"
            "2. If information is missing or not provided, explicitly state it is unavailable.\n"
            "3. Do not make guaranteed return claims. All assessments must be objective and highlight risk factors.\n"
            "4. Your verdict MUST be exactly one of: 'Strong Potential', 'Potential with Caution', 'Weak Investment', 'High Risk', or 'Insufficient Information'.\n"
            "5. You must return ONLY a valid JSON object matching the requested schema without any markdown formatting or preamble."
        )

        # Context summary in INR
        ret = fin.returns
        deal_score = fin.deal_score
        loan = fin.loan_metrics
        op = fin.operating_finances
        acq = fin.acquisition_costs
        sens = ret.get("sensitivity_scenarios", {})

        prompt_data = {
            "property": {
                "id": prop.id,
                "title": prop.title,
                "city": prop.city,
                "locality": prop.locality,
                "state": prop.state,
                "property_type": prop.property_type,
                "bedrooms": prop.bedrooms,
                "bathrooms": prop.bathrooms,
                "built_up_area_sqft": prop.built_up_area_sqft,
                "purchase_price_inr": prop.purchase_price_inr,
                "purchase_price_formatted": format_inr(prop.purchase_price_inr),
                "price_per_sqft": fin.price_per_sqft,
                "property_age": prop.property_age or "Not Provided",
                "source_url": prop.source_url or "Not Provided",
                "is_demo_data": prop.is_demo,
            },
            "acquisition_costs": {
                "total_acquisition_cost_inr": acq.get("total_acquisition_cost_inr"),
                "total_acquisition_cost_formatted": format_inr(acq.get("total_acquisition_cost_inr", 0)),
                "stamp_duty_inr": acq.get("stamp_duty_inr"),
                "registration_charges_inr": acq.get("registration_charges_inr"),
                "brokerage_inr": acq.get("brokerage_inr"),
                "renovation_expenses_inr": acq.get("renovation_expenses_inr"),
            },
            "financial_metrics": {
                "expected_monthly_rent_inr": prop.expected_monthly_rent_inr,
                "expected_monthly_rent_formatted": format_inr(prop.expected_monthly_rent_inr),
                "gross_rental_yield_pct": ret.get("gross_rental_yield_pct"),
                "net_rental_yield_pct": ret.get("net_rental_yield_pct"),
                "monthly_net_cash_flow_inr": ret.get("monthly_net_cash_flow_inr"),
                "annual_net_cash_flow_inr": ret.get("annual_net_cash_flow_inr"),
                "monthly_emi_inr": loan.get("monthly_emi_inr"),
                "loan_principal_inr": loan.get("loan_principal_inr"),
                "down_payment_inr": loan.get("down_payment_inr"),
                "cash_on_cash_roi_pct": ret.get("cash_on_cash_roi_pct"),
                "break_even_summary": ret.get("break_even", {}).get("summary"),
            },
            "deterministic_scoring": {
                "overall_score": deal_score.get("overall_score"),
                "classification": deal_score.get("classification"),
                "positive_factors": deal_score.get("positive_factors", []),
                "risk_flags": deal_score.get("risk_flags", []),
            },
            "stress_test_scenarios": {
                "conservative_cash_flow": sens.get("conservative", {}).get("monthly_net_cash_flow_inr"),
                "base_cash_flow": sens.get("base", {}).get("monthly_net_cash_flow_inr"),
                "optimistic_cash_flow": sens.get("optimistic", {}).get("monthly_net_cash_flow_inr"),
            },
        }

        user_prompt = f"""Evaluate this Indian real estate property using the supplied verified numbers:

DATA:
{json.dumps(prompt_data, indent=2)}

Respond with a JSON object with EXACTLY this structure (keep each string concise and under 2 sentences):
{{
  "verdict": "Strong Potential | Potential with Caution | Weak Investment | High Risk | Insufficient Information",
  "verdict_rationale": "1 sentence on why this verdict fits the numbers.",
  "executive_summary": "2 sentences summarizing yield, cash flow, and debt burden.",
  "investment_strengths": ["Strength 1 from data", "Strength 2 from data"],
  "investment_weaknesses": ["Weakness 1 from data", "Weakness 2 from data"],
  "risks": {{
    "calculated_risks": ["1-2 numerical risks like negative cash flow or high EMI"],
    "information_gap_risks": ["1-2 risks from missing listing details"],
    "external_verification_required": ["1-2 physical/legal verification checks required"]
  }},
  "rental_income_analysis": "1-2 sentences evaluating gross and net yield.",
  "loan_burden_analysis": "1-2 sentences on debt service and EMI coverage.",
  "cash_flow_interpretation": "1-2 sentences on monthly net cash flow.",
  "scenario_analysis_summary": "1-2 sentences interpreting downturn vs base case.",
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "missing_information": ["Missing property age or legal approvals"],
  "disclaimers": ["Educational analysis; physical inspection and title check mandatory."]
}}"""

        res = await self.ollama.generate_json(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.2,
            num_predict=420,
            timeout=120.0,
        )

        data = res.get("data", {})
        duration_ms = res.get("total_duration_ms")

        # Sanitize verdict to ensure valid enum
        raw_verdict = data.get("verdict", "")
        valid_verdicts = {v.value for v in AIAnalysisVerdict}
        if raw_verdict not in valid_verdicts:
            score = deal_score.get("overall_score", 50)
            if score >= 85:
                raw_verdict = AIAnalysisVerdict.STRONG_POTENTIAL.value
            elif score >= 65:
                raw_verdict = AIAnalysisVerdict.POTENTIAL_WITH_CAUTION.value
            elif score >= 45:
                raw_verdict = AIAnalysisVerdict.WEAK_INVESTMENT.value
            else:
                raw_verdict = AIAnalysisVerdict.HIGH_RISK.value

        # Build verified risks
        raw_risks = data.get("risks", {})
        calc_risks = raw_risks.get("calculated_risks") or deal_score.get("risk_flags", [])
        gap_risks = raw_risks.get("information_gap_risks") or [
            "Listing source requires independent verification.",
            "Property age and actual maintenance records require physical ledger review.",
        ]
        ext_risks = raw_risks.get("external_verification_required") or [
            "Encumbrance Certificate (EC) and 30-year title deed verification.",
            "Municipal/RERA approval and occupancy certificate (OC) verification.",
            "Independent structural safety audit for older properties.",
        ]

        now_str = datetime.now(timezone.utc).isoformat()

        return AIStructuredAnalysis(
            property_id=prop.id,
            property_title=prop.title,
            city=prop.city,
            locality=prop.locality,
            verdict=AIAnalysisVerdict(raw_verdict),
            verdict_rationale=data.get(
                "verdict_rationale",
                f"Assigned based on deterministic investment score of {deal_score.get('overall_score')}/100 and net rental yield of {ret.get('net_rental_yield_pct')}%.",
            ),
            executive_summary=data.get(
                "executive_summary",
                f"The property in {prop.locality}, {prop.city} listed at {format_inr(prop.purchase_price_inr)} yields a gross rental return of {ret.get('gross_rental_yield_pct')}% with a monthly net cash flow of {format_inr(ret.get('monthly_net_cash_flow_inr', 0))}.",
            ),
            investment_strengths=data.get("investment_strengths") or deal_score.get("positive_factors", []),
            investment_weaknesses=data.get("investment_weaknesses") or [
                f"Net yield of {ret.get('net_rental_yield_pct')}% after operating costs and vacancy.",
                f"Monthly debt service obligation of {format_inr(loan.get('monthly_emi_inr', 0))}.",
            ],
            risks=AIRiskBreakdown(
                calculated_risks=calc_risks,
                information_gap_risks=gap_risks,
                external_verification_required=ext_risks,
            ),
            rental_income_analysis=data.get(
                "rental_income_analysis",
                f"Expected rent of {format_inr(prop.expected_monthly_rent_inr)} generates an annual gross yield of {ret.get('gross_rental_yield_pct')}%.",
            ),
            loan_burden_analysis=data.get(
                "loan_burden_analysis",
                f"Monthly EMI stands at {format_inr(loan.get('monthly_emi_inr', 0))} against an effective rent of {format_inr(op.get('effective_gross_monthly_rent_inr', 0))}.",
            ),
            cash_flow_interpretation=data.get(
                "cash_flow_interpretation",
                f"Estimated monthly net cash flow is {format_inr(ret.get('monthly_net_cash_flow_inr', 0))} with a break-even projection of {ret.get('break_even', {}).get('summary')}.",
            ),
            scenario_analysis_summary=data.get(
                "scenario_analysis_summary",
                f"Under stress-testing, monthly cash flow shifts between {format_inr(sens.get('conservative', {}).get('monthly_net_cash_flow_inr', 0))} (downturn) and {format_inr(sens.get('optimistic', {}).get('monthly_net_cash_flow_inr', 0))} (high demand).",
            ),
            recommendations=data.get("recommendations") or [
                "Negotiate purchase price to enhance gross yield above 4.5%.",
                "Verify actual utility and society maintenance charges with local resident welfare association.",
                "Conduct legal due diligence on title and encumbrance.",
            ],
            missing_information=data.get("missing_information") or [
                "Physical property age certificate.",
                "RERA approval registration number.",
                "Historical tenant turnover rate in this micro-market.",
            ],
            disclaimers=data.get("disclaimers") or [
                "This AI report is generated locally using llama3.2:3b for analysis purposes only.",
                "Not financial, legal, or investment advice. Investors must conduct independent due diligence.",
            ],
            generated_at=now_str,
            model_used=self.ollama.model,
            inference_time_ms=duration_ms,
        )
        self._analysis_cache[prop.id] = result
        return result

    async def chat_with_property_advisor(
        self,
        prop: Property,
        fin: FinancialAnalysisResponse,
        request: AIChatRequest,
    ) -> AIChatResponse:
        """
        Engage in an interactive property-specific Q&A grounded in deterministic calculations.
        Maintains conversational context for follow-up inquiries.
        """
        ret = fin.returns
        loan = fin.loan_metrics
        op = fin.operating_finances
        acq = fin.acquisition_costs
        score = fin.deal_score
        sens = ret.get("sensitivity_scenarios", {})

        system_prompt = (
            f"You are a specialized Indian Real Estate Investment Advisor assisting a property investor.\n"
            f"You are currently analyzing ONLY this specific property:\n"
            f"- Title: {prop.title}\n"
            f"- Location: {prop.locality}, {prop.city}, {prop.state}\n"
            f"- Type: {prop.property_type} ({prop.bedrooms} BHK, {prop.built_up_area_sqft} sq.ft)\n"
            f"- Purchase Price: {format_inr(prop.purchase_price_inr)} (₹{fin.price_per_sqft}/sq.ft)\n"
            f"- Total Acquisition Cost: {format_inr(acq.get('total_acquisition_cost_inr', 0))}\n"
            f"- Expected Monthly Rent: {format_inr(prop.expected_monthly_rent_inr)}/mo\n"
            f"- Monthly Maintenance: {format_inr(prop.monthly_maintenance_inr)}/mo\n"
            f"- Gross Rental Yield: {ret.get('gross_rental_yield_pct')}%\n"
            f"- Net Rental Yield: {ret.get('net_rental_yield_pct')}%\n"
            f"- Monthly EMI: {format_inr(loan.get('monthly_emi_inr', 0))} (at {loan.get('annual_interest_rate_pct')}% interest)\n"
            f"- Monthly Net Cash Flow: {format_inr(ret.get('monthly_net_cash_flow_inr', 0))}/mo\n"
            f"- Cash-on-Cash ROI: {ret.get('cash_on_cash_roi_pct')}%\n"
            f"- Break-Even Timeline: {ret.get('break_even', {}).get('summary')}\n"
            f"- Deal Score: {score.get('overall_score')}/100 ({score.get('classification')})\n"
            f"- Stress Tests: Conservative cash flow: {format_inr(sens.get('conservative', {}).get('monthly_net_cash_flow_inr', 0))}, Optimistic: {format_inr(sens.get('optimistic', {}).get('monthly_net_cash_flow_inr', 0))}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Answer user questions concisely, professionally, and factually using ONLY these verified figures.\n"
            f"2. Always format currency in Indian Rupees (₹, Lakhs, Crores).\n"
            f"3. Do not invent missing data. If the user asks about an unknown detail, clearly state that it is not provided.\n"
            f"4. Keep answers under 3-4 paragraphs so they are easy to read in the chat UI."
        )

        # Assemble messages list
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # Include prior conversation history (up to last 6 messages to keep context concise)
        if request.history:
            for h in request.history[-6:]:
                messages.append({"role": h.role, "content": h.content})

        messages.append({"role": "user", "content": request.message})

        res = await self.ollama.generate_chat(
            messages=messages,
            temperature=0.4,
            num_predict=500,
        )

        response_text = res.get("response", "")
        duration_ms = res.get("total_duration_ms")

        # Dynamic follow-up suggestions
        suggestions = [
            "Why is the cash flow at this level?",
            "What if loan interest rates rise by 1%?",
            "How does the price per sq ft compare to the city average?",
            "What physical checks should I do before buying?",
        ]

        return AIChatResponse(
            response=response_text,
            property_id=prop.id,
            property_title=prop.title,
            model_used=self.ollama.model,
            follow_up_suggestions=suggestions[:3],
            inference_time_ms=duration_ms,
        )

    async def compare_properties_ai(
        self,
        properties: List[Property],
        comparison_items: List[ComparisonItem],
        user_notes: Optional[str] = None,
    ) -> AIComparisonResponse:
        """
        Evaluate and compare 2 to 4 properties side-by-side using local AI.
        Explains score differentials, trade-offs, and investor suitability.
        """
        system_prompt = (
            "You are a Senior Real Estate Investment Analyst in India. "
            "Compare the supplied properties using only their verified financial metrics. "
            "Output your analysis strictly in JSON format without markdown code blocks."
        )

        comparison_payload = []
        for item in comparison_items:
            comparison_payload.append({
                "property_id": item.property_id,
                "title": item.title,
                "city": item.city,
                "locality": item.locality,
                "property_type": item.property_type,
                "purchase_price_inr": item.purchase_price_inr,
                "price_formatted": format_inr(item.purchase_price_inr),
                "price_per_sqft": item.price_per_sqft,
                "gross_monthly_rent_inr": item.gross_monthly_rent_inr,
                "gross_rental_yield_pct": item.gross_rental_yield_pct,
                "net_rental_yield_pct": item.net_rental_yield_pct,
                "monthly_net_cash_flow_inr": item.monthly_net_cash_flow_inr,
                "cash_on_cash_roi_pct": item.cash_on_cash_roi_pct,
                "overall_score": item.investment_score,
                "classification": item.classification,
            })

        user_prompt = f"""Compare these {len(comparison_payload)} Indian real estate investment properties:

PROPERTIES DATA:
{json.dumps(comparison_payload, indent=2)}

USER PREFERENCES / NOTES:
{user_notes or 'Standard balanced investment seeking good rental yield and sustainable cash flow.'}

Respond with a JSON object conforming EXACTLY to:
{{
  "top_pick_property_id": {comparison_payload[0]["property_id"]},
  "top_pick_title": "{comparison_payload[0]["title"]}",
  "executive_comparison": "3-4 sentences comparing the properties across ticket size, yields, and cash flow stability.",
  "comparative_insights": [
    {{
      "property_id": <id>,
      "title": "<title>",
      "city": "<city>",
      "primary_strength": "1 sentence on top financial strength",
      "primary_risk": "1 sentence on primary risk or drag",
      "investor_suitability": "Type of investor best suited (e.g. Yield seeker, Capital appreciation, Conservative)"
    }}
  ],
  "key_tradeoffs": [
    "Tradeoff 1: High yield vs capital appreciation potential",
    "Tradeoff 2: Monthly cash flow vs acquisition price"
  ],
  "verdict_summary": "Final concluding recommendation grounded in the numbers."
}}"""

        res = await self.ollama.generate_json(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.2,
            num_predict=750,
        )

        data = res.get("data", {})
        duration_ms = res.get("total_duration_ms")

        top_id = data.get("top_pick_property_id") or comparison_payload[0]["property_id"]
        top_title = data.get("top_pick_title") or comparison_payload[0]["title"]

        insights = []
        raw_insights = data.get("comparative_insights", [])
        if isinstance(raw_insights, list) and len(raw_insights) > 0:
            for r in raw_insights:
                insights.append(
                    AIComparisonItemInsight(
                        property_id=r.get("property_id", 0),
                        title=r.get("title", ""),
                        city=r.get("city", ""),
                        primary_strength=r.get("primary_strength", "Competitive entry price."),
                        primary_risk=r.get("primary_risk", "Moderate rental yield."),
                        investor_suitability=r.get("investor_suitability", "Balanced Investor"),
                    )
                )
        else:
            for item in comparison_payload:
                insights.append(
                    AIComparisonItemInsight(
                        property_id=item["property_id"],
                        title=item["title"],
                        city=item["city"],
                        primary_strength=f"Gross yield of {item['gross_rental_yield_pct']}%.",
                        primary_risk=f"Monthly net cash flow of {format_inr(item['monthly_net_cash_flow_inr'])}.",
                        investor_suitability="Income-focused investor" if item["gross_rental_yield_pct"] >= 4.0 else "Capital growth investor",
                    )
                )

        return AIComparisonResponse(
            properties_compared=comparison_payload,
            top_pick_property_id=top_id,
            top_pick_title=top_title,
            executive_comparison=data.get(
                "executive_comparison",
                f"Comparison of {len(comparison_payload)} properties reveals varying trade-offs between rental yield efficiency and capital requirement.",
            ),
            comparative_insights=insights,
            key_tradeoffs=data.get("key_tradeoffs") or [
                "Yield efficiency vs Absolute Capital Outlay",
                "Monthly Cash Flow Buffer vs Locality Premium",
            ],
            verdict_summary=data.get(
                "verdict_summary",
                f"Property #{top_id} presents the strongest balance of yield and risk adjusted score.",
            ),
            disclaimer="Comparative AI analysis is generated locally using deterministic financial metrics and llama3.2:3b. Not financial advice.",
            model_used=self.ollama.model,
            inference_time_ms=duration_ms,
        )

    async def explain_risk_intelligence(
        self,
        prop: Property,
        risk: RiskScoreBreakdown,
        sim: WhatIfSimulationResponse,
        benchmark: Optional[MarketBenchmark] = None,
    ) -> Dict[str, Any]:
        """
        Produce a focused, grounded risk advisory using local llama3.2:3b.
        Explains risk exposure, downside scenarios, sensitivity to interest rates/rent,
        and provides an objective due-diligence verification roadmap.
        """
        system_prompt = (
            "You are a Senior Risk Officer specialized in Indian real estate investment analysis. "
            "Explain the supplied deterministic risk scores and stress test outputs factually. "
            "Never invent legal approvals or market appreciation. Output strictly in JSON format."
        )

        prompt_payload = {
            "property": {
                "title": prop.title,
                "city": prop.city,
                "locality": prop.locality,
                "purchase_price": format_inr(prop.purchase_price_inr),
                "rent": format_inr(prop.expected_monthly_rent_inr),
            },
            "risk_scores": {
                "risk_exposure_score": risk.risk_exposure_score,
                "overall_risk_level": risk.overall_risk_level,
                "investment_attractiveness_score": risk.investment_attractiveness_score,
                "data_confidence_score": risk.data_confidence_score,
                "data_confidence_level": risk.data_confidence_level,
                "financial_risk_score": risk.categories["financial"].score,
                "loan_risk_score": risk.categories["loan"].score,
                "rental_risk_score": risk.categories["rental"].score,
                "critical_red_flags": risk.critical_red_flags,
            },
            "stress_scenarios": [
                {
                    "scenario": s.scenario_name,
                    "monthly_cash_flow": format_inr(s.monthly_cash_flow_inr),
                    "gross_yield": s.gross_rental_yield_pct,
                    "risk_level": s.risk_level,
                }
                for s in sim.scenarios
            ],
            "market_benchmark": {
                "available": benchmark is not None,
                "locality": benchmark.locality if benchmark else "Unavailable",
                "avg_price_per_sqft": benchmark.avg_price_per_sqft if benchmark else None,
                "avg_rental_yield": benchmark.avg_gross_rental_yield_pct if benchmark else None,
                "provenance": benchmark.data_source if benchmark else "No benchmark record",
            },
        }

        user_prompt = f"""Review the risk breakdown and stress test results for this Indian property:

RISK INTELLIGENCE DATA:
{json.dumps(prompt_payload, indent=2)}

Respond with a JSON object conforming EXACTLY to:
{{
  "executive_risk_summary": "2-3 sentences synthesizing overall risk exposure vs investment attractiveness.",
  "biggest_risks": ["Risk 1 grounded in numbers", "Risk 2 grounded in numbers"],
  "sensitive_assumptions": ["Assumption 1 (e.g. rate hike sensitivity)", "Assumption 2 (e.g. vacancy allowance)"],
  "downside_scenarios_interpretation": "2 sentences interpreting the rental decline and rate hike scenarios.",
  "data_verification_checklist": ["Checklist item 1 for lawyer/buyer", "Checklist item 2 for lawyer/buyer"],
  "benchmark_comparison_analysis": "1-2 sentences comparing property yield to benchmark (or state insufficient benchmark data if unavailable)."
}}"""

        res = await self.ollama.generate_json(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.2,
            num_predict=400,
            timeout=120.0,
        )

        data = res.get("data", {})
        return {
            "property_id": prop.id,
            "property_title": prop.title,
            "executive_risk_summary": data.get(
                "executive_risk_summary",
                f"Overall risk exposure is evaluated at {risk.risk_exposure_score}/100 ({risk.overall_risk_level}) with a data confidence score of {risk.data_confidence_score}/100.",
            ),
            "biggest_risks": data.get("biggest_risks") or risk.critical_red_flags or ["Debt leverage and cash flow sensitivity."],
            "sensitive_assumptions": data.get("sensitive_assumptions") or [
                "Borrower interest rate stability.",
                "Sustained tenant occupancy without extended vacancy gaps.",
            ],
            "downside_scenarios_interpretation": data.get(
                "downside_scenarios_interpretation",
                "Stress-testing indicates vulnerabilities under rate increases and rent softened conditions.",
            ),
            "data_verification_checklist": data.get("data_verification_checklist") or risk.external_verification_checklist,
            "benchmark_comparison_analysis": data.get(
                "benchmark_comparison_analysis",
                "Micro-market benchmark data provides baseline orientation for valuation comparison."
                if benchmark
                else "Insufficient market data for deep locality statistical comparison.",
            ),
            "model_used": self.ollama.model,
            "inference_time_ms": res.get("total_duration_ms"),
            "disclaimer": "AI risk explanation is based on local deterministic calculations. Physical title search and legal verification are mandatory.",
        }


ai_analysis_service = AIAnalysisService()
