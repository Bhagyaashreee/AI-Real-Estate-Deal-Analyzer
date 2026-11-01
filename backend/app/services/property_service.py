import math
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from app.models.property import Property
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse
from app.utils.financial import (
    format_inr,
    calculate_gross_rental_yield,
    calculate_net_rental_yield,
    calculate_monthly_cash_flow,
)


def compute_metrics(
    purchase_price_inr: float,
    built_up_area_sqft: float,
    expected_monthly_rent_inr: float,
    monthly_maintenance_inr: float,
) -> Dict[str, Any]:
    """Compute financial yield and initial valuation metrics for a property."""
    price_per_sqft = round(purchase_price_inr / built_up_area_sqft, 2) if built_up_area_sqft > 0 else 0.0
    annual_rent = expected_monthly_rent_inr * 12
    annual_maintenance = monthly_maintenance_inr * 12

    gross_yield = calculate_gross_rental_yield(annual_rent, purchase_price_inr)
    net_yield = calculate_net_rental_yield(annual_rent, annual_maintenance, purchase_price_inr)
    cash_flow = calculate_monthly_cash_flow(expected_monthly_rent_inr, 0.0, monthly_maintenance_inr)

    # Valuation & Risk Scoring Benchmark (India National Avg ~3.25% gross yield)
    if gross_yield >= 4.5:
        valuation_status = "Undervalued"
        risk_level = "Low"
        ai_score = min(98, int(85 + (gross_yield - 4.5) * 6))
    elif gross_yield >= 3.25:
        valuation_status = "Fair Value"
        risk_level = "Moderate"
        ai_score = int(70 + (gross_yield - 3.25) * 11)
    else:
        valuation_status = "Overpriced"
        risk_level = "High" if gross_yield < 2.5 else "Moderate"
        ai_score = max(40, int(50 + (gross_yield / 3.25) * 19))

    return {
        "price_per_sqft": price_per_sqft,
        "gross_rental_yield_pct": gross_yield,
        "net_rental_yield_pct": net_yield,
        "estimated_monthly_cash_flow_inr": cash_flow,
        "ai_investment_score": ai_score,
        "risk_level": risk_level,
        "valuation_status": valuation_status,
    }


def to_response_dto(prop: Property) -> PropertyResponse:
    """Transform SQLAlchemy model into a rich PropertyResponse DTO."""
    metrics = compute_metrics(
        purchase_price_inr=prop.purchase_price_inr,
        built_up_area_sqft=prop.built_up_area_sqft,
        expected_monthly_rent_inr=prop.expected_monthly_rent_inr,
        monthly_maintenance_inr=prop.monthly_maintenance_inr,
    )
    
    return PropertyResponse(
        id=prop.id,
        title=prop.title,
        city=prop.city,
        locality=prop.locality,
        state=prop.state,
        property_type=prop.property_type,
        bedrooms=prop.bedrooms,
        bathrooms=prop.bathrooms,
        built_up_area_sqft=prop.built_up_area_sqft,
        purchase_price_inr=prop.purchase_price_inr,
        expected_monthly_rent_inr=prop.expected_monthly_rent_inr,
        monthly_maintenance_inr=prop.monthly_maintenance_inr,
        property_age=prop.property_age,
        listing_source=prop.listing_source,
        source_url=prop.source_url,
        listing_date=prop.listing_date,
        is_demo=prop.is_demo,
        price_per_sqft=prop.price_per_sqft or metrics["price_per_sqft"],
        gross_rental_yield_pct=prop.gross_rental_yield_pct if prop.gross_rental_yield_pct is not None else metrics["gross_rental_yield_pct"],
        net_rental_yield_pct=prop.net_rental_yield_pct if prop.net_rental_yield_pct is not None else metrics["net_rental_yield_pct"],
        estimated_monthly_cash_flow_inr=prop.estimated_monthly_cash_flow_inr if prop.estimated_monthly_cash_flow_inr is not None else metrics["estimated_monthly_cash_flow_inr"],
        ai_investment_score=prop.ai_investment_score if prop.ai_investment_score is not None else metrics["ai_investment_score"],
        risk_level=prop.risk_level or metrics["risk_level"],
        valuation_status=prop.valuation_status or metrics["valuation_status"],
        ai_summary=prop.ai_summary,
        price_formatted=format_inr(prop.purchase_price_inr),
        rent_formatted=f"{format_inr(prop.expected_monthly_rent_inr)}/mo",
        created_at=prop.created_at,
        updated_at=prop.updated_at,
        # Backward compatibility aliases
        bhk=prop.bedrooms,
        area_sqft=prop.built_up_area_sqft,
        price_inr=prop.purchase_price_inr,
        monthly_cash_flow_inr=prop.estimated_monthly_cash_flow_inr if prop.estimated_monthly_cash_flow_inr is not None else metrics["estimated_monthly_cash_flow_inr"],
        estimated_monthly_rent_inr=prop.expected_monthly_rent_inr,
    )


class PropertyService:
    @staticmethod
    def create_property(db: Session, data: PropertyCreate) -> Property:
        metrics = compute_metrics(
            purchase_price_inr=data.purchase_price_inr,
            built_up_area_sqft=data.built_up_area_sqft,
            expected_monthly_rent_inr=data.expected_monthly_rent_inr,
            monthly_maintenance_inr=data.monthly_maintenance_inr,
        )

        db_prop = Property(
            title=data.title,
            city=data.city,
            locality=data.locality,
            state=data.state,
            property_type=data.property_type,
            bedrooms=data.bedrooms,
            bathrooms=data.bathrooms,
            built_up_area_sqft=data.built_up_area_sqft,
            purchase_price_inr=data.purchase_price_inr,
            expected_monthly_rent_inr=data.expected_monthly_rent_inr,
            monthly_maintenance_inr=data.monthly_maintenance_inr,
            property_age=data.property_age,
            listing_source=data.listing_source or "Direct Listing",
            source_url=data.source_url,
            listing_date=data.listing_date,
            is_demo=data.is_demo,
            price_per_sqft=metrics["price_per_sqft"],
            gross_rental_yield_pct=metrics["gross_rental_yield_pct"],
            net_rental_yield_pct=metrics["net_rental_yield_pct"],
            estimated_monthly_cash_flow_inr=metrics["estimated_monthly_cash_flow_inr"],
            ai_investment_score=metrics["ai_investment_score"],
            risk_level=metrics["risk_level"],
            valuation_status=metrics["valuation_status"],
        )
        db.add(db_prop)
        db.commit()
        db.refresh(db_prop)
        return db_prop

    @staticmethod
    def get_property(db: Session, property_id: int) -> Optional[Property]:
        return db.query(Property).filter(Property.id == property_id).first()

    @staticmethod
    def update_property(db: Session, property_id: int, data: PropertyUpdate) -> Optional[Property]:
        db_prop = db.query(Property).filter(Property.id == property_id).first()
        if not db_prop:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_prop, key, value)

        # Recalculate metrics if financial inputs changed
        metrics = compute_metrics(
            purchase_price_inr=db_prop.purchase_price_inr,
            built_up_area_sqft=db_prop.built_up_area_sqft,
            expected_monthly_rent_inr=db_prop.expected_monthly_rent_inr,
            monthly_maintenance_inr=db_prop.monthly_maintenance_inr,
        )
        for m_key, m_val in metrics.items():
            setattr(db_prop, m_key, m_val)

        db.commit()
        db.refresh(db_prop)
        return db_prop

    @staticmethod
    def delete_property(db: Session, property_id: int) -> bool:
        db_prop = db.query(Property).filter(Property.id == property_id).first()
        if not db_prop:
            return False
        db.delete(db_prop)
        db.commit()
        return True

    @staticmethod
    def search_properties(
        db: Session,
        city: Optional[str] = None,
        locality: Optional[str] = None,
        state: Optional[str] = None,
        property_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_bedrooms: Optional[int] = None,
        max_bedrooms: Optional[int] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
        min_yield: Optional[float] = None,
        valuation_status: Optional[str] = None,
        is_demo: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 12,
    ) -> Tuple[List[Property], int, int]:
        """Search and filter properties with pagination and sorting."""
        query = db.query(Property)

        if is_demo is not None:
            query = query.filter(Property.is_demo == is_demo)

        if city and city.lower() != "all cities":
            query = query.filter(Property.city.ilike(f"%{city.strip()}%"))

        if locality:
            query = query.filter(Property.locality.ilike(f"%{locality.strip()}%"))

        if state:
            query = query.filter(Property.state.ilike(f"%{state.strip()}%"))

        if property_type and property_type.lower() != "all":
            query = query.filter(Property.property_type.ilike(f"%{property_type.strip()}%"))

        if min_price is not None:
            query = query.filter(Property.purchase_price_inr >= min_price)

        if max_price is not None:
            query = query.filter(Property.purchase_price_inr <= max_price)

        if min_bedrooms is not None:
            query = query.filter(Property.bedrooms >= min_bedrooms)

        if max_bedrooms is not None:
            query = query.filter(Property.bedrooms <= max_bedrooms)

        if min_area is not None:
            query = query.filter(Property.built_up_area_sqft >= min_area)

        if max_area is not None:
            query = query.filter(Property.built_up_area_sqft <= max_area)

        if min_yield is not None:
            query = query.filter(Property.gross_rental_yield_pct >= min_yield)

        if valuation_status and valuation_status.lower() != "all":
            query = query.filter(Property.valuation_status.ilike(valuation_status.strip()))

        total = query.count()

        # Sorting
        sort_map = {
            "created_at": Property.created_at,
            "price_inr": Property.purchase_price_inr,
            "purchase_price_inr": Property.purchase_price_inr,
            "expected_monthly_rent_inr": Property.expected_monthly_rent_inr,
            "gross_rental_yield_pct": Property.gross_rental_yield_pct,
            "built_up_area_sqft": Property.built_up_area_sqft,
            "bedrooms": Property.bedrooms,
            "ai_investment_score": Property.ai_investment_score,
        }

        sort_col = sort_map.get(sort_by.lower(), Property.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        # Pagination
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        total_pages = max(1, math.ceil(total / page_size))
        offset = (page - 1) * page_size

        items = query.offset(offset).limit(page_size).all()
        return items, total, total_pages


property_service = PropertyService()

