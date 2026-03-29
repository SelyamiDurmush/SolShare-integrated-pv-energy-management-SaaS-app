from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Building, AllocationMethod

def calculate_billing(building_id: int, month: int, year: int, db: Session):
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        return None

    total_solar_production = 1500.0  
    billing_results = []

    for apartment in building.apartments:
        total_consumption = 350.0 
        allocated_solar = 0.0
        
        if apartment.allocation_method == AllocationMethod.STATIC:
            share = (apartment.static_allocation_percentage or 0) / 100.0
            allocated_solar = total_solar_production * share
        else:
            total_building_consumption = 3500.0 
            share = total_consumption / total_building_consumption if total_building_consumption > 0 else 0
            allocated_solar = total_solar_production * share

        allocated_solar = min(allocated_solar, total_consumption)
        residual_grid = total_consumption - allocated_solar

        solar_rate = 0.10 
        grid_rate = 0.35  
        
        total_cost = (allocated_solar * solar_rate) + (residual_grid * grid_rate)

        billing_results.append({
            "apartment_unit": apartment.unit_number,
            "resident": apartment.resident.full_name if apartment.resident else "Vacant",
            "period": f"{month}/{year}",
            "consumption_kwh": total_consumption,
            "solar_contribution_kwh": round(allocated_solar, 2),
            "residual_grid_kwh": round(residual_grid, 2),
            "total_cost_eur": round(total_cost, 2),
            "savings_eur": round((total_consumption * grid_rate) - total_cost, 2)
        })

    return {
        "building_address": building.address,
        "generated_at": datetime.now().isoformat(),
        "statements": billing_results
    }
