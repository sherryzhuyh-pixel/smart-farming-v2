"""
BaseRepository: 替代 SQLAlchemy ORM 的通用 CRUD 封装
为每张表提供一个 Repository 实例，实现与 ORM 类似的接口
S4 Phase 1 增强：支持 field_mapping（英文字段名 <-> 中文字段名双向映射）
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
        field_mapping: Optional[dict[str, str]] = None,
    ):
        self.client = client
        self.table_id = table_id
        self.primary_key_field = primary_key_field
        self.cache = cache
        self.cache_ttl = cache_ttl
        self.field_mapping = field_mapping or {}
        # 反向映射：中文 -> 英文
        self._reverse_mapping = {v: k for k, v in self.field_mapping.items()}

    def _cache_key(self, key: str) -> str:
        return f"base:{self.table_id}:{key}"

    def _map_to_feishu(self, data: dict) -> dict:
        """将英文字段名映射为飞书中文字段名（用于 create/update）"""
        if not self.field_mapping:
            return data
        mapped = {}
        for key, value in data.items():
            feishu_key = self.field_mapping.get(key, key)
            mapped[feishu_key] = value
        return mapped

    def _map_from_feishu(self, data: dict) -> dict:
        """将飞书中文字段名映射回英文字段名（用于 read）"""
        if not self.field_mapping:
            return data
        mapped = {}
        for key, value in data.items():
            # 保留内部字段（如 _record_id）不做映射
            if key.startswith("_"):
                mapped[key] = value
                continue
            english_key = self._reverse_mapping.get(key, key)
            mapped[english_key] = value
        return mapped

    # ── CRUD 基础操作 ──

    async def create(self, data: dict) -> dict:
        """创建记录"""
        mapped_data = self._map_to_feishu(data)
        record = await self.client.create_record(self.table_id, mapped_data)
        normalized = self._normalize_record(record)
        if self.primary_key_field:
            pk = normalized.get(self.primary_key_field)
            if pk and self.cache:
                self.cache.set(
                    self._cache_key(str(pk)), normalized, expire=self.cache_ttl
                )
        return normalized

    async def get_by_id(self, record_id: str) -> Optional[dict]:
        """按飞书 record_id 查询"""
        cache_key = self._cache_key(f"rid:{record_id}")
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        record = await self.client.get_record(self.table_id, record_id)
        if record:
            normalized = self._normalize_record(record)
            if self.cache:
                self.cache.set(cache_key, normalized, expire=self.cache_ttl)
                # 同时缓存业务主键
                if self.primary_key_field:
                    pk = normalized.get(self.primary_key_field)
                    if pk:
                        self.cache.set(
                            self._cache_key(str(pk)),
                            normalized,
                            expire=self.cache_ttl,
                        )
            return normalized
        return None

    async def get_by_field(self, field: str, value: Any) -> Optional[dict]:
        """按字段值查询单条记录（字段名使用英文或中文均可）"""
        # 如果 field 是英文名，映射为中文用于飞书搜索
        feishu_field = self.field_mapping.get(field, field)
        async for record in self.client.search_records(
            self.table_id, feishu_field, value
        ):
            return self._normalize_record(record)
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
        feishu_pk_field = self.field_mapping.get(
            self.primary_key_field, self.primary_key_field
        )
        async for record in self.client.search_records(
            self.table_id, feishu_pk_field, pk_value
        ):
            normalized = self._normalize_record(record)
            if self.cache:
                self.cache.set(cache_key, normalized, expire=self.cache_ttl)
            return normalized
        return None

    async def update(self, record_id: str, data: dict) -> dict:
        """按 record_id 更新"""
        mapped_data = self._map_to_feishu(data)
        updated = await self.client.update_record(
            self.table_id, record_id, mapped_data
        )
        normalized = self._normalize_record(updated)
        # 失效缓存
        if self.cache:
            self.cache.delete(self._cache_key(f"rid:{record_id}"))
            if self.primary_key_field:
                pk = normalized.get(self.primary_key_field)
                if pk:
                    self.cache.delete(self._cache_key(str(pk)))
        return normalized

    async def update_by_pk(self, pk_value: Any, data: dict) -> Optional[dict]:
        """按业务主键更新"""
        existing = await self.get_by_pk(pk_value)
        if not existing:
            return None
        record_id = existing["_record_id"]
        return await self.update(record_id, data)

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
            records.append(self._normalize_record(record))
            count += 1
            if limit and count >= limit:
                break
        return records

    async def list_records_dict(
        self,
        filter_str: Optional[str] = None,
        filter_structured: Optional[dict] = None,
        limit: Optional[int] = None,
        sort: Optional[list] = None,
    ) -> dict:
        """分页查询，返回标准响应格式（适配路由层）"""
        records = []
        count = 0
        async for record in self.client.list_records(
            self.table_id,
            filter_expr=filter_str,
            filter_structured=filter_structured,
            sort=sort,
        ):
            records.append(self._normalize_record(record))
            count += 1
            if limit and count >= limit:
                break
        return {"records": records, "total": count}

    async def filter_by(
        self,
        field: str,
        value: Any,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """按字段过滤查询"""
        records = []
        count = 0
        feishu_field = self.field_mapping.get(field, field)
        async for record in self.client.search_records(
            self.table_id, feishu_field, value
        ):
            records.append(self._normalize_record(record))
            count += 1
            if limit and count >= limit:
                break
        return records

    # ── 批量操作 ──

    async def batch_create(self, data_list: list[dict]) -> list[dict]:
        """批量创建（自动分片，单次上限 100 条）"""
        mapped_list = [self._map_to_feishu(d) for d in data_list]
        records = await self.client.batch_create_records(self.table_id, mapped_list)
        return [self._normalize_record(r) for r in records]

    async def batch_update(
        self, records: list[tuple[str, dict]]
    ) -> list[dict]:
        """批量更新（自动分片，单次上限 100 条）
        records: [(record_id, fields), ...]
        """
        mapped_records = [
            (rid, self._map_to_feishu(fields)) for rid, fields in records
        ]
        updated = await self.client.batch_update_records(
            self.table_id, mapped_records
        )
        return [self._normalize_record(r) for r in updated]

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

    # ── 内部方法 ──

    def _normalize_record(self, raw: dict) -> dict:
        """规范化飞书返回的记录格式"""
        record_id = raw.get("record_id") or raw.get("id")
        fields = raw.get("fields", {})
        # 将 record_id 注入字段，方便应用层使用
        fields["_record_id"] = record_id
        # 字段名映射：中文 -> 英文
        return self._map_from_feishu(fields)
