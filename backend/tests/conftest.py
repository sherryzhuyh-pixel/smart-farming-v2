"""pytest fixtures and test configuration"""
import os
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:3000")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.auth import create_access_token

# Use SQLite in-memory for fast tests (StaticPool ensures shared DB across connections)
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_token():
    """Generate a valid test JWT token"""
    token = create_access_token(data={"sub": "1", "username": "testuser", "role": "admin"})
    return token


@pytest.fixture(scope="function")
def client(db, test_token):
    """TestClient with overridden DB dependency and auth header"""
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {test_token}"})
        yield c


@pytest.fixture
def seed_breed(db):
    """Seed a breed record"""
    from app.models import Breed
    breed = Breed(
        breed_code="AA",
        breed_name="爱拔益加",
        breed_type=1,
        survival_rate_std=95.0,
        daily_gain_std=65.0,
        feed_meat_ratio=1.75,
    )
    db.add(breed)
    db.commit()
    db.refresh(breed)
    return breed


@pytest.fixture
def seed_house(db):
    """Seed a house record"""
    from app.models import House
    house = House(
        house_code="H001",
        house_name="1号鸡舍",
        house_type=1,
        capacity=20000,
        status=1,
    )
    db.add(house)
    db.commit()
    db.refresh(house)
    return house


@pytest.fixture
def seed_batch(db, seed_breed, seed_house):
    """Seed a batch record"""
    from app.models import Batch
    from datetime import date
    batch = Batch(
        batch_no="B20240921001",
        batch_name="20240921-AA-001",
        breed_id=seed_breed.id,
        house_id=seed_house.id,
        quantity_initial=10000,
        quantity_current=9500,
        date_in=date(2024, 9, 1),
        age_day_in=1,
        source_type=1,
        status=1,
        responsible_person="张三",
        pilot_flag=0,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


@pytest.fixture
def seed_inventory(db):
    """Seed inventory records"""
    from app.models import Inventory
    from datetime import date
    items = [
        Inventory(
            item_code="F001",
            item_name="雏鸡饲料A",
            item_category=1,
            item_spec="20kg/袋",
            quantity=500.0,
            unit="袋",
            storage_location="主仓库",
            safety_stock=50.0,
            expiry_date=date(2025, 3, 1),
            status=1,
        ),
        Inventory(
            item_code="M001",
            item_name="疫苗B",
            item_category=2,
            item_spec="100ml/瓶",
            quantity=10.0,
            unit="瓶",
            storage_location="药品库",
            safety_stock=20.0,
            expiry_date=date(2024, 12, 1),
            status=1,
        ),
    ]
    db.add_all(items)
    db.commit()
    for item in items:
        db.refresh(item)
    return items


@pytest.fixture
def seed_financial(db, seed_batch):
    """Seed financial transaction records"""
    from app.models import FinancialTransaction
    from datetime import date
    txs = [
        FinancialTransaction(
            transaction_type=1,
            category="销售款",
            amount=500000.0,
            batch_id=seed_batch.id,
            transaction_date=date(2024, 9, 15),
            payee_payer="客户A",
            remark="批次销售",
        ),
        FinancialTransaction(
            transaction_type=2,
            category="饲料费",
            amount=120000.0,
            batch_id=seed_batch.id,
            transaction_date=date(2024, 9, 10),
            payee_payer="饲料供应商",
            remark="饲料采购",
        ),
        FinancialTransaction(
            transaction_type=2,
            category="雏鸡苗",
            amount=80000.0,
            batch_id=seed_batch.id,
            transaction_date=date(2024, 9, 5),
            payee_payer="种鸡场",
            remark="进苗费用",
        ),
    ]
    db.add_all(txs)
    db.commit()
    return txs
