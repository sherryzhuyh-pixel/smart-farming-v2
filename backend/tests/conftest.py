"""pytest fixtures and test configuration (Feishu Base mock version)"""
import os
import asyncio
from datetime import date

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("ADMIN_PASSWORD_HASH", "")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth import create_access_token
from app.repositories import get_repositories


class MockRecord(dict):
    """模拟飞书 Base 返回的记录，支持 .id 等属性访问"""
    def __getattr__(self, name):
        if name == "id":
            return self.get("_record_id")
        return self.get(name)


class InMemoryRepo:
    """内存中的 Repository，模拟 BaseRepository 行为（async 版本）"""
    def __init__(self):
        self._records = []
        self._counter = 0

    def _new_id(self):
        self._counter += 1
        return f"rec_{self._counter}"

    async def create(self, data: dict) -> MockRecord:
        record = MockRecord(data)
        record["_record_id"] = self._new_id()
        self._records.append(record)
        return record

    async def get_by_id(self, record_id: str):
        for r in self._records:
            if r.get("_record_id") == record_id:
                return r
        return None

    async def get_by_field(self, field: str, value):
        for r in self._records:
            if r.get(field) == value:
                return r
        return None

    async def get_by_pk(self, pk_value):
        for r in self._records:
            if r.get("batch_no") == pk_value or r.get("username") == pk_value:
                return r
        return None

    async def update(self, record_id: str, data: dict):
        for r in self._records:
            if r.get("_record_id") == record_id:
                r.update(data)
                return r
        return None

    async def update_by_pk(self, pk_value, data: dict):
        r = await self.get_by_pk(pk_value)
        if r:
            r.update(data)
            return r
        return None

    async def delete(self, record_id: str):
        self._records = [r for r in self._records if r.get("_record_id") != record_id]

    async def list_all(self, limit=None):
        return self._records[:limit] if limit else list(self._records)

    async def filter_by(self, field: str, value, limit=None):
        result = [r for r in self._records if str(r.get(field)) == str(value)]
        return result[:limit] if limit else result

    async def count(self, filter_expr=None):
        return len(self._records)

    async def batch_create(self, data_list):
        created = []
        for d in data_list:
            created.append(await self.create(d))
        return created


class MockRepositoryFactory:
    """模拟 RepositoryFactory，所有表使用内存存储"""
    def __init__(self):
        self.breed = InMemoryRepo()
        self.house = InMemoryRepo()
        self.batch = InMemoryRepo()
        self.animal = InMemoryRepo()
        self.growth = InMemoryRepo()
        self.health = InMemoryRepo()
        self.operation = InMemoryRepo()
        self.env_param = InMemoryRepo()
        self.alert = InMemoryRepo()
        self.feed = InMemoryRepo()
        self.purchase = InMemoryRepo()
        self.purchase_item = InMemoryRepo()
        self.inventory = InMemoryRepo()
        self.inv_trans = InMemoryRepo()
        self.hatching = InMemoryRepo()
        self.sales = InMemoryRepo()
        self.sales_item = InMemoryRepo()
        self.culling = InMemoryRepo()
        self.benchmark = InMemoryRepo()
        self.performance = InMemoryRepo()
        self.traceability = InMemoryRepo()
        self.pilot_project = InMemoryRepo()
        self.pilot_batch = InMemoryRepo()
        self.pilot_indicator = InMemoryRepo()
        self.market = InMemoryRepo()
        self.sys_config = InMemoryRepo()
        self.sys_config_history = InMemoryRepo()
        self.financial = InMemoryRepo()
        self.cost = InMemoryRepo()
        self.profit = InMemoryRepo()
        self.users = InMemoryRepo()

    async def close(self):
        pass


def override_get_repositories():
    if not hasattr(override_get_repositories, "factory"):
        override_get_repositories.factory = MockRepositoryFactory()
    return override_get_repositories.factory


app.dependency_overrides[get_repositories] = override_get_repositories


@pytest.fixture(scope="function")
def mock_repos():
    """每个测试函数开始前重置内存存储"""
    factory = MockRepositoryFactory()
    override_get_repositories.factory = factory
    return factory


@pytest.fixture(scope="function")
def test_token():
    """Generate a valid test JWT token"""
    token = create_access_token(data={"sub": "1", "username": "testuser", "role": "admin"})
    return token


@pytest.fixture(scope="function")
def client(mock_repos, test_token):
    """TestClient with mocked repositories and auth header"""
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {test_token}"})
        yield c


@pytest.fixture(scope="function")
def unauth_client(mock_repos):
    """Client without auth header"""
    with TestClient(app) as c:
        yield c


# Helper to call async repo methods from sync fixtures
_loop = asyncio.new_event_loop()


def _sync(coro):
    """在同步上下文中运行异步协程"""
    return _loop.run_until_complete(coro)


@pytest.fixture
def seed_breed(mock_repos):
    """Seed a breed record"""
    return _sync(mock_repos.breed.create({
        "breed_code": "AA",
        "breed_name": "爱拔益加",
        "breed_type": 1,
        "survival_rate_std": 95.0,
        "daily_gain_std": 65.0,
        "feed_meat_ratio": 1.75,
    }))


@pytest.fixture
def seed_house(mock_repos):
    """Seed a house record"""
    return _sync(mock_repos.house.create({
        "house_code": "H001",
        "house_name": "1号鸡舍",
        "house_type": 1,
        "capacity": 20000,
        "status": 1,
    }))


@pytest.fixture
def seed_batch(mock_repos, seed_breed, seed_house):
    """Seed a batch record"""
    return _sync(mock_repos.batch.create({
        "batch_no": "B20240921001",
        "batch_name": "20240921-AA-001",
        "breed_id": seed_breed.id,
        "house_id": seed_house.id,
        "quantity_initial": 10000,
        "quantity_current": 9500,
        "date_in": str(date(2024, 9, 1)),
        "age_day_in": 1,
        "source_type": 1,
        "status": 1,
        "responsible_person": "张三",
        "pilot_flag": 0,
    }))


@pytest.fixture
def seed_inventory(mock_repos):
    """Seed inventory records"""
    items = []
    items.append(_sync(mock_repos.inventory.create({
        "item_code": "F001",
        "item_name": "雏鸡饲料A",
        "item_category": 1,
        "item_spec": "20kg/袋",
        "quantity": 500.0,
        "unit": "袋",
        "storage_location": "主仓库",
        "safety_stock": 50.0,
        "expiry_date": str(date(2025, 3, 1)),
        "status": 1,
    })))
    items.append(_sync(mock_repos.inventory.create({
        "item_code": "M001",
        "item_name": "疫苗B",
        "item_category": 2,
        "item_spec": "100ml/瓶",
        "quantity": 10.0,
        "unit": "瓶",
        "storage_location": "药品库",
        "safety_stock": 20.0,
        "expiry_date": str(date(2024, 12, 1)),
        "status": 1,
    })))
    return items


@pytest.fixture
def seed_user(mock_repos):
    """Seed an admin user for login tests"""
    from app.auth import get_password_hash
    return _sync(mock_repos.users.create({
        "username": "admin",
        "password_hash": get_password_hash("admin123"),
        "full_name": "Administrator",
        "role": "admin",
        "is_active": True,
    }))


@pytest.fixture
def seed_financial(mock_repos, seed_batch):
    """Seed financial transaction records"""
    txs = []
    txs.append(_sync(mock_repos.financial.create({
        "transaction_type": 1,
        "category": "销售款",
        "amount": 500000.0,
        "batch_id": seed_batch.id,
        "transaction_date": str(date(2024, 9, 15)),
        "payee_payer": "客户A",
        "remark": "批次销售",
    })))
    txs.append(_sync(mock_repos.financial.create({
        "transaction_type": 2,
        "category": "饲料费",
        "amount": 120000.0,
        "batch_id": seed_batch.id,
        "transaction_date": str(date(2024, 9, 10)),
        "payee_payer": "饲料供应商",
        "remark": "饲料采购",
    })))
    txs.append(_sync(mock_repos.financial.create({
        "transaction_type": 2,
        "category": "雏鸡苗",
        "amount": 80000.0,
        "batch_id": seed_batch.id,
        "transaction_date": str(date(2024, 9, 5)),
        "payee_payer": "种鸡场",
        "remark": "进苗费用",
    })))
    return txs
