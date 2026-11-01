from typing import Dict, Any, List, Optional
from app.models.property import Property
from app.models.benchmark import MarketBenchmark
from app.schemas.risk import (
    RiskCategoryDetail,
    RiskScoreBreakdown,
    WhatIfSimulationInputs,
    ScenarioOutcome,
    WhatIfSimulationResponse,
    DataConfidenceResponse,
)
from app.services.financial_engine import (
    financial_engine,
    AcquisitionCostInputs,
    LoanInputs,
    OperatingExpenseInputs,
)
from app.utils.financial import format_inr


class RiskEngine:
    def __init__(self):
        # Configurable category weights summing to 1.0
        self.weights = {
            "financial": 0.25,
            "loan": 0.25,
            "rental": 0.20,
            "data_reliability": 0.15,
            "external_verification": 0.15,
        }

    def evaluate_risk(
        self,
        prop: Property,
        fin_analysis: Any,
        benchmark: Optional[MarketBenchmark] = None,
    ) -> RiskScoreBreakdown:
        """
        Compute an explainable, multi-dimensional risk exposure score (0-100)
        and an independent data confidence score (0-100).
        Distinguishes calculated financial risks from information gaps and legal requirements.
        """
        price = prop.purchase_price_inr
        rent = prop.expected_monthly_rent_inr
        maint = prop.monthly_maintenance_inr
        acq = fin_analysis.acquisition_costs
        loan = fin_analysis.loan_metrics
        op = fin_analysis.operating_finances
        ret = fin_analysis.returns
        score = fin_analysis.deal_score

        # -------------------------------------------------------------
        # 1. Financial Risk (0 to 100)
        # -------------------------------------------------------------
        fin_factors = []
        fin_mitigations = []
        fin_score = 0.0

        monthly_cash_flow = ret.get("monthly_net_cash_flow_inr", 0)
        gross_yield = ret.get("gross_rental_yield_pct", 0)
        net_yield = ret.get("net_rental_yield_pct", 0)
        closing_costs = acq.get("total_closing_costs_inr", 0)
        closing_pct = (closing_costs / price * 100) if price > 0 else 0

        # Cash Flow
        if monthly_cash_flow < 0:
            fin_score += 45.0
            fin_factors.append(f"Negative monthly cash flow: {format_inr(monthly_cash_flow)}/mo deficit requiring ongoing capital subsidy.")
            fin_mitigations.append("Increase down payment or negotiate lower purchase price to eliminate monthly cash deficit.")
        elif monthly_cash_flow < 5000:
            fin_score += 25.0
            fin_factors.append(f"Thin cash flow buffer: {format_inr(monthly_cash_flow)}/mo offers minimal cushion for surprise repairs.")
            fin_mitigations.append("Set aside a 6-month contingency fund for unanticipated repairs.")
        else:
            fin_score += 5.0
            fin_factors.append(f"Healthy positive cash flow of {format_inr(monthly_cash_flow)}/mo.")

        # Rental Yields
        if gross_yield < 2.5:
            fin_score += 35.0
            fin_factors.append(f"Severe gross yield compression ({gross_yield}%): well below Indian residential average (3.5% - 4.5%).")
            fin_mitigations.append("Target micro-markets with stronger tenant demand to avoid capital stagnation.")
        elif gross_yield < 3.5:
            fin_score += 20.0
            fin_factors.append(f"Sub-optimal gross yield of {gross_yield}%.")
        else:
            fin_score += 5.0

        # Net Operating Yield
        if net_yield < 2.0:
            fin_score += 15.0
            fin_factors.append(f"Net rental yield ({net_yield}%) is lower than traditional fixed deposits.")
        else:
            fin_score += 5.0

        # Acquisition closing costs
        if closing_pct > 10.0:
            fin_score += 10.0
            fin_factors.append(f"High acquisition closing costs ({closing_pct:.1f}% of price) lengthen break-even horizon.")

        fin_score = min(100.0, max(5.0, fin_score))
        fin_level = "Severe" if fin_score >= 70 else "Elevated" if fin_score >= 45 else "Moderate" if fin_score >= 25 else "Low"

        # -------------------------------------------------------------
        # 2. Loan & Leverage Risk (0 to 100)
        # -------------------------------------------------------------
        loan_factors = []
        loan_mitigations = []
        loan_score = 0.0

        monthly_emi = loan.get("monthly_emi_inr", 0)
        loan_principal = loan.get("loan_principal_inr", 0)
        ltv_pct = (loan_principal / price * 100) if price > 0 else 0
        emi_to_rent_ratio = (monthly_emi / rent * 100) if rent > 0 else 100.0

        if emi_to_rent_ratio > 90.0:
            loan_score += 45.0
            loan_factors.append(f"Critical EMI-to-Rent debt burden ({emi_to_rent_ratio:.1f}%): Rent cannot absorb vacancies without default risk.")
            loan_mitigations.append("Reduce debt leverage by increasing equity down payment above 35%.")
        elif emi_to_rent_ratio > 70.0:
            loan_score += 30.0
            loan_factors.append(f"Elevated debt service load ({emi_to_rent_ratio:.1f}% of rent dedicated to EMI).")
            loan_mitigations.append("Consider opting for a longer tenure or prepayment to reduce monthly EMI burden.")
        else:
            loan_score += 10.0
            loan_factors.append(f"Moderate EMI-to-Rent burden ({emi_to_rent_ratio:.1f}%).")

        if ltv_pct > 80.0:
            loan_score += 25.0
            loan_factors.append(f"High Loan-To-Value (LTV: {ltv_pct:.1f}%), leaving little equity protection against price corrections.")
        elif ltv_pct > 60.0:
            loan_score += 15.0
        else:
            loan_score += 5.0

        # Sensitivity to interest rate hike (+1.5%)
        stressed_loan = financial_engine.calculate_loan_emi(
            LoanInputs(
                purchase_price_inr=price,
                down_payment_pct=loan.get("down_payment_pct", 20.0),
                annual_interest_rate_pct=loan.get("annual_interest_rate_pct", 8.5) + 1.5,
                tenure_years=loan.get("tenure_years", 20),
            )
        )
        stressed_emi_diff = stressed_loan["monthly_emi_inr"] - monthly_emi
        if stressed_emi_diff > 3000:
            loan_score += 15.0
            loan_factors.append(f"Interest Rate Hike Exposure: A +1.5% repo rate increase adds {format_inr(stressed_emi_diff)}/mo to your EMI.")
            loan_mitigations.append("Model floating rate resets and maintain liquidity for interest rate spikes.")

        loan_score = min(100.0, max(5.0, loan_score))
        loan_level = "Severe" if loan_score >= 70 else "Elevated" if loan_score >= 45 else "Moderate" if loan_score >= 25 else "Low"

        # -------------------------------------------------------------
        # 3. Rental & Operational Risk (0 to 100)
        # -------------------------------------------------------------
        rental_factors = []
        rental_mitigations = []
        rental_score = 0.0

        vacancy_rate = op.get("vacancy_rate_pct", 5.0)
        maintenance_ratio = (maint / rent * 100) if rent > 0 else 0

        if vacancy_rate >= 10.0:
            rental_score += 35.0
            rental_factors.append(f"Extended vacancy exposure assumed at {vacancy_rate}% (~36+ unoccupied days annually).")
            rental_mitigations.append("Partner with local leasing agencies or verify rental demand with resident associations.")
        else:
            rental_score += 10.0
            rental_factors.append(f"Standard vacancy allowance assumed at {vacancy_rate}%.")

        if maintenance_ratio > 18.0:
            rental_score += 30.0
            rental_factors.append(f"High maintenance load: {maintenance_ratio:.1f}% of monthly rent consumed by society/amenity charges.")
            rental_mitigations.append("Audit society maintenance accounts for pending special assessments or lift/generator replacement funds.")
        elif maintenance_ratio > 10.0:
            rental_score += 15.0
            rental_factors.append(f"Moderate maintenance cost ratio ({maintenance_ratio:.1f}% of rent).")
        else:
            rental_score += 5.0

        # Rent decline test (-10%)
        rent_drop_net_cash = monthly_cash_flow - (rent * 0.10)
        if rent_drop_net_cash < 0 and monthly_cash_flow >= 0:
            rental_score += 25.0
            rental_factors.append(f"Downside vulnerability: A 10% market rent reduction would flip cash flow negative ({format_inr(rent_drop_net_cash)}/mo).")
            rental_mitigations.append("Secure multi-year corporate leases with fixed lock-in periods where feasible.")

        rental_score = min(100.0, max(5.0, rental_score))
        rental_level = "Severe" if rental_score >= 70 else "Elevated" if rental_score >= 45 else "Moderate" if rental_score >= 25 else "Low"

        # -------------------------------------------------------------
        # 4. Data Reliability Risk (0 to 100)
        # -------------------------------------------------------------
        data_factors = []
        data_mitigations = []
        data_score = 0.0

        if not prop.source_url:
            data_score += 35.0
            data_factors.append("Missing listing source URL: Listing cannot be independently corroborated online.")
            data_mitigations.append("Request original web listing link or physical broker agreement.")
        else:
            data_score += 5.0
            data_factors.append("Listing source URL is recorded for provenance check.")

        if not prop.property_age:
            data_score += 25.0
            data_factors.append("Property age is unspecified: Unable to evaluate structural depreciation or remaining lifespan.")
            data_mitigations.append("Inspect building completion certificate and municipal tax receipts for construction date.")
        else:
            data_score += 5.0
            data_factors.append(f"Property age noted as: {prop.property_age}.")

        if prop.is_demo:
            data_score += 20.0
            data_factors.append("Listing is simulated DEMO DATA created for analytical modeling.")

        if prop.listing_source in ["Unknown", "Unverified", "Direct Listing"]:
            data_score += 15.0
            data_factors.append(f"Listing source '{prop.listing_source}' has not undergone portal verification.")

        data_score = min(100.0, max(5.0, data_score))
        data_level = "Severe" if data_score >= 70 else "Elevated" if data_score >= 45 else "Moderate" if data_score >= 25 else "Low"

        # -------------------------------------------------------------
        # 5. External Verification Risk (0 to 100)
        # -------------------------------------------------------------
        ext_factors = [
            "RERA Project Registration and complaint history pending manual verification.",
            "30-year Encumbrance Certificate (EC) from Sub-Registrar Office pending legal review.",
            "Occupancy Certificate (OC) and building sanction plan compliance pending verification.",
            "Society NOC, property tax receipts, and municipal water connections require physical inspection.",
            "Physical structural audit required to rule out foundation or dampness issues.",
        ]
        ext_mitigations = [
            "Hire a licensed real estate advocate to execute a 30-year title search at the local Sub-Registrar Office.",
            "Verify the project on the state RERA web portal (e.g. MahaRERA, TS RERA, Karnataka RERA).",
            "Demand original Occupancy Certificate (OC) from the seller prior to paying advance token money.",
        ]
        ext_score = 65.0  # Real estate transactions inherently require external verification until verified by advocate
        ext_level = "Elevated"

        # -------------------------------------------------------------
        # Overall Risk Exposure Score Calculation
        # -------------------------------------------------------------
        overall_risk_score = round(
            self.weights["financial"] * fin_score
            + self.weights["loan"] * loan_score
            + self.weights["rental"] * rental_score
            + self.weights["data_reliability"] * data_score
            + self.weights["external_verification"] * ext_score,
            1,
        )

        overall_risk_level = (
            "Critical Risk"
            if overall_risk_score >= 75
            else "High Risk"
            if overall_risk_score >= 60
            else "Elevated Risk"
            if overall_risk_score >= 45
            else "Moderate Risk"
            if overall_risk_score >= 30
            else "Low Risk"
        )

        # -------------------------------------------------------------
        # Data Confidence Score (0 to 100, independent of attractiveness)
        # -------------------------------------------------------------
        confidence_score, confidence_level, confidence_reasons = self.calculate_data_confidence(
            prop, benchmark
        )

        # Critical Red Flags (Deal Breakers)
        red_flags = []
        if monthly_cash_flow < -10000:
            red_flags.append(f"Severe negative monthly cash drain ({format_inr(monthly_cash_flow)}/mo).")
        if emi_to_rent_ratio > 95.0:
            red_flags.append(f"Critical debt burden: EMI exceeds 95% of expected gross rent.")
        if gross_yield < 2.5:
            red_flags.append("Gross rental yield is severely compressed below 2.5%.")
        if not prop.source_url and not prop.property_age:
            red_flags.append("High information deficit: Missing both source provenance and construction age.")

        categories = {
            "financial": RiskCategoryDetail(
                category_id="financial",
                category_name="Financial & Yield Risk",
                score=fin_score,
                risk_level=fin_level,
                factors=fin_factors,
                mitigation_steps=fin_mitigations,
            ),
            "loan": RiskCategoryDetail(
                category_id="loan",
                category_name="Loan & Leverage Risk",
                score=loan_score,
                risk_level=loan_level,
                factors=loan_factors,
                mitigation_steps=loan_mitigations,
            ),
            "rental": RiskCategoryDetail(
                category_id="rental",
                category_name="Rental & Operational Risk",
                score=rental_score,
                risk_level=rental_level,
                factors=rental_factors,
                mitigation_steps=rental_mitigations,
            ),
            "data_reliability": RiskCategoryDetail(
                category_id="data_reliability",
                category_name="Data Reliability & Provenance",
                score=data_score,
                risk_level=data_level,
                factors=data_factors,
                mitigation_steps=data_mitigations,
            ),
            "external_verification": RiskCategoryDetail(
                category_id="external_verification",
                category_name="External Legal Due Diligence",
                score=ext_score,
                risk_level=ext_level,
                factors=ext_factors,
                mitigation_steps=ext_mitigations,
            ),
        }

        # Investment Attractiveness (reused from Phase 3 deterministic deal scoring)
        attractiveness_score = float(score.get("overall_score", 50))

        return RiskScoreBreakdown(
            property_id=prop.id,
            property_title=prop.title,
            city=prop.city,
            locality=prop.locality,
            investment_attractiveness_score=attractiveness_score,
            risk_exposure_score=overall_risk_score,
            data_confidence_score=confidence_score,
            overall_risk_level=overall_risk_level,
            data_confidence_level=confidence_level,
            categories=categories,
            critical_red_flags=red_flags,
            data_confidence_reasons=confidence_reasons,
            external_verification_checklist=[
                "Confirm clear title through minimum 30-year Encumbrance Certificate (EC).",
                "Verify project sanction on State RERA portal with valid registration number.",
                "Inspect sanctioned building plan vs actual as-built physical dimensions.",
                "Verify Occupancy Certificate (OC) has been issued by municipal corporation.",
                "Review latest property tax receipt and electricity bill in seller's name.",
            ],
            scoring_methodology={
                "weights": self.weights,
                "formula": "Overall Risk = 0.25*Financial + 0.25*Loan + 0.20*Rental + 0.15*Data + 0.15*Legal",
                "note": "Investment Attractiveness, Risk Exposure, and Data Confidence are evaluated as three independent scores.",
            },
            disclaimer="Risk scoring is deterministic and educational. Does not replace physical legal title verification by a qualified advocate.",
        )

    def calculate_data_confidence(
        self,
        prop: Property,
        benchmark: Optional[MarketBenchmark] = None,
    ) -> tuple[float, str, List[str]]:
        """
        Calculate an independent data confidence rating (0-100) reflecting
        the completeness and verifiable provenance of property records.
        """
        score = 0.0
        reasons = []

        # 1. Listing Source Presence (+25 pts)
        if prop.listing_source and prop.listing_source not in ["Unknown", "Unverified"]:
            score += 25.0
            reasons.append(f"Listing source identified: '{prop.listing_source}'.")
        else:
            reasons.append("Unidentified or anonymous listing source.")

        # 2. Source URL Presence (+20 pts)
        if prop.source_url and prop.source_url.startswith("http"):
            score += 20.0
            reasons.append("Direct listing URL is provided for online cross-referencing.")
        else:
            reasons.append("No verifiable web link or portal URL provided.")

        # 3. Property Age & Timing (+15 pts)
        if prop.property_age:
            score += 15.0
            reasons.append(f"Property construction age specified: '{prop.property_age}'.")
        else:
            reasons.append("Property age/completion status is missing.")

        # 4. Financial & Area Completeness (+20 pts)
        if prop.purchase_price_inr > 0 and prop.built_up_area_sqft > 0 and prop.expected_monthly_rent_inr > 0:
            score += 20.0
            reasons.append("Complete core financial data (Price, Area, Monthly Rent, Maintenance).")
        else:
            reasons.append("Incomplete operational financial inputs.")

        # 5. Locality Benchmark Corroboration (+20 pts)
        if benchmark:
            score += 20.0
            reasons.append(
                f"Corroborated by {benchmark.city} ({benchmark.locality}) benchmark from '{benchmark.data_source}' ({benchmark.verification_status})."
            )
        else:
            reasons.append("No micro-market benchmark dataset available for this specific locality.")

        # Penalize simulated demo data
        if prop.is_demo:
            score = max(20.0, score - 15.0)
            reasons.append("Listing is flagged as DEMO DATA (analytical simulation).")

        score = min(100.0, max(10.0, score))
        level = (
            "High Confidence"
            if score >= 80
            else "Moderate Confidence"
            if score >= 60
            else "Low Confidence"
            if score >= 40
            else "Unverified"
        )

        return round(score, 1), level, reasons

    def run_what_if_simulation(
        self,
        prop: Property,
        custom_inputs: Optional[WhatIfSimulationInputs] = None,
    ) -> WhatIfSimulationResponse:
        """
        Run deterministic scenario simulation across 6 standard stress-test scenarios
        plus an optional user-defined custom scenario.
        """
        base_price = prop.purchase_price_inr
        base_rent = prop.expected_monthly_rent_inr
        base_maint = prop.monthly_maintenance_inr
        base_area = prop.built_up_area_sqft

        # Predefined 6 Scenario Definitions
        scenario_configs = [
            {
                "id": "base",
                "name": "Base Scenario (Current Baseline)",
                "description": "Standard market baseline using current listing price, rent, and prevailing home loan terms.",
                "badge": "Expected",
                "price_mult": 1.0,
                "rent_mult": 1.0,
                "vacancy_pct": 5.0,
                "interest_rate": 8.5,
                "down_payment_pct": 20.0,
                "tenure": 20,
                "maint_mult": 1.0,
            },
            {
                "id": "conservative",
                "name": "Conservative Scenario (Prudent)",
                "description": "Conservative assumptions: 5% lower rent, 8% vacancy, interest rate at 9.25%, and 10% higher maintenance.",
                "badge": "Prudent",
                "price_mult": 1.0,
                "rent_mult": 0.95,
                "vacancy_pct": 8.0,
                "interest_rate": 9.25,
                "down_payment_pct": 20.0,
                "tenure": 20,
                "maint_mult": 1.10,
            },
            {
                "id": "optimistic",
                "name": "Optimistic Scenario (High Demand)",
                "description": "High tenant demand scenario: 8% higher rent, minimal 3% vacancy, and competitive 8.0% interest rate.",
                "badge": "Bull Market",
                "price_mult": 1.0,
                "rent_mult": 1.08,
                "vacancy_pct": 3.0,
                "interest_rate": 8.0,
                "down_payment_pct": 20.0,
                "tenure": 20,
                "maint_mult": 1.0,
            },
            {
                "id": "rental_decline",
                "name": "Rental Decline Shock (-15% Rent)",
                "description": "Local market supply surge or tech slowdown causing rental rates to soften by 15%.",
                "badge": "Market Softening",
                "price_mult": 1.0,
                "rent_mult": 0.85,
                "vacancy_pct": 8.0,
                "interest_rate": 8.5,
                "down_payment_pct": 20.0,
                "tenure": 20,
                "maint_mult": 1.0,
            },
            {
                "id": "rate_hike",
                "name": "Interest Rate Shock (+2.0% Hike)",
                "description": "Monetary tightening cycle: Home loan interest rate increases by 200 bps to 10.5%.",
                "badge": "Debt Stress",
                "price_mult": 1.0,
                "rent_mult": 1.0,
                "vacancy_pct": 5.0,
                "interest_rate": 10.5,
                "down_payment_pct": 20.0,
                "tenure": 20,
                "maint_mult": 1.0,
            },
            {
                "id": "extended_vacancy",
                "name": "Extended Vacancy Shock (~55 Days Unoccupied)",
                "description": "Tenant turnover lag or difficult leasing period causing 15% annual vacancy allowance.",
                "badge": "Vacancy Shock",
                "price_mult": 1.0,
                "rent_mult": 1.0,
                "vacancy_pct": 15.0,
                "interest_rate": 8.5,
                "down_payment_pct": 20.0,
                "tenure": 20,
                "maint_mult": 1.15,
            },
        ]

        def compute_scenario_outcome(cfg: Dict[str, Any], custom_title: Optional[str] = None) -> ScenarioOutcome:
            s_price = round(cfg["price_inr"] if "price_inr" in cfg else cfg["price_mult"] * base_price, 2)
            s_rent = round(cfg["rent_inr"] if "rent_inr" in cfg else cfg["rent_mult"] * base_rent, 2)
            s_maint = round(cfg["maint_inr"] if "maint_inr" in cfg else cfg["maint_mult"] * base_maint, 2)
            s_vac = cfg["vacancy_pct"]
            s_rate = cfg["interest_rate"]
            s_dp = cfg["down_payment_pct"]
            s_ten = cfg["tenure"]

            # Acquisition Closing Costs (standard 7% closing)
            closing_costs = round(s_price * 0.07, 2)
            total_acq_cost = round(s_price + closing_costs, 2)

            # Loan & EMI
            loan_res = financial_engine.calculate_loan_emi(
                LoanInputs(
                    purchase_price_inr=s_price,
                    down_payment_pct=s_dp,
                    annual_interest_rate_pct=s_rate,
                    tenure_years=s_ten,
                )
            )

            # Operating Finances
            op_res = financial_engine.calculate_operating_finances(
                OperatingExpenseInputs(
                    expected_monthly_rent_inr=s_rent,
                    monthly_maintenance_inr=s_maint,
                    vacancy_rate_pct=s_vac,
                )
            )

            # Returns
            ret_res = financial_engine.calculate_investment_returns(
                purchase_price_inr=s_price,
                total_acquisition_cost_inr=total_acq_cost,
                down_payment_inr=loan_res["down_payment_inr"],
                total_closing_costs_inr=closing_costs,
                monthly_emi_inr=loan_res["monthly_emi_inr"],
                annual_gross_rent_inr=op_res["annual_gross_rent_inr"],
                annual_noi_inr=op_res["annual_noi_inr"],
            )

            # Fast Risk Level for this scenario
            c_flow = ret_res["monthly_net_cash_flow_inr"]
            g_yield = ret_res["gross_rental_yield_pct"]
            emi = loan_res["monthly_emi_inr"]
            emi_rent = (emi / s_rent * 100) if s_rent > 0 else 100

            s_risk_score = 30.0
            if c_flow < 0:
                s_risk_score += 35.0
            if emi_rent > 80:
                s_risk_score += 25.0
            if g_yield < 3.0:
                s_risk_score += 15.0
            s_risk_score = min(100.0, max(10.0, s_risk_score))

            s_risk_level = "Severe" if s_risk_score >= 70 else "Elevated" if s_risk_score >= 50 else "Moderate" if s_risk_score >= 35 else "Low"

            return ScenarioOutcome(
                scenario_id=cfg["id"],
                scenario_name=custom_title or cfg["name"],
                description=cfg["description"],
                badge=cfg["badge"],
                purchase_price_inr=s_price,
                monthly_rent_inr=s_rent,
                vacancy_rate_pct=s_vac,
                interest_rate_pct=s_rate,
                down_payment_pct=s_dp,
                tenure_years=s_ten,
                monthly_emi_inr=loan_res["monthly_emi_inr"],
                monthly_noi_inr=op_res["monthly_noi_inr"],
                monthly_cash_flow_inr=ret_res["monthly_net_cash_flow_inr"],
                gross_rental_yield_pct=ret_res["gross_rental_yield_pct"],
                net_rental_yield_pct=ret_res["net_rental_yield_pct"],
                cash_on_cash_roi_pct=ret_res["cash_on_cash_roi_pct"],
                risk_score=s_risk_score,
                risk_level=s_risk_level,
                break_even_summary=ret_res["break_even"]["summary"],
            )

        outcomes = [compute_scenario_outcome(cfg) for cfg in scenario_configs]
        base_case = outcomes[0]

        # Custom Scenario computation if user provided override parameters
        custom_outcome = None
        if custom_inputs:
            c_price = custom_inputs.purchase_price_inr if custom_inputs.purchase_price_inr is not None else base_price
            c_rent = custom_inputs.expected_monthly_rent_inr if custom_inputs.expected_monthly_rent_inr is not None else base_rent
            c_maint = (custom_inputs.annual_maintenance_inr / 12) if custom_inputs.annual_maintenance_inr is not None else base_maint
            c_vac = custom_inputs.vacancy_rate_pct if custom_inputs.vacancy_rate_pct is not None else 5.0
            c_rate = custom_inputs.annual_interest_rate_pct if custom_inputs.annual_interest_rate_pct is not None else 8.5
            c_dp = custom_inputs.down_payment_pct if custom_inputs.down_payment_pct is not None else 20.0
            c_ten = custom_inputs.tenure_years if custom_inputs.tenure_years is not None else 20

            custom_cfg = {
                "id": "custom",
                "name": "Custom User Simulation",
                "description": "User-defined custom financial parameters.",
                "badge": "Custom Model",
                "price_inr": c_price,
                "rent_inr": c_rent,
                "maint_inr": c_maint,
                "vacancy_pct": c_vac,
                "interest_rate": c_rate,
                "down_payment_pct": c_dp,
                "tenure": c_ten,
            }
            custom_outcome = compute_scenario_outcome(custom_cfg, "Custom Scenario")

        # Analytical conclusions
        insights = []
        rate_hike_sc = next((s for s in outcomes if s.scenario_id == "rate_hike"), None)
        rent_drop_sc = next((s for s in outcomes if s.scenario_id == "rental_decline"), None)

        if rate_hike_sc and rate_hike_sc.monthly_cash_flow_inr < 0 and base_case.monthly_cash_flow_inr >= 0:
            insights.append("Interest Rate Sensitivity: A +2.0% rate increase turns this property cash-flow negative.")
        if rent_drop_sc and rent_drop_sc.monthly_cash_flow_inr < 0:
            insights.append("Rental Income Vulnerability: A 15% rent decline causes an operating cash deficit.")
        if base_case.gross_rental_yield_pct >= 4.5:
            insights.append("Yield Buffer: The property's high gross yield provides resilience against modest cost inflation.")
        else:
            insights.append("Compressed Margins: Thin baseline yield requires disciplined debt management.")

        return WhatIfSimulationResponse(
            property_id=prop.id,
            property_title=prop.title,
            base_case=base_case,
            scenarios=outcomes,
            custom_simulation=custom_outcome,
            insights=insights,
        )


risk_engine = RiskEngine()
