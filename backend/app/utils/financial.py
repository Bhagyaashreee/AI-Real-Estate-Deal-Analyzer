from typing import Optional


def format_inr(amount: Optional[float], show_symbol: bool = True) -> str:
    """
    Format a number into Indian Rupee denomination:
    - Below 1 Lakh: standard Indian comma notation (e.g. ₹75,000)
    - 1 Lakh to 99 Lakhs: Lakhs notation (e.g. ₹45.5 Lakhs)
    - 1 Crore and above: Crores notation (e.g. ₹1.25 Cr)
    """
    if amount is None:
        return "₹0" if show_symbol else "0"

    symbol = "₹" if show_symbol else ""

    if abs(amount) >= 10_000_000:
        cr_val = amount / 10_000_000
        return f"{symbol}{cr_val:.2f} Cr"
    elif abs(amount) >= 100_000:
        lakh_val = amount / 100_000
        return f"{symbol}{lakh_val:.2f} L"
    else:
        # Standard Indian comma format
        s = f"{int(amount)}"
        if len(s) <= 3:
            res = s
        else:
            last3 = s[-3:]
            other = s[:-3]
            res = ""
            while len(other) > 2:
                res = "," + other[-2:] + res
                other = other[:-2]
            res = other + res + "," + last3
        return f"{symbol}{res}"


def calculate_gross_rental_yield(annual_rent: float, purchase_price: float) -> float:
    """Calculate Gross Rental Yield percentage."""
    if purchase_price <= 0:
        return 0.0
    return round((annual_rent / purchase_price) * 100, 2)


def calculate_net_rental_yield(
    annual_rent: float,
    annual_maintenance: float,
    purchase_price: float,
    annual_property_tax: float = 0.0,
) -> float:
    """Calculate Net Rental Yield percentage after deductions."""
    if purchase_price <= 0:
        return 0.0
    net_annual_income = annual_rent - annual_maintenance - annual_property_tax
    return round((max(0.0, net_annual_income) / purchase_price) * 100, 2)


def calculate_monthly_cash_flow(
    monthly_rent: float,
    monthly_emi: float,
    monthly_maintenance: float,
) -> float:
    """Calculate Net Monthly Cash Flow in INR."""
    return round(monthly_rent - (monthly_emi + monthly_maintenance), 2)

