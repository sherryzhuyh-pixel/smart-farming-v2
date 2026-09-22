"""Security regression tests for P0 and P1 fixes"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth import create_access_token, verify_token
from app.config import Settings, get_settings
from app.utils.privacy import mask_phone, mask_id_card, desensitize_dict


@pytest.fixture(scope="function")
def test_token():
    return create_access_token(data={"sub": "1", "username": "testuser", "role": "admin"})


@pytest.fixture(scope="function")
def client(mock_repos, test_token):
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {test_token}"})
        yield c


@pytest.fixture(scope="function")
def unauth_client(mock_repos):
    """Client without auth header"""
    with TestClient(app) as c:
        yield c


# =============================================================================
# P0-B1: CORS whitelist (verified via settings, not HTTP client)
# =============================================================================
class TestCORSWhitelist:
    def test_cors_origins_not_wildcard(self):
        """CORS配置不应包含通配符*"""
        settings = Settings(CORS_ALLOWED_ORIGINS="https://example.com,https://app.example.com")
        assert "*" not in settings.CORS_ORIGINS_LIST
        assert len(settings.CORS_ORIGINS_LIST) > 0

    def test_cors_origins_from_env(self):
        """CORS origins应从环境变量读取"""
        settings = Settings(CORS_ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173")
        assert "http://localhost:3000" in settings.CORS_ORIGINS_LIST
        assert "http://localhost:5173" in settings.CORS_ORIGINS_LIST


# =============================================================================
# P0-B2: Exception handler does NOT leak stack traces
# =============================================================================
class TestExceptionHandler:
    def test_exception_no_detail_leak(self, client):
        """全局异常处理器不应向客户端泄露异常详情"""
        from app.main import global_exception_handler
        from fastapi import Request
        import asyncio

        class FakeRequest:
            method = "GET"
            url = type("URL", (), {"path": "/test"})()

        exc = ValueError("Internal secret: /etc/passwd")
        response = asyncio.get_event_loop().run_until_complete(
            global_exception_handler(FakeRequest(), exc)
        )
        body = response.body.decode()
        assert "Internal secret" not in body
        assert "detail" not in body or "服务器内部错误" in body


# =============================================================================
# P0-B3: Authentication required for protected endpoints
# =============================================================================
class TestAuthentication:
    def test_protected_endpoint_without_token(self, unauth_client):
        """不带Token访问受保护端点应返回401"""
        resp = unauth_client.get("/api/v2/batches")
        assert resp.status_code == 401

    def test_protected_endpoint_with_valid_token(self, client):
        """带有效Token应正常访问"""
        resp = client.get("/api/v2/batches")
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

    def test_public_health_endpoint_no_auth(self, unauth_client):
        """公开端点/health不需要认证"""
        resp = unauth_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_public_root_endpoint_no_auth(self, unauth_client):
        """公开端点/不需要认证"""
        resp = unauth_client.get("/")
        assert resp.status_code == 200

    def test_login_endpoint_no_auth(self, unauth_client, seed_user):
        """登录端点不需要认证"""
        resp = unauth_client.post("/api/v2/auth/login", json={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "access_token" in data["data"]

    def test_invalid_token_rejected(self, unauth_client):
        """无效Token应被拒绝"""
        unauth_client.headers.update({"Authorization": "Bearer invalid-token"})
        resp = unauth_client.get("/api/v2/batches")
        assert resp.status_code == 401

    def test_token_verify(self, test_token):
        """Token验证应返回有效payload"""
        payload = verify_token(test_token)
        assert payload is not None
        assert payload.get("sub") == "1"
        assert payload.get("username") == "testuser"

    def test_expired_token_rejected(self):
        """过期Token应被拒绝"""
        from datetime import timedelta
        expired_token = create_access_token(
            data={"sub": "1"},
            expires_delta=timedelta(seconds=-1),
        )
        payload = verify_token(expired_token)
        assert payload is None


# =============================================================================
# P0-B4: Feishu credentials validation (replaces DB_PASSWORD after SQLAlchemy removal)
# =============================================================================
class TestFeishuCredentials:
    def test_lark_app_id_empty_by_default(self):
        """LARK_APP_ID 默认为空字符串"""
        settings = Settings()
        assert settings.LARK_APP_ID == ""

    def test_lark_app_secret_empty_by_default(self):
        """LARK_APP_SECRET 默认为空字符串"""
        settings = Settings()
        assert settings.LARK_APP_SECRET == ""


# =============================================================================
# P1-B5: Data desensitization
# =============================================================================
class TestDesensitization:
    def test_mask_phone(self):
        """手机号脱敏"""
        assert mask_phone("13812345678") == "138****5678"
        assert mask_phone("") == ""
        assert mask_phone(None) is None

    def test_mask_id_card(self):
        """身份证号脱敏"""
        assert mask_id_card("110101199001011234") == "110101********1234"
        assert mask_id_card("") == ""

    def test_desensitize_dict(self):
        """字典脱敏"""
        data = {"name": "张三", "phone": "13812345678", "customer_phone": "13987654321"}
        result = desensitize_dict(data)
        assert result["phone"] == "138****5678"
        assert result["customer_phone"] == "139****4321"
        assert result["name"] == "张三"  # name not in default masks


# =============================================================================
# P1-B6: Inventory concurrency lock
# =============================================================================
class TestInventoryConcurrency:
    def test_inventory_transaction_updates_balance(self, client, seed_inventory):
        """库存出入库应正确更新余额"""
        inv_id = seed_inventory[0].id
        resp = client.post(f"/api/v2/inventory/{inv_id}/transactions", json={
            "transaction_type": "out",
            "quantity": 10.0,
            "reason": "领用",
            "operator": "李四",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        # 原数量500 - 10 = 490
        assert data["balance"] == 490.0

    def test_inventory_transaction_insufficient_stock(self, client, seed_inventory):
        """库存不足时应拒绝出库"""
        inv_id = seed_inventory[0].id
        resp = client.post(f"/api/v2/inventory/{inv_id}/transactions", json={
            "transaction_type": "out",
            "quantity": 1000.0,
            "reason": "领用",
        })
        assert resp.status_code == 200
        assert resp.json()["code"] != 0
        assert "库存不足" in resp.json()["message"]

    def test_inventory_transaction_no_sqlalchemy_locks(self):
        """库存流水不应再使用 SQLAlchemy 悲观锁（已迁移至 Feishu Base）"""
        import inspect
        from app.routers import inventory as inv_module
        source = inspect.getsource(inv_module.create_transaction)
        assert "with_for_update" not in source, "Inventory transaction must not use SQLAlchemy locks"


# =============================================================================
# P1-B7: Traceability N+1 fix
# =============================================================================
class TestTraceabilityN1Fix:
    def test_completeness_no_sqlalchemy_in_query(self):
        """溯源完整度不应再使用 SQLAlchemy IN 查询（已迁移至 Feishu Base）"""
        import inspect
        from app.routers import traceability as trace_module
        source = inspect.getsource(trace_module.get_traceability_completeness)
        assert ".in_(" not in source, "Traceability completeness must not use SQLAlchemy IN query"

    def test_completeness_no_batch_id_returns_summary(self, client):
        """不传batch_id时应返回汇总"""
        resp = client.get("/api/v2/traceability/completeness")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "summary" in data


# =============================================================================
# P1-B8: Pagination limits
# =============================================================================
class TestPaginationLimits:
    def test_inventory_alerts_has_pagination(self):
        """库存预警查询应支持分页"""
        import inspect
        from app.routers import inventory as inv_module
        source = inspect.getsource(inv_module.get_inventory_alerts)
        assert "page_size" in source
        assert "page" in source

    def test_page_size_max_100(self, client):
        """page_size超过100应被拒绝"""
        resp = client.get("/api/v2/batches?page_size=200")
        assert resp.status_code == 422


# =============================================================================
# Auth module tests
# =============================================================================
class TestAuthModule:
    def test_jwt_creation_and_decode(self):
        """JWT创建和解析应正常工作"""
        token = create_access_token(data={"sub": "42", "role": "admin"})
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["role"] == "admin"

    def test_jwt_with_bad_secret_fails(self):
        """错误密钥应无法解析JWT"""
        token = create_access_token(data={"sub": "1"})
        # Tamper with token
        bad_token = token[:-5] + "xxxxx"
        payload = verify_token(bad_token)
        assert payload is None
