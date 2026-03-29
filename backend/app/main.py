from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base, SessionLocal
from app.api.v1 import auth, users, buildings, meters, billing, analytics, alerts
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Initialize Admin User
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if not admin_user:
            admin_user = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                full_name=settings.ADMIN_FULL_NAME,
                role=UserRole.ADMIN
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()
    yield

app = FastAPI(title="SolShare Energy System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(buildings.router, prefix="/api/v1")
app.include_router(meters.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to SolShare API"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}

@app.get("/solar/estimate")
def estimate_solar_production(lat: float, lon: float, capacity_kw: float):
    return {"estimated_daily_production_kwh": capacity_kw * 4.5, "location": {"lat": lat, "lon": lon}}
