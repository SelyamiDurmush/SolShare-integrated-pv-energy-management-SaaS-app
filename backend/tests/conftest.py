import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import timedelta

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole

# 🚀 Use an in-memory SQLite database for maximum test isolation and speed
# The StaticPool ensures that the same in-memory DB is used for the duration of the connection
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# .fixture is a function that returns a value that can be used by other tests
@pytest.fixture(scope="function")
def db():
    # Create the tables in the in-memory database
    Base.metadata.create_all(bind=engine) # creates all tables in the database
    session = TestingSessionLocal() # creates a new session for each test
    try:
        yield session
    finally:
        session.close()
        # Drop everything so the next test starts with a blank page
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    del app.dependency_overrides[get_db]

@pytest.fixture
def admin_user(db):
    user = User(
        email="admin@solshare.com",
        hashed_password=get_password_hash("admin1234"),
        full_name="System Administrator",
        role=UserRole.ADMIN
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def resident_user(db):
    user = User(
        email="resident1@solshare.com",
        hashed_password=get_password_hash("resident123"),
        full_name="Test Resident",
        role=UserRole.RESIDENT
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def admin_token(admin_user):
    return create_access_token(data={"sub": admin_user.email}, expires_delta=timedelta(minutes=30))

@pytest.fixture
def resident_token(resident_user):
    return create_access_token(data={"sub": resident_user.email}, expires_delta=timedelta(minutes=30))
