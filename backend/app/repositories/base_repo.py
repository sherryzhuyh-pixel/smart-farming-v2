"""
BaseRepository: 替代 SQLAlchemy ORM 的通用 CRUD 封装
为每张表提供一个 Repository 实例，实现与 ORM 类似的接口
"""
from typing import Any, Optional

from app.clients.feishu_base import FeishuBaseClient


class BaseRepository:
    """
    通用 Base 数据仓库
    每个业务表对应一个 Repository 实例
    """

    def __init__(
        self,
        client: FeishuBaseClient,
        table_id: str,
        primary_key_field: Optional[str],  # 业务主键字段名（如 "batch_no"）
        cache: Optional[Any] = None,
        cache_ttl: int = 300,
    ):
        self.client = client
        self.table_id = table_id
        self.primary_key_field = primary_key_field
        self.cache = cache
        self.cache_ttl = cache_ttl

    def _cache_key(self, key: str) -> str:
        return f"base:{self.table_id}:{key}"

    # ── CRUD 基础操作 ──

    async def create(self, data: dict) -> dict:
        """创建记录"""
        record = await self.client.create_record(self.table_id, data)
        if self.primary_key_field:
            pk = record.get(self.primary_key_field)
            if pk and self.cache:
                self.cache.set(
                    self._cache_key(str(pk)), record, expire=self.cache_ttl
                )
        return record

    async def get_by_id(self, record_id: str) -> Optional[dict]:
        """按飞书 record_id 查询"""
        cache_key = self._cache_key(f"rid:{record_id}")
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        record = await self.client.get_record(self.table_id, record_id)
        if record and self.cache:
            self.cache.set(cache_key, record, expire=self.cache_ttl)
            # 同时缓存业务主键
            if self.primary_key_field:
                pk = record.get(self.primary_key_field)
                if pk:
                    self.cache.set(
                        self._cache_key(str(pk)),
                        record,
                        expire=self.cache_ttl,
                    )
        return record

    async def get_by_field(self, field: str, value: Any) -> Optional[dict]:
        """按字段值查询单条记录"""
        async for record in self.client.search_records(
            self.table_id, field, value
        ):
            return record
        return None

    async def get_by_pk(self, pk_value: Any) -> Optional[dict]:
        """按业务主键查询（先查缓存，再查 Base）"""
        if not self.primary_key_field:
            raise ValueError(
                f"Repository for '{self.table_id}' has no primary_key_field set"
            )
        cache_key = self._cache_key(str(pk_value))
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        # 通过 filter 按业务主键搜索
        async for record in self.client.search_records(
            self.table_id, self.primary_key_field, pk_value
        ):
            if self.cache:
                self.cache.set(cache_key, record, expire=self.cache_ttl)
            return record
        return None

    async def update(self, record_id: str, data: dict) -> dict:
        """按 record_id 更新"""
        updated = await self.client.update_record(
            self.table_id, record_id, data
        )
        # 失效缓存
        if self.cache:
            self.cache.delete(self._cache_key(f"rid:{record_id}"))
            if self.primary_key_field:
                pk = updated.get(self.primary_key_field)
                if pk:
                    self.cache.delete(self._cache_key(str(pk)))
        return updated

    async def update_by_pk(self, pk_value: Any, data: dict) -> Optional[dict]:
        """按业务主键更新"""
        existing = await self.get_by_pk(pk_value)
        if not existing:
            return None
        record_id = existing["_record_id"]
        updated = await self.client.update_record(
            self.table_id, record_id, data
        )
        # 失效缓存
        if self.cache:
            self.cache.delete(self._cache_key(str(pk_value)))
            self.cache.delete(self._cache_key(f"rid:{record_id}"))
        return updated

    async def delete(self, record_id: str) -> None:
        """按 record_id 删除"""
        await self.client.delete_record(self.table_id, record_id)
        if self.cache:
            self.cache.delete(self._cache_key(f"rid:{record_id}"))

    async def delete_by_pk(self, pk_value: Any) -> bool:
        """按业务主键删除"""
        existing = await self.get_by_pk(pk_value)
        if not existing:
            return False
        record_id = existing["_record_id"]
        await self.client.delete_record(self.table_id, record_id)
        if self.cache:
            self.cache.delete(self._cache_key(str(pk_value)))
            self.cache.delete(self._cache_key(f"rid:{record_id}"))
        return True

    # ── 列表查询 ──

    async def list_all(self, limit: Optional[int] = None) -> list[dict]:
        """全量查询（适合小表）"""
        records = []
        count = 0
        async for record in self.client.list_records(self.table_id):
            records.append(record)
            count += 1
            if limit and count >= limit:
                break
        return records

    async def filter_by(
        self,
        field: str,
        value: Any,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """按字段过滤查询"""
        records = []
        count = 0
        async for record in self.client.search_records(
            self.table_id, field, value
        ):
            records.append(record)
            count += 1
            if limit and count >= limit:
                break
        return records

    # ── 批量操作 ──

    async def batch_create(self, data_list: list[dict]) -> list[dict]:
        """批量创建（自动分片，单次上限 100 条）"""
        return await self.client.batch_create_records(self.table_id, data_list)

    async def batch_update(
        self, records: list[tuple[str, dict]]
    ) -> list[dict]:
        """批量更新（自动分片，单次上限 100 条）
        records: [(record_id, fields), ...]
        """
        return await self.client.batch_update_records(
            self.table_id, records
        )

    # ── 关联查询 ──

    async def resolve_fk(
        self,
        record: dict,
        fk_field: str,
        related_repo: "BaseRepository",
    ) -> Optional[dict]:
        """
        解析外键关联（Lazy Loading）
        用法: breed = await batch_repo.resolve_fk(batch, "breed_id", breed_repo)
        """
        fk_value = record.get(fk_field)
        if not fk_value:
            return None
        return await related_repo.get_by_id(str(fk_value))

    async def preload_related(
        self,
        records: list[dict],
        fk_field: str,
        related_repo: "BaseRepository",
        target_field: Optional[str] = None,
    ) -> list[dict]:
        """
        预加载关联数据（Eager Loading）
        用法: batches = await batch_repo.preload_related(
            batches, "breed_id", breed_repo, "breed"
        )
        """
        if not records:
            return records

        # 收集所有外键值
        fk_values = {
            str(r.get(fk_field))
            for r in records
            if r.get(fk_field)
        }
        if not fk_values:
            return records

        # 批量查询关联数据（利用缓存）
        related_map = {}
        for fk in fk_values:
            related = await related_repo.get_by_id(fk)
            if related:
                related_map[fk] = related

        # 注入关联数据
        target = target_field or fk_field.replace("_id", "")
        for r in records:
            fk = str(r.get(fk_field, ""))
            r[target] = related_map.get(fk)

        return records

    # ── 聚合查询（应用层实现） ──

    async def count(self, filter_expr: Optional[str] = None) -> int:
        """统计记录数（需遍历全表）"""
        count = 0
        async for _ in self.client.list_records(
            self.table_id, filter_expr=filter_expr
        ):
            count += 1
        return count
