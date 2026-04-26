from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models import Building, AllocationMethod, User, UserRole, Apartment
from app.models.energy import MeterReading, MeterType
from app.services.energy import EnergyService

class BillingService:
    @staticmethod
    def calculate_billing(building_id: int, month: int, year: int, db: Session):
        building = db.query(Building).filter(Building.id == building_id).first()
        if not building:
            return None

        total_solar_production = 1500.0  
        billing_results = []

        for apartment in building.apartments:
            total_consumption = 350.0 
            allocated_solar = 0.0
            solar_rate = 0.10 
            grid_rate = 0.35  
            
            if apartment.allocation_method == AllocationMethod.STATIC:
                share = (apartment.static_allocation_percentage or 0) / 100.0
                allocated_solar = total_solar_production * share
            else:
                total_building_consumption = 3500.0 
                share = total_consumption / total_building_consumption if total_building_consumption > 0 else 0
                allocated_solar = total_solar_production * share

            allocated_solar = min(allocated_solar, total_consumption)
            residual_grid = total_consumption - allocated_solar
            
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

    @staticmethod
    def get_user_statements(db: Session, user: User) -> list[dict]:
        query = db.query(Apartment).join(Building)

        if user.role == UserRole.PROPERTY_MANAGER:
            query = query.filter(Building.manager_id == user.id)
        elif user.role == UserRole.RESIDENT:
            query = query.filter(Apartment.resident_id == user.id)

        apartments = query.all()

        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        statements = []

        for apt in apartments:
            consumption = 0.0
            if apt.meter:
                specific = (
                    db.query(func.sum(MeterReading.value_kwh))
                    .filter(MeterReading.meter_id == apt.meter.id)
                    .filter(MeterReading.time >= thirty_days_ago)
                    .scalar()
                ) or 0.0
                consumption = round(specific, 2)

            total_pv = 0.0
            total_consumption_building = 0.0
            building = apt.building
            if building:
                total_pv = EnergyService.sum_readings(db, MeterType.PV_PRODUCTION, thirty_days_ago, now, building.id)
                total_consumption_building = EnergyService.sum_readings(db, MeterType.APARTMENT, thirty_days_ago, now, building.id)

            solar_share = 0.0
            if total_consumption_building > 0 and consumption > 0:
                fraction = consumption / total_consumption_building
                solar_share = round(min(fraction * total_pv, consumption), 2)

            residual_grid = max(0.0, consumption - solar_share)

            solar_rate = 0.10 
            grid_rate = 0.35  

            total_cost = (solar_share * solar_rate) + (residual_grid * grid_rate)

            h = hash(str(apt.id) + apt.unit_number) % 3
            status = "Paid" if h == 0 else "Sent" if h == 1 else "Generated"

            statements.append({
                "id": apt.id,
                "unit": apt.unit_number,
                "building_name": building.name or building.address if building else "—",
                "resident": apt.resident.full_name if apt.resident else "Unassigned",
                "consumption": consumption,
                "solar_output": solar_share,
                "residual": round(residual_grid, 2),
                "total_cost": round(total_cost, 2),
                "status": status
            })

        return statements
