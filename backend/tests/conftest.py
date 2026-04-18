import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import timedelta

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole
from app.core.config import settings

# Use a local test database file
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    # Begin a non-ORM transaction
    transaction = connection.begin()
    # Establish a session bound to the connection
    session = TestingSessionLocal(bind=connection)
    
    # 🌟 NEW: Create a savepoint for nested transactions
    nested = connection.begin_nested()

    @pytest.fixture
    def _db_session():
        yield session

    yield session
    
    session.close()
    # Roll back everything to ensure a clean slate for the next test
    transaction.rollback()
    connection.close()

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
    user = db.query(User).filter(User.email == "admin@solshare.com").first()
    if not user:
        user = User(
            email="admin@solshare.com",
            hashed_password=get_password_hash("admin1234"),
            full_name="Test Admin",
            role=UserRole.ADMIN
        )
        db.add(user)
        db.flush() # 🌟 Use flush instead of commit
    return user

@pytest.fixture
def resident_user(db):
    user = db.query(User).filter(User.email == "resident1@solshare.com").first()
    if not user:
        user = User(
            email="resident1@solshare.com",
            hashed_password=get_password_hash("resident123"),
            full_name="Test Resident",
            role=UserRole.RESIDENT
        )
        db.add(user)
        db.flush() # 🌟 Use flush instead of commit
    return user

@pytest.fixture
def admin_token(admin_user):
    return create_access_token(data={"sub": admin_user.email}, expires_delta=timedelta(minutes=30))

@pytest.fixture
def resident_token(resident_user):
    return create_access_token(data={"sub": resident_user.email}, expires_delta=timedelta(minutes=30))
