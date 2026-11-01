import math
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class AcquisitionCostInputs(BaseModel):
    purchase_price_inr: float = Field(..., gt=0, description="Purchase price of the property in INR")
    stamp_duty_rate_pct: Optional[float] = Field(None, ge=0, le=25, description="Stamp duty rate % (e.g. 5.0% - 7.5%)")
    stamp_duty_inr: Optional[float] = Field(None, ge=0, description="Explicit stamp duty amount in INR")
    registration_rate_pct: Optional[float] = Field(None, ge=0, le=10, description="Registration charge % (e.g. 1.0%)")
    registration_inr: Optional[float] = Field(None, ge=0, description="Explicit registration charge in INR")
    brokerage_rate_pct: Optional[float] = Field(None, ge=0, le=10, description="Brokerage commission % (e.g. 1.0% - 2.0%)")
    brokerage_inr: Optional[float] = Field(None, ge=0, description="Explicit brokerage commission in INR")
    renovation_expenses_inr: float = Field(default=0.0, ge=0, description="Interior & renovation expenses in INR")
    other_acquisition_costs_inr: float = Field(default=0.0, ge=0, description="Other acquisition expenses (legal, inspection) in INR")


class LoanInputs(BaseModel):
    purchase_price_inr: float = Field(..., gt=0, description="Property purchase price in INR")
    down_payment_pct: float = Field(default=20.0, ge=0, le=100, description="Down payment percentage (e.g. 20.0%)")
    annual_interest_rate_pct: float = Field(default=8.5, ge=0, le=30, description="Annual home loan interest rate % (e.g. 8.5%)")
    tenure_years: int = Field(default=20, ge=1, le=40, description="Home loan tenure in years (e.g. 15, 20, 30)")


class OperatingExpenseInputs(BaseModel):
    expected_monthly_rent_inr: float = Field(..., ge=0, description="Gross expected monthly rental income in INR")
    monthly_maintenance_inr: float = Field(default=0.0, ge=0, description="Monthly society/amenity maintenance in INR")
    vacancy_rate_pct: float = Field(default=5.0, ge=0, le=50, description="Estimated vacancy rate % (e.g. 5.0% = ~18 days/yr)")
    property_management_pct: float = Field(default=0.0, ge=0, le=30, description="Property management fee % of rent")
    other_monthly_expenses_inr: float = Field(default=0.0, ge=0, description="Other monthly expenses (property tax, insurance)")


class FinancialEngine:
    @staticmethod
    def calculate_price_per_sqft(purchase_price_inr: float, built_up_area_sqft: float) -> float:
        """Calculate Price Per Square Foot in INR."""
        if built_up_area_sqft <= 0 or purchase_price_inr <= 0:
            return 0.0
        return round(purchase_price_inr / built_up_area_sqft, 2)

    @staticmethod
    def calculate_acquisition_costs(inputs: AcquisitionCostInputs) -> Dict[str, Any]:
        """
        Calculate total acquisition cost including stamp duty, registration,
        brokerage, renovation, and closing costs without hardcoding static state rates.
        """
        price = inputs.purchase_price_inr

        # 1. Stamp Duty
        if inputs.stamp_duty_inr is not None:
            stamp_duty = inputs.stamp_duty_inr
            stamp_duty_pct = round((stamp_duty / price) * 100, 2) if price > 0 else 0.0
        elif inputs.stamp_duty_rate_pct is not None:
            stamp_duty_pct = inputs.stamp_duty_rate_pct
            stamp_duty = round(price * (stamp_duty_pct / 100), 2)
        else:
            # Default Indian benchmark average stamp duty (6.0%)
            stamp_duty_pct = 6.0
            stamp_duty = round(price * 0.06, 2)

        # 2. Registration Charges
        if inputs.registration_inr is not None:
            registration = inputs.registration_inr
            registration_pct = round((registration / price) * 100, 2) if price > 0 else 0.0
        elif inputs.registration_rate_pct is not None:
            registration_pct = inputs.registration_rate_pct
            registration = round(price * (registration_pct / 100), 2)
        else:
            # Standard Indian registration fee (1.0%)
            registration_pct = 1.0
            registration = round(price * 0.01, 2)

        # 3. Brokerage
        if inputs.brokerage_inr is not None:
            brokerage = inputs.brokerage_inr
            brokerage_pct = round((brokerage / price) * 100, 2) if price > 0 else 0.0
        elif inputs.brokerage_rate_pct is not None:
            brokerage_pct = inputs.brokerage_rate_pct
            brokerage = round(price * (brokerage_pct / 100), 2)
        else:
            brokerage_pct = 0.0
            brokerage = 0.0

        renovation = max(0.0, inputs.renovation_expenses_inr)
        other_costs = max(0.0, inputs.other_acquisition_costs_inr)

        total_acquisition_cost = round(price + stamp_duty + registration + brokerage + renovation + other_costs, 2)
        total_closing_costs = round(stamp_duty + registration + brokerage + renovation + other_costs, 2)

        return {
            "purchase_price_inr": price,
            "stamp_duty_inr": stamp_duty,
            "stamp_duty_pct": stamp_duty_pct,
            "registration_charges_inr": registration,
            "registration_rate_pct": registration_pct,
            "brokerage_inr": brokerage,
            "brokerage_rate_pct": brokerage_pct,
            "renovation_expenses_inr": renovation,
            "other_acquisition_costs_inr": other_costs,
            "total_closing_costs_inr": total_closing_costs,
            "total_acquisition_cost_inr": total_acquisition_cost,
        }

    @staticmethod
    def calculate_loan_emi(inputs: LoanInputs) -> Dict[str, Any]:
        """
        Calculate home loan monthly installment (EMI) using the reducing-balance method.
        Handles zero-interest and 100% cash payments safely.
        """
        price = max(0.0, inputs.purchase_price_inr)
        down_payment_pct = min(100.0, max(0.0, inputs.down_payment_pct))
        down_payment_inr = round(price * (down_payment_pct / 100.0), 2)
        loan_principal = round(max(0.0, price - down_payment_inr), 2)

        tenure_years = max(1, inputs.tenure_years)
        total_installments = tenure_years * 12
        annual_rate = max(0.0, inputs.annual_interest_rate_pct)

        # Cash purchase scenario (no loan)
        if loan_principal <= 0:
            return {
                "purchase_price_inr": price,
                "down_payment_pct": down_payment_pct,
                "down_payment_inr": down_payment_inr,
                "loan_principal_inr": 0.0,
                "annual_interest_rate_pct": annual_rate,
                "monthly_interest_rate": 0.0,
                "tenure_years": tenure_years,
                "total_installments": total_installments,
                "monthly_emi_inr": 0.0,
                "total_interest_payable_inr": 0.0,
                "total_repayment_amount_inr": 0.0,
                "is_zero_interest": False,
                "is_cash_purchase": True,
            }

        # Zero-interest scenario
        if annual_rate == 0.0:
            monthly_emi = round(loan_principal / total_installments, 2)
            return {
                "purchase_price_inr": price,
                "down_payment_pct": down_payment_pct,
                "down_payment_inr": down_payment_inr,
                "loan_principal_inr": loan_principal,
                "annual_interest_rate_pct": 0.0,
                "monthly_interest_rate": 0.0,
                "tenure_years": tenure_years,
                "total_installments": total_installments,
                "monthly_emi_inr": monthly_emi,
                "total_interest_payable_inr": 0.0,
                "total_repayment_amount_inr": loan_principal,
                "is_zero_interest": True,
                "is_cash_purchase": False,
            }

        # Reducing balance amortization
        monthly_rate = (annual_rate / 12.0) / 100.0
        # E = P * r * (1 + r)^n / ((1 + r)^n - 1)
        compound_factor = math.pow(1.0 + monthly_rate, total_installments)
        monthly_emi = round(loan_principal * monthly_rate * compound_factor / (compound_factor - 1.0), 2)
        total_repayment = round(monthly_emi * total_installments, 2)
        total_interest = round(max(0.0, total_repayment - loan_principal), 2)

        return {
            "purchase_price_inr": price,
            "down_payment_pct": down_payment_pct,
            "down_payment_inr": down_payment_inr,
            "loan_principal_inr": loan_principal,
            "annual_interest_rate_pct": annual_rate,
            "monthly_interest_rate": round(monthly_rate, 6),
            "tenure_years": tenure_years,
            "total_installments": total_installments,
            "monthly_emi_inr": monthly_emi,
            "total_interest_payable_inr": total_interest,
            "total_repayment_amount_inr": total_repayment,
            "is_zero_interest": False,
            "is_cash_purchase": False,
        }

    @staticmethod
    def calculate_operating_finances(inputs: OperatingExpenseInputs) -> Dict[str, Any]:
        """
        Calculate operating income and expenses including vacancy allowance,
        maintenance, and property management fees.
        """
        gross_rent = max(0.0, inputs.expected_monthly_rent_inr)
        annual_gross_rent = round(gross_rent * 12, 2)

        # Vacancy Allowance
        vacancy_pct = max(0.0, min(50.0, inputs.vacancy_rate_pct))
        vacancy_loss_monthly = round(gross_rent * (vacancy_pct / 100.0), 2)
        vacancy_loss_annual = round(vacancy_loss_monthly * 12, 2)
        effective_gross_monthly_rent = round(gross_rent - vacancy_loss_monthly, 2)

        # Operating Expenses
        maintenance_monthly = max(0.0, inputs.monthly_maintenance_inr)
        mgmt_pct = max(0.0, min(30.0, inputs.property_management_pct))
        mgmt_fee_monthly = round(gross_rent * (mgmt_pct / 100.0), 2)
        other_expenses_monthly = max(0.0, inputs.other_monthly_expenses_inr)

        total_monthly_operating_expenses = round(
            maintenance_monthly + mgmt_fee_monthly + other_expenses_monthly, 2
        )
        total_annual_operating_expenses = round(total_monthly_operating_expenses * 12, 2)

        # Net Operating Income (NOI)
        monthly_noi = round(effective_gross_monthly_rent - total_monthly_operating_expenses, 2)
        annual_noi = round(monthly_noi * 12, 2)

        return {
            "gross_monthly_rent_inr": gross_rent,
            "annual_gross_rent_inr": annual_gross_rent,
            "vacancy_rate_pct": vacancy_pct,
            "vacancy_loss_monthly_inr": vacancy_loss_monthly,
            "vacancy_loss_annual_inr": vacancy_loss_annual,
            "effective_gross_monthly_rent_inr": effective_gross_monthly_rent,
            "monthly_maintenance_inr": maintenance_monthly,
            "property_management_pct": mgmt_pct,
            "property_management_monthly_inr": mgmt_fee_monthly,
            "other_monthly_expenses_inr": other_expenses_monthly,
            "total_monthly_operating_expenses_inr": total_monthly_operating_expenses,
            "total_annual_operating_expenses_inr": total_annual_operating_expenses,
            "monthly_noi_inr": monthly_noi,
            "annual_noi_inr": annual_noi,
        }

    @staticmethod
    def calculate_investment_returns(
        purchase_price_inr: float,
        total_acquisition_cost_inr: float,
        down_payment_inr: float,
        total_closing_costs_inr: float,
        monthly_emi_inr: float,
        annual_gross_rent_inr: float,
        annual_noi_inr: float,
        annual_appreciation_rate_pct: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate Gross Rental Yield, Net Rental Yield, Monthly Cash Flow,
        Cash-on-Cash Return, and Break-Even timeline.
        """
        # A. Gross Rental Yield (%) = (Annual Gross Rent / Purchase Price) * 100
        gross_yield = (
            round((annual_gross_rent_inr / purchase_price_inr) * 100.0, 2)
            if purchase_price_inr > 0
            else 0.0
        )

        # B. Net Rental Yield (%) = (Annual NOI / Total Acquisition Cost) * 100
        net_yield = (
            round((annual_noi_inr / total_acquisition_cost_inr) * 100.0, 2)
            if total_acquisition_cost_inr > 0
            else 0.0
        )

        # C. Cash Flow
        annual_debt_service = round(monthly_emi_inr * 12, 2)
        annual_net_cash_flow = round(annual_noi_inr - annual_debt_service, 2)
        monthly_net_cash_flow = round(annual_net_cash_flow / 12, 2)

        # Total Initial Capital Outlay = Down Payment + Acquisition Closing Costs
        total_invested_capital = round(down_payment_inr + total_closing_costs_inr, 2)

        # F. Cash-on-Cash Return (%) = (Annual Net Cash Flow / Total Invested Capital) * 100
        cash_on_cash_roi_pct = (
            round((annual_net_cash_flow / total_invested_capital) * 100.0, 2)
            if total_invested_capital > 0
            else 0.0
        )

        # Appreciation-based Total ROI (only calculated if appreciation rate is supplied)
        appreciation_info: Dict[str, Any] = {
            "appreciation_considered": False,
            "annual_appreciation_rate_pct": 0.0,
            "annual_capital_appreciation_inr": 0.0,
            "total_annual_return_inr": annual_net_cash_flow,
            "total_roi_pct": cash_on_cash_roi_pct,
            "note": "Property appreciation is omitted unless explicitly provided by user.",
        }

        if annual_appreciation_rate_pct is not None and annual_appreciation_rate_pct > 0:
            annual_appreciation_inr = round(
                purchase_price_inr * (annual_appreciation_rate_pct / 100.0), 2
            )
            total_annual_return = round(annual_net_cash_flow + annual_appreciation_inr, 2)
            total_roi = (
                round((total_annual_return / total_invested_capital) * 100.0, 2)
                if total_invested_capital > 0
                else 0.0
            )
            appreciation_info = {
                "appreciation_considered": True,
                "annual_appreciation_rate_pct": annual_appreciation_rate_pct,
                "annual_capital_appreciation_inr": annual_appreciation_inr,
                "total_annual_return_inr": total_annual_return,
                "total_roi_pct": total_roi,
                "note": f"Includes user-specified annual appreciation rate of {annual_appreciation_rate_pct}%.",
            }

        # G. Break-even Analysis
        if annual_net_cash_flow > 0 and total_invested_capital > 0:
            break_even_years = round(total_invested_capital / annual_net_cash_flow, 2)
            break_even_months = round(break_even_years * 12, 1)
            break_even_status = "Achievable"
            break_even_text = f"{break_even_years} years (~{int(break_even_months)} months)"
        elif annual_net_cash_flow <= 0:
            break_even_years = None
            break_even_months = None
            break_even_status = "Indefinite"
            break_even_text = "Never / Indefinite (Negative or zero annual net cash flow)"
        else:
            break_even_years = 0.0
            break_even_months = 0.0
            break_even_status = "Immediate"
            break_even_text = "Immediate (Zero initial capital invested)"

        return {
            "gross_rental_yield_pct": gross_yield,
            "net_rental_yield_pct": net_yield,
            "monthly_net_cash_flow_inr": monthly_net_cash_flow,
            "annual_net_cash_flow_inr": annual_net_cash_flow,
            "total_invested_capital_inr": total_invested_capital,
            "cash_on_cash_roi_pct": cash_on_cash_roi_pct,
            "appreciation_metrics": appreciation_info,
            "break_even": {
                "status": break_even_status,
                "years": break_even_years,
                "months": break_even_months,
                "summary": break_even_text,
            },
        }

    @classmethod
    def calculate_sensitivity_scenarios(
        cls,
        purchase_price_inr: float,
        expected_monthly_rent_inr: float,
        monthly_maintenance_inr: float,
        total_acquisition_cost_inr: float,
        down_payment_inr: float,
        total_closing_costs_inr: float,
        base_down_payment_pct: float = 20.0,
        base_interest_rate_pct: float = 8.5,
        base_tenure_years: int = 20,
        base_vacancy_rate_pct: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Generate deterministic scenario testing (Sensitivity Analysis):
        - Base Case: current parameters
        - Best Case (Optimistic): rent +10%, vacancy -2% (min 1%), interest -0.5% (min 0%)
        - Conservative Case (Pessimistic): rent -10%, vacancy +5%, interest +1.0%, maintenance +15%
        """
        scenarios_def = [
            {
                "id": "conservative",
                "name": "Conservative / Downturn",
                "rent_multiplier": 0.90,
                "vacancy_pct": min(30.0, base_vacancy_rate_pct + 5.0),
                "interest_rate_pct": base_interest_rate_pct + 1.0,
                "maintenance_multiplier": 1.15,
                "badge": "Stress Test",
            },
            {
                "id": "base",
                "name": "Base Case (Current)",
                "rent_multiplier": 1.0,
                "vacancy_pct": base_vacancy_rate_pct,
                "interest_rate_pct": base_interest_rate_pct,
                "maintenance_multiplier": 1.0,
                "badge": "Expected",
            },
            {
                "id": "optimistic",
                "name": "Best Case (High Demand)",
                "rent_multiplier": 1.10,
                "vacancy_pct": max(1.0, base_vacancy_rate_pct - 2.0),
                "interest_rate_pct": max(0.0, base_interest_rate_pct - 0.5),
                "maintenance_multiplier": 1.0,
                "badge": "Bull Market",
            },
        ]

        results = {}
        for sc in scenarios_def:
            sc_rent = round(expected_monthly_rent_inr * sc["rent_multiplier"], 2)
            sc_maint = round(monthly_maintenance_inr * sc["maintenance_multiplier"], 2)
            sc_loan = cls.calculate_loan_emi(
                LoanInputs(
                    purchase_price_inr=purchase_price_inr,
                    down_payment_pct=base_down_payment_pct,
                    annual_interest_rate_pct=sc["interest_rate_pct"],
                    tenure_years=base_tenure_years,
                )
            )
            sc_op = cls.calculate_operating_finances(
                OperatingExpenseInputs(
                    expected_monthly_rent_inr=sc_rent,
                    monthly_maintenance_inr=sc_maint,
                    vacancy_rate_pct=sc["vacancy_pct"],
                )
            )
            sc_returns = cls.calculate_investment_returns(
                purchase_price_inr=purchase_price_inr,
                total_acquisition_cost_inr=total_acquisition_cost_inr,
                down_payment_inr=down_payment_inr,
                total_closing_costs_inr=total_closing_costs_inr,
                monthly_emi_inr=sc_loan["monthly_emi_inr"],
                annual_gross_rent_inr=sc_op["annual_gross_rent_inr"],
                annual_noi_inr=sc_op["annual_noi_inr"],
            )

            results[sc["id"]] = {
                "scenario_name": sc["name"],
                "badge": sc["badge"],
                "monthly_rent_inr": sc_rent,
                "vacancy_rate_pct": sc["vacancy_pct"],
                "interest_rate_pct": sc["interest_rate_pct"],
                "monthly_emi_inr": sc_loan["monthly_emi_inr"],
                "monthly_noi_inr": sc_op["monthly_noi_inr"],
                "monthly_net_cash_flow_inr": sc_returns["monthly_net_cash_flow_inr"],
                "gross_rental_yield_pct": sc_returns["gross_rental_yield_pct"],
                "net_rental_yield_pct": sc_returns["net_rental_yield_pct"],
                "cash_on_cash_roi_pct": sc_returns["cash_on_cash_roi_pct"],
                "break_even": sc_returns["break_even"],
            }

        return results


financial_engine = FinancialEngine()
