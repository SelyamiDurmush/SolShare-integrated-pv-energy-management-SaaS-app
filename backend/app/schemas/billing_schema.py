from pydantic import BaseModel
from typing import List, Optional

class BillingStatement(BaseModel):
    apartment_unit: str
    resident: str
    period: str
    consumption_kwh: float
    solar_contribution_kwh: float
    residual_grid_kwh: float
    total_cost_eur: float
    savings_eur: float

class BillingResponse(BaseModel):
    building_address: str
    generated_at: str
    statements: List[BillingStatement]
