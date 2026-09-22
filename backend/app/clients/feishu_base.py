"""
飞书 Base API 客户端封装
职责: tenant_access_token 管理、请求重试、速率控制、分页处理
"""
import asyncio
import time
from typing import Any, AsyncIterator, Optional

import httpx
from diskcache import Cache


class FeishuAPIError(Exception):
    """飞书 API 业务错误"""

    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code


class FeishuBaseClient:
    """飞书多维表格 API 客户端"""

    TOKEN_CACHE_KEY = "feishu_tenant_access_token"
    TOKEN_TTL = 7000  # token 有效期 ~2h，提前缓存

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        base_token: str,
        cache_dir: str = "./cache",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_token = base_token
        self.cache = Cache(cache_dir)
        self.client = httpx.AsyncClient(timeout=30.0, http2=True)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        # 速率限制: 20 QPS (飞书开放平台默认) = 50ms 间隔
        self._last_request_time = 0.0
        self._min_interval = 0.05
        self._lock = asyncio.Lock()

    async def _get_tenant_access_token(self) -> str:
        """获取/缓存 tenant_access_token"""
        cached = self.cache.get(self.TOKEN_CACHE_KEY)
        if cached:
            return cached

        resp = await self.client.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise FeishuAPIError(
                data.get("msg", "Failed to get tenant_access_token"),
                data.get("code", 0),
            )
        token = data["tenant_access_token"]
        self.cache.set(self.TOKEN_CACHE_KEY, token, expire=self.TOKEN_TTL)
        return token

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict:
        """统一请求封装（含速率控制和重试）"""
        token = await self._get_tenant_access_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        headers.setdefault("Content-Type", "application/json")

        url = f"https://open.feishu.cn/open-apis{path}"

        for attempt in range(self.max_retries + 1):
            # 速率控制
            async with self._lock:
                now = time.time()
                elapsed = now - self._last_request_time
                if elapsed < self._min_interval:
                    await asyncio.sleep(self._min_interval - elapsed)
                self._last_request_time = time.time()

            try:
                resp = await self.client.request(
                    method, url, headers=headers, **kwargs
                )
                # 429 Too Many Requests -> 退避重试
                if resp.status_code == 429:
                    wait = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                result = resp.json()
                # 飞书业务错误码处理
                if result.get("code") != 0:
                    if result.get("code") == 99991663:  # token 过期
                        self.cache.delete(self.TOKEN_CACHE_KEY)
                        continue
                    raise FeishuAPIError(
                        result.get("msg", "Unknown error"),
                        result.get("code", 0),
                    )
                return result
            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
            except FeishuAPIError:
                raise
            except Exception as e:
                if attempt == self.max_retries:
                    raise FeishuAPIError(str(e), 0) from e
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

        raise FeishuAPIError("Max retries exceeded", 0)

    # ── 表记录操作 ──

    async def list_records(
        self,
        table_id: str,
        filter_expr: Optional[str] = None,
        sort: Optional[list] = None,
        page_size: int = 500,
    ) -> AsyncIterator[dict]:
        """分页遍历表记录（生成器，内存友好）"""
        page_token = None
        while True:
            params: dict[str, Any] = {"page_size": min(page_size, 500)}
            if filter_expr:
                params["filter"] = filter_expr
            if sort:
                params["sort"] = sort
            if page_token:
                params["page_token"] = page_token

            result = await self._request(
                "GET",
                f"/bitable/v1/apps/{self.base_token}/tables/{table_id}/records",
                params=params,
            )
            items = result["data"]["items"]
            for item in items:
                yield self._normalize_record(item)

            if not result["data"].get("has_more"):
                break
            page_token = result["data"].get("page_token")

    async def get_record(
        self, table_id: str, record_id: str
    ) -> Optional[dict]:
        """按 record_id 获取单条记录"""
        try:
            result = await self._request(
                "GET",
                f"/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/{record_id}",
            )
            return self._normalize_record(result["data"]["record"])
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def create_record(self, table_id: str, fields: dict) -> dict:
        """创建记录"""
        result = await self._request(
            "POST",
            f"/bitable/v1/apps/{self.base_token}/tables/{table_id}/records",
            json={"fields": fields},
        )
        return self._normalize_record(result["data"]["record"])

    async def batch_create_records(
        self, table_id: str, records: list[dict]
    ) -> list[dict]:
        """批量创建记录（飞书限制单次最多 100 条）"""
        BATCH_SIZE = 100
        created = []
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i : i + BATCH_SIZE]
            result = await self._request(
                "POST",
                f"/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/batch_create",
                json={"records": [{"fields": r} for r in batch]},
            )
            created.extend(
                [
                    self._normalize_record(r)
                    for r in result["data"]["records"]
                ]
            )
        return created

    async def update_record(
        self, table_id: str, record_id: str, fields: dict
    ) -> dict:
        """更新记录"""
        result = await self._request(
            "PUT",
            f"/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/{record_id}",
            json={"fields": fields},
        )
        return self._normalize_record(result["data"]["record"])

    async def batch_update_records(
        self, table_id: str, records: list[tuple[str, dict]]
    ) -> list[dict]:
        """批量更新记录（飞书限制单次最多 100 条）"""
        BATCH_SIZE = 100
        updated = []
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i : i + BATCH_SIZE]
            result = await self._request(
                "POST",
                f"/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/batch_update",
                json={
                    "records": [
                        {"record_id": rid, "fields": f} for rid, f in batch
                    ]
                },
            )
            updated.extend(
                [
                    self._normalize_record(r)
                    for r in result["data"]["records"]
                ]
            )
        return updated

    async def delete_record(
        self, table_id: str, record_id: str
    ) -> None:
        """删除记录"""
        await self._request(
            "DELETE",
            f"/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/{record_id}",
        )

    async def batch_delete_records(
        self, table_id: str, record_ids: list[str]
    ) -> None:
        """批量删除记录（飞书限制单次最多 100 条）"""
        BATCH_SIZE = 100
        for i in range(0, len(record_ids), BATCH_SIZE):
            batch = record_ids[i : i + BATCH_SIZE]
            await self._request(
                "POST",
                f"/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/batch_delete",
                json={"records": batch},
            )

    async def search_records(
        self,
        table_id: str,
        field_name: str,
        value: Any,
    ) -> AsyncIterator[dict]:
        """按字段值搜索记录（使用 filter 表达式）
        字段名使用白名单校验，字符串值使用 JSON 序列化转义，防止注入
        """
        import re
        if not re.match(r'^[\w\u4e00-\u9fff]+$', field_name):
            raise ValueError(f"Invalid field_name: {field_name}")

        # 飞书 filter 语法: CurrentValue.["字段名"] = "值"
        if isinstance(value, bool):
            val_str = "true" if value else "false"
            filter_expr = f'CurrentValue.["{field_name}"] = {val_str}'
        elif isinstance(value, (int, float)):
            filter_expr = f'CurrentValue.["{field_name}"] = {value}'
        else:
            # 使用 JSON 序列化安全转义字符串值
            import json
            safe_value = json.dumps(str(value))
            filter_expr = f'CurrentValue.["{field_name}"] = {safe_value}'
        async for record in self.list_records(
            table_id, filter_expr=filter_expr
        ):
            yield record

    def _normalize_record(self, raw: dict) -> dict:
        """规范化飞书返回的记录格式"""
        record_id = raw.get("record_id") or raw.get("id")
        fields = raw.get("fields", {})
        # 将 record_id 注入字段，方便应用层使用
        fields["_record_id"] = record_id
        return fields

    async def close(self):
        await self.client.aclose()
