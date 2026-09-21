"""
Repository 工厂，集中管理所有表的 Repository 实例
替代 SQLAlchemy Session 的依赖注入模式
"""
from typing import Any, Optional

from app.clients.feishu_base import FeishuBaseClient
from app.repositories.base_repo import BaseRepository


class RepositoryFactory:
    """Repository 工厂，集中管理 31 张表的 Repository 实例"""

    def __init__(
        self,
        client: FeishuBaseClient,
        cache: Optional[Any] = None,
        table_ids: Optional[dict[str, str]] = None,
    ):
        self.client = client
        self.cache = cache
        # 默认 table_id 映射（用户可在环境变量或配置中覆盖）
        self.table_ids = table_ids or {}

        # 30 个业务表 + 1 users 表
        self.breed = self._repo("breed", "breed_code")
        self.house = self._repo("house", "house_code")
        self.batch = self._repo("batch", "batch_no")
        self.animal = self._repo("animal_individual", "animal_no")
        self.growth = self._repo("growth_record", None)
        self.health = self._repo("health_record", None)
        self.operation = self._repo("breeding_operation", None)
        self.env_param = self._repo("environment_param", None)
        self.alert = self._repo("alert", None)
        self.feed = self._repo("feed_consumption", None)
        self.purchase = self._repo("purchase_order", "order_no")
        self.purchase_item = self._repo("purchase_item", None)
        self.inventory = self._repo("inventory", "item_code")
        self.inv_trans = self._repo("inventory_transaction", None)
        self.hatching = self._repo("hatching_record", None)
        self.sales = self._repo("sales_order", "order_no")
        self.sales_item = self._repo("sales_item", None)
        self.culling = self._repo("culling_record", None)
        self.benchmark = self._repo("benchmark_standard", None)
        self.performance = self._repo("performance_analysis", None)
        self.traceability = self._repo("traceability_chain", "traceability_code")
        self.pilot_project = self._repo("pilot_project", "project_code")
        self.pilot_batch = self._repo("pilot_batch", None)
        self.pilot_indicator = self._repo("pilot_indicator", None)
        self.market = self._repo("market_price", None)
        self.sys_config = self._repo("sys_config", "config_key")
        self.sys_config_history = self._repo("sys_config_history", None)
        self.financial = self._repo("financial_transaction", None)
        self.cost = self._repo("cost_allocation", None)
        self.profit = self._repo("profit_analysis", None)
        self.users = self._repo("users", "username")

    def _repo(self, table_name: str, primary_key_field: Optional[str]) -> BaseRepository:
        """创建 Repository 实例，优先使用用户配置的 table_id"""
        table_id = self.table_ids.get(table_name, table_name)
        return BaseRepository(
            client=self.client,
            table_id=table_id,
            primary_key_field=primary_key_field,
            cache=self.cache,
            cache_ttl=300,
        )

    async def close(self):
        await self.client.close()


# ── FastAPI Depends 依赖注入函数 ──

from fastapi import Request


async def get_repositories(request: Request) -> RepositoryFactory:
    """FastAPI Depends 用：获取 Repository 工厂"""
    return request.app.state.repositories


async def get_base_client(request: Request) -> FeishuBaseClient:
    """从 app state 获取 Base 客户端"""
    return request.app.state.base_client


async def get_cache(request: Request):
    """获取缓存实例"""
    return request.app.state.cache


__all__ = [
    "BaseRepository",
    "RepositoryFactory",
    "get_repositories",
    "get_base_client",
    "get_cache",
]
