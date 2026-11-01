from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ScoringWeights(BaseModel):
    gross_yield_weight: float = Field(default=0.25, ge=0, le=1.0)
    net_yield_weight: float = Field(default=0.20, ge=0, le=1.0)
    cash_flow_weight: float = Field(default=0.25, ge=0, le=1.0)
    debt_burden_weight: float = Field(default=0.10, ge=0, le=1.0)
    expense_ratio_weight: float = Field(default=0.10, ge=0, le=1.0)
    data_completeness_weight: float = Field(default=0.10, ge=0, le=1.0)


class DealScoringEngine:
    @staticmethod
    def evaluate_deal(
        purchase_price_inr: float,
        built_up_area_sqft: float,
        gross_monthly_rent_inr: float,
        monthly_maintenance_inr: float,
        monthly_emi_inr: float,
        gross_rental_yield_pct: float,
        net_rental_yield_pct: float,
        monthly_net_cash_flow_inr: float,
        vacancy_rate_pct: float = 5.0,
        has_source_url: bool = False,
        has_property_age: bool = False,
        has_market_comparables: bool = False,
        weights: Optional[ScoringWeights] = None,
    ) -> Dict[str, Any]:
        """
        Compute an explainable, deterministic 0-100 investment score for Indian properties.
        Generates positive factors, negative factors, risk flags, and transparency caveats.
        """
        w = weights or ScoringWeights()
        positive_factors: List[str] = []
        negative_factors: List[str] = []
        risk_flags: List[str] = []

        # -------------------------------------------------------------
        # 1. Gross Rental Yield Scoring (Indian National Avg: ~3.25%)
        # -------------------------------------------------------------
        if gross_rental_yield_pct >= 5.0:
            gross_score = min(100.0, 90.0 + (gross_rental_yield_pct - 5.0) * 10.0)
            positive_factors.append(
                f"Exceptional gross rental yield of {gross_rental_yield_pct:.2f}% (national benchmark: ~3.25%)."
            )
        elif gross_rental_yield_pct >= 4.0:
            gross_score = 75.0 + (gross_rental_yield_pct - 4.0) * 15.0
            positive_factors.append(
                f"Strong gross rental yield of {gross_rental_yield_pct:.2f}%, well above Tier-1 Indian city medians."
            )
        elif gross_rental_yield_pct >= 3.25:
            gross_score = 60.0 + (gross_rental_yield_pct - 3.25) * 20.0
            positive_factors.append(
                f"Moderate gross rental yield of {gross_rental_yield_pct:.2f}%, in line with Indian metro benchmarks."
            )
        elif gross_rental_yield_pct >= 2.5:
            gross_score = 40.0 + (gross_rental_yield_pct - 2.5) * 26.6
            negative_factors.append(
                f"Compressed gross rental yield of {gross_rental_yield_pct:.2f}%; high capital appreciation will be required to justify returns."
            )
        else:
            gross_score = max(10.0, gross_rental_yield_pct * 16.0)
            negative_factors.append(
                f"Critically low gross rental yield of {gross_rental_yield_pct:.2f}% (<2.5%); strong indicator of premium/overpriced capital valuation."
            )
            risk_flags.append("Severely compressed rental yield (<2.50%).")

        # -------------------------------------------------------------
        # 2. Net Rental Yield Scoring
        # -------------------------------------------------------------
        if net_rental_yield_pct >= 4.0:
            net_score = min(100.0, 85.0 + (net_rental_yield_pct - 4.0) * 15.0)
            positive_factors.append(
                f"Healthy net yield of {net_rental_yield_pct:.2f}% after accounting for maintenance and vacancy reserves."
            )
        elif net_rental_yield_pct >= 3.0:
            net_score = 70.0 + (net_rental_yield_pct - 3.0) * 15.0
        elif net_rental_yield_pct >= 2.0:
            net_score = 50.0 + (net_rental_yield_pct - 2.0) * 20.0
        elif net_rental_yield_pct >= 1.0:
            net_score = 30.0 + (net_rental_yield_pct - 1.0) * 20.0
            negative_factors.append(
                f"Low net rental yield of {net_rental_yield_pct:.2f}% due to acquisition closing costs and ongoing operating deductions."
            )
        else:
            net_score = max(5.0, net_rental_yield_pct * 30.0)
            negative_factors.append(
                f"Sub-1% net rental yield ({net_rental_yield_pct:.2f}%); operating expenses consume most rental income."
            )
            risk_flags.append("Net rental yield below 1.50%.")

        # -------------------------------------------------------------
        # 3. Monthly Cash Flow Scoring
        # -------------------------------------------------------------
        if monthly_net_cash_flow_inr >= 15000:
            cash_flow_score = min(100.0, 85.0 + (monthly_net_cash_flow_inr - 15000) / 1000.0)
            positive_factors.append(
                f"Substantial positive monthly cash flow (+₹{monthly_net_cash_flow_inr:,.0f}/mo) providing strong liquidity buffer."
            )
        elif monthly_net_cash_flow_inr >= 5000:
            cash_flow_score = 70.0 + (monthly_net_cash_flow_inr - 5000) / 666.0
            positive_factors.append(
                f"Positive net monthly cash flow (+₹{monthly_net_cash_flow_inr:,.0f}/mo) covering debt and operating charges."
            )
        elif monthly_net_cash_flow_inr >= 0:
            cash_flow_score = 55.0 + (monthly_net_cash_flow_inr / 5000.0) * 15.0
            positive_factors.append("Break-even cash flow; rental income covers ongoing EMI and maintenance obligations.")
        elif monthly_net_cash_flow_inr >= -10000:
            cash_flow_score = max(30.0, 50.0 + (monthly_net_cash_flow_inr / 10000.0) * 20.0)
            negative_factors.append(
                f"Negative monthly cash flow (-₹{abs(monthly_net_cash_flow_inr):,.0f}/mo); requires monthly out-of-pocket investor contribution."
            )
            risk_flags.append(f"Negative monthly cash flow (-₹{abs(monthly_net_cash_flow_inr):,.0f}/mo).")
        else:
            cash_flow_score = max(10.0, 30.0 - (abs(monthly_net_cash_flow_inr) - 10000) / 2000.0)
            negative_factors.append(
                f"Severe negative monthly cash drain (-₹{abs(monthly_net_cash_flow_inr):,.0f}/mo); high recurring holding liability."
            )
            risk_flags.append(f"High negative cash flow drain (-₹{abs(monthly_net_cash_flow_inr):,.0f}/mo).")

        # -------------------------------------------------------------
        # 4. Debt Burden & Coverage Scoring (Rent-to-EMI Ratio)
        # -------------------------------------------------------------
        if monthly_emi_inr <= 0:
            debt_score = 100.0
            positive_factors.append("No active debt obligation (cash acquisition model).")
        else:
            rent_to_emi = gross_monthly_rent_inr / monthly_emi_inr if monthly_emi_inr > 0 else 0.0
            if rent_to_emi >= 1.25:
                debt_score = 95.0
                positive_factors.append(
                    f"Strong debt service coverage (Rent covers {rent_to_emi:.2f}x of EMI)."
                )
            elif rent_to_emi >= 1.0:
                debt_score = 75.0 + (rent_to_emi - 1.0) * 80.0
                positive_factors.append(
                    f"Rental income fully services home loan EMI (coverage: {rent_to_emi:.2f}x)."
                )
            elif rent_to_emi >= 0.75:
                debt_score = 50.0 + (rent_to_emi - 0.75) * 100.0
                negative_factors.append(
                    f"Rental income covers only {rent_to_emi * 100:.0f}% of home loan EMI."
                )
            else:
                debt_score = max(15.0, rent_to_emi * 66.0)
                negative_factors.append(
                    f"Heavy debt burden: EMI (₹{monthly_emi_inr:,.0f}) significantly exceeds monthly rent (₹{gross_monthly_rent_inr:,.0f})."
                )
                risk_flags.append(f"High debt service burden (EMI exceeds rent by ₹{monthly_emi_inr - gross_monthly_rent_inr:,.0f}).")

        # -------------------------------------------------------------
        # 5. Operating Expense Ratio Scoring (Maintenance / Rent)
        # -------------------------------------------------------------
        expense_ratio = (
            (monthly_maintenance_inr / gross_monthly_rent_inr) * 100.0
            if gross_monthly_rent_inr > 0
            else 0.0
        )
        if expense_ratio <= 10.0:
            expense_score = 95.0
        elif expense_ratio <= 20.0:
            expense_score = 75.0 + (20.0 - expense_ratio) * 2.0
        elif expense_ratio <= 35.0:
            expense_score = 50.0 + (35.0 - expense_ratio) * 1.66
            negative_factors.append(
                f"Relatively high maintenance overhead ({expense_ratio:.1f}% of monthly rental revenue)."
            )
        else:
            expense_score = max(20.0, 50.0 - (expense_ratio - 35.0) * 1.5)
            negative_factors.append(
                f"Elevated recurring maintenance ratio ({expense_ratio:.1f}% of rent) compressing net margins."
            )
            risk_flags.append(f"High maintenance burden ({expense_ratio:.1f}% of rent).")

        # -------------------------------------------------------------
        # 6. Data Completeness & Verification Scoring
        # -------------------------------------------------------------
        completeness_points = 100.0
        if not has_source_url:
            completeness_points -= 15.0
        if not has_property_age:
            completeness_points -= 10.0
        if monthly_maintenance_inr == 0:
            completeness_points -= 15.0
            negative_factors.append(
                "Maintenance charge recorded as ₹0; verify if society maintenance is unbilled or absent."
            )
            risk_flags.append("Zero maintenance recorded — potential missing recurring expense.")
        if built_up_area_sqft <= 0:
            completeness_points -= 30.0

        completeness_score = max(20.0, completeness_points)

        # -------------------------------------------------------------
        # Calculate Weighted Aggregate Score (0 to 100)
        # -------------------------------------------------------------
        raw_score = (
            gross_score * w.gross_yield_weight
            + net_score * w.net_yield_weight
            + cash_flow_score * w.cash_flow_weight
            + debt_score * w.debt_burden_weight
            + expense_score * w.expense_ratio_weight
            + completeness_score * w.data_completeness_weight
        )

        overall_score = round(max(0.0, min(100.0, raw_score)), 1)

        # -------------------------------------------------------------
        # Classification Mapping (Deterministic Screening Categories)
        # -------------------------------------------------------------
        if monthly_net_cash_flow_inr < -15000 and debt_score < 40:
            classification = "High Risk"
            explanation = (
                "Heavy monthly cash drain combined with elevated debt obligations presents severe cash-flow risk."
            )
        elif overall_score >= 80.0:
            classification = "Excellent Deal"
            explanation = (
                "Above-market rental yields paired with positive cash flow and healthy debt coverage."
            )
        elif overall_score >= 68.0:
            classification = "Good Deal"
            explanation = (
                "Solid fundamentals with yields meeting or beating Indian benchmarks and sustainable debt metrics."
            )
        elif overall_score >= 52.0:
            classification = "Average Deal"
            explanation = (
                "Typical Indian urban residential yield profile; requires steady capital appreciation to deliver target IRR."
            )
        elif overall_score >= 38.0:
            classification = "Overpriced"
            explanation = (
                "Compressed yield profile where capital asking price is disproportionately high relative to rental generation."
            )
        else:
            classification = "High Risk"
            explanation = (
                "Weak cash flow, compressed yield profile, or significant missing financial information."
            )

        # Explicit limitation caveat
        valuation_limitation_note = (
            "Analytical screening classification based strictly on deterministic mathematical models. "
            "Does not constitute guaranteed investment advice. "
            + (
                "Valuation assessment is based on asset-level cash flows; macro locality comparable data is unlinked."
                if not has_market_comparables
                else "Locality comparable benchmarks applied."
            )
        )

        return {
            "overall_score": int(round(overall_score)),
            "classification": classification,
            "explanation": explanation,
            "metric_scores": {
                "gross_yield_score": round(gross_score, 1),
                "net_yield_score": round(net_score, 1),
                "cash_flow_score": round(cash_flow_score, 1),
                "debt_burden_score": round(debt_score, 1),
                "expense_ratio_score": round(expense_score, 1),
                "data_completeness_score": round(completeness_score, 1),
            },
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "risk_flags": risk_flags,
            "disclaimer": valuation_limitation_note,
        }


deal_scoring_engine = DealScoringEngine()

