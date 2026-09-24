"""
Repository 工厂，集中管理所有表的 Repository 实例
替代 SQLAlchemy Session 的依赖注入模式
S4 Phase 1 更新：新增 V3 指标层 3 张表 + 全量 FIELD_MAPPINGS + DEFAULT_TABLE_IDS
"""
from typing import Any, Optional

from app.clients.feishu_base import FeishuBaseClient
from app.repositories.base_repo import BaseRepository


# 飞书 Base 真实 table_id 映射（表名 -> table_id）
DEFAULT_TABLE_IDS = {
    "breed": "tblk17I1dQ2v1gEs",
    "house": "tblixNzK8t8PlWD6",
    "batch": "tblLIgJiDbK3jYOb",
    "animal_individual": "tblaRxXhjxN8fgDu",
    "growth_record": "tbltydlsXR6oVBTj",
    "health_record": "tblWYRLkrd8OyrmV",
    "breeding_operation": "tblAUl7eZPbaRgzU",
    "environment_param": "tbluaD1MVQ4Ukiaj",
    "alert": "tblrJZB0fUz2b1ej",
    "feed_consumption": "tblkwDZgf4tialVd",
    "purchase_order": "tblef9zGf1LalTpE",
    "purchase_item": "tblioPBqRwKhw1vZ",
    "inventory": "tbl2obx2lNfiDJDn",
    "inventory_transaction": "tblHaH23eWq68yZ0",
    "hatching_record": "tblpaERjpRy1AH2d",
    "sales_order": "tblm8cDPvOoN8v25",
    "sales_item": "tblxGkV2T9cs3VzX",
    "culling_record": "tblpGMVvKJyMSpSO",
    "benchmark_standard": "tblC5CZctsgKKaOe",
    "performance_analysis": "tblNSkzaupvilBKp",
    "traceability_chain": "tblxVJH8j7FA0h4i",
    "pilot_project": "tblLJQqbc6EkMuq3",
    "pilot_batch": "tblx0lcfwjjVa5fM",
    "pilot_indicator": "tblttrzRWtO5gOq3",
    "market_price": "tbl5q441BWNBe1hy",
    "sys_config": "tbl3MFmagrUB2Fi2",
    "sys_config_history": "tblrhkmC32wHmQMz",
    "financial_transaction": "tbl8f2ow4iiHkpjK",
    "cost_allocation": "tblxl9sb0UkJbFzQ",
    "profit_analysis": "tblQ4Gm1k7V5Cez4",
    "farming_events": "tblYDcpLnhS5CEfE",
    "device_ledger": "tblCCaIpacTt7UAu",
    "data_sources": "tbl1ZoDSd95OGHfn",
    "users": "tblygsKhkVyuEJrM",
    # --- V3 新增指标层表 ---
    "indicator_dictionary": "tbl5TyWJmWU9361S",
    "indicator_threshold": "tblpVSDxMHqsIHQY",
    "indicator_computation_log": "tbl75Zx3c2bNLdQJ",
}

FIELD_MAPPINGS = {
    "alert": {"batch": "养殖批次", "house": "鸡舍", "alert_id": "alert_id", "alert_type": "alert_type", "alert_level": "alert_level", "alert_time": "alert_time", "alert_value": "alert_value", "threshold_value": "threshold_value", "handle_time": "handle_time", "handle_note": "handle_note", "status": "status", "animal_id": "animal_id", "house_id": "house_id", "device_id": "device_id", "related_event_id": "related_event_id", "source_type": "source_type", "source_ref": "source_ref", "handler": "handler", "group_id": "group_id"},
    "animal_individual": {"animal_no": "个体编号", "batch_id": "养殖批次", "house_id": "鸡舍", "breed_id": "品种", "gender": "性别", "birth_date": "出生日期", "date_in": "入栏日期", "age_day_in": "入栏日龄", "weight_in": "入栏体重_g", "weight_out": "出栏体重_g", "date_out": "出栏日期", "exit_type": "出栏类型", "status": "状态", "traceability_code": "溯源码", "dam_id": "母系ID", "sire_id": "父系ID"},
    "batch": {"batch_no": "批次编号", "batch_name": "批次名称", "breed_id": "品种", "house_id": "鸡舍", "date_in": "入栏日期", "date_out": "出栏日期", "quantity_initial": "入栏数量_羽", "quantity_current": "存栏数量_羽", "quantity_out": "出栏数量_羽", "status": "批次状态", "remark": "备注"},
    "benchmark_standard": {"standard_name": "标准名称", "breed": "品种", "start_age_days": "起始日龄", "end_age_days": "结束日龄", "target_weight_g": "目标体重_g", "target_daily_gain_g": "目标日增重_g", "target_egg_rate_pct": "目标产蛋率_pct", "target_survival_pct": "目标成活率_pct", "target_fcr": "目标料肉比", "target_temp_min_c": "目标温度下限_C", "target_temp_max_c": "目标温度上限_C", "target_humidity_min_pct": "目标湿度下限_pct", "target_humidity_max_pct": "目标湿度上限_pct", "target_feed_intake_g": "目标采食量_g_羽_日", "source": "标准来源"},
    "breed": {"breed_code": "品种编码", "breed_name": "品种名称", "breed_type": "品种类型", "origin": "品种来源", "description": "品种特性描述", "avg_weight_male": "成年公鸡均重_kg", "avg_weight_female": "成年母鸡均重_kg", "avg_egg_rate": "平均产蛋率_pct", "feed_meat_ratio": "标准料肉比", "survival_rate_std": "标准成活率_pct", "daily_gain_std": "标准日增重_g"},
    "breeding_operation": {"op_no": "操作编号", "op_type": "操作类型", "batch": "关联批次", "house": "关联鸡舍", "op_date": "操作日期", "feed_type": "饲料类型", "feed_qty_kg": "饲料用量(kg)", "drug_name": "药品/疫苗名称", "drug_dose": "用药剂量", "admin_route": "给药途径", "target_house": "目标鸡舍", "sample_count": "称重抽样数量", "avg_weight_g": "平均体重(g)", "operator": "操作人", "remark": "备注"},
    "cost_allocation": {},
    "culling_record": {"batch": "养殖批次", "animal": "个体", "cull_date": "淘汰日期", "cull_reason": "淘汰原因", "cull_qty": "淘汰数量", "total_weight_kg": "总重量_kg", "disposal_method": "处理方式", "disposal_revenue": "处置收入_元", "operator": "操作人", "remark": "备注"},
    "data_sources": {},
    "device_ledger": {"device_id": "device_id", "device_name": "device_name", "device_type": "device_type", "protocol": "protocol", "manufacturer": "manufacturer", "location_detail": "location_detail", "house_id": "house_id", "mqtt_topic": "mqtt_topic", "install_date": "install_date", "last_heartbeat": "last_heartbeat", "status": "status", "remarks": "remarks", "source_id": "source_id"},
    "environment_param": {"batch": "养殖批次", "house": "鸡舍", "record_time": "record_time", "temperature": "temperature", "humidity": "humidity", "dissolved_oxygen": "dissolved_oxygen", "ammonia": "ammonia", "water_temp": "water_temp", "location": "location", "device_id": "device_id", "house_id": "house_id", "source_type": "source_type"},
    "farming_events": {"event_id": "event_id", "animal_id": "animal_id", "batch": "养殖批次", "house": "鸡舍", "event_date": "event_date", "event_type": "event_type", "description": "description", "location": "location", "operator": "operator", "source_type": "source_type", "source_ref": "source_ref", "group_id": "group_id", "confidence": "confidence"},
    "feed_consumption": {"batch": "养殖批次", "house": "鸡舍", "record_date": "record_date", "feed_type": "feed_type", "feed_quantity_kg": "feed_quantity_kg", "avg_intake_kg": "avg_intake_kg", "animal_count": "animal_count", "feed_cost": "feed_cost", "group_id": "group_id", "confidence": "confidence", "source_type": "source_type"},
    "financial_transaction": {"transaction_type": "收支类型", "category": "收支科目", "amount": "金额", "batch_id": "关联批次", "ref_table": "关联业务表", "ref_id": "关联业务ID", "transaction_date": "交易日期", "payee_payer": "收款/付款方", "remark": "备注", "voucher_no": "凭证号", "created_by": "录入人"},
    "growth_record": {"animal_id": "个体", "batch_id": "养殖批次", "record_date": "记录日期", "age_days": "日龄", "weight": "体重_g", "body_length": "体长_cm", "chest_girth": "胸围_cm", "shank_length": "胫长_cm", "recorder": "记录人", "remark": "备注"},
    "hatching_record": {},
    "health_record": {"event_id": "event_id", "animal_id": "animal_id", "batch_id": "养殖批次", "house_id": "鸡舍", "record_date": "record_date", "record_type": "记录类型", "disease_name": "disease_name", "diagnosis": "diagnosis", "symptom": "symptoms", "treatment": "treatment", "drug_name": "药品名称", "drug_dosage": "用药剂量", "route": "给药途径", "treatment_result": "治疗结果", "cost": "费用_元", "mortality_flag": "死亡标记", "health_status": "health_status", "source_type": "source_type", "confidence": "confidence", "veterinarian": "veterinarian"},
    "house": {"house_code": "鸡舍编码", "house_name": "鸡舍名称", "house_type": "鸡舍类型", "area_sqm": "建筑面积_m2", "capacity": "设计存栏量_羽", "location": "地理位置", "env_device_id": "环境监控设备编号", "camera_ids": "摄像头编号", "status": "状态"},
    "inventory": {"item_code": "物料编码", "item_name": "物料名称", "item_category": "物料类别", "item_spec": "规格", "unit": "单位", "quantity": "当前库存量", "safety_stock": "安全库存", "storage_location": "存放位置", "batch_no": "入库批号", "expiry_date": "有效期至", "status": "状态"},
    "inventory_transaction": {},
    "market_price": {},
    "performance_analysis": {"analysis_dimension": "分析维度", "batch": "养殖批次", "analysis_date": "分析日期", "age_days": "当日日龄", "benchmark": "基准标准", "actual_weight_g": "实际均重_g", "target_weight_g": "目标均重_g", "weight_deviation_g": "体重偏差_g", "weight_deviation_pct": "体重偏差率_pct", "actual_daily_gain_g": "实际日增重_g", "target_daily_gain_g": "目标日增重_g", "daily_gain_deviation_pct": "日增重偏差率_pct", "actual_fcr": "实际料肉比", "target_fcr": "目标料肉比", "fcr_deviation_pct": "料肉比偏差率_pct", "actual_survival_pct": "实际成活率_pct", "target_survival_pct": "目标成活率_pct", "survival_deviation_pp": "成活率偏差_pp", "actual_egg_rate_pct": "实际产蛋率_pct", "target_egg_rate_pct": "目标产蛋率_pct", "egg_rate_deviation_pp": "产蛋率偏差_pp"},
    "pilot_batch": {},
    "pilot_indicator": {},
    "pilot_project": {"project_code": "项目编码", "project_name": "项目名称", "project_type": "项目类型", "tech_partner": "技术合作方", "channel_partner": "渠道合作方", "description": "项目描述", "target_scale": "目标规模_羽", "current_stage": "当前阶段", "status": "状态", "start_date": "开始日期", "end_date": "结束日期", "project_lead": "项目负责人"},
    "profit_analysis": {"batch": "养殖批次", "total_revenue": "总收入", "total_cost": "总成本", "gross_profit": "毛利润", "gross_margin": "毛利率", "cost_per_bird": "单只成本", "revenue_per_bird": "单只收入", "analysis_date": "分析日期"},
    "purchase_item": {"purchase_order": "采购订单", "product_name": "品名", "specification": "规格", "unit": "单位", "qty": "数量", "unit_price": "单价", "subtotal": "小计金额", "batch_no": "生产批号", "expiry_date": "有效期至"},
    "purchase_order": {"order_no": "订单编号", "order_type": "订单类型", "supplier_name": "供应商名称", "supplier_contact": "供应商联系人", "order_date": "下单日期", "expected_arrival": "预计到货日期", "total_amount": "订单总金额", "total_qty": "总数量", "status": "状态", "remark": "备注"},
    "sales_item": {"sales_order": "销售订单", "source_batch": "来源批次", "product_name": "品名", "specification": "规格", "unit": "单位", "qty": "数量", "unit_price": "单价", "subtotal": "小计金额", "traceability_code": "溯源码"},
    "sales_order": {"order_no": "订单编号", "order_type": "订单类型", "customer_name": "客户名称", "customer_contact": "客户联系人", "customer_phone": "客户电话", "order_date": "下单日期", "delivery_date": "交货日期", "total_amount": "订单总金额", "total_qty": "总数量", "status": "状态", "remark": "备注"},
    "sys_config": {"config_key": "配置键", "config_value": "配置值", "value_type": "值类型", "scope": "作用域", "scope_id": "作用域对象ID", "description": "配置说明", "editable": "是否可编辑"},
    "sys_config_history": {},
    "traceability_chain": {"traceability_code": "溯源码", "batch": "养殖批次", "animal": "个体", "stage": "阶段", "stage_id": "阶段关联ID", "event_date": "事件日期", "event_desc": "事件描述", "location": "地点", "operator": "操作人", "data_hash": "数据哈希"},
    "users": {},
    # --- V3 新增：指标字典 ---
    "indicator_dictionary": {
        "indicator_code": "指标编码",
        "indicator_name_cn": "中文名称",
        "indicator_name_en": "英文名称",
        "category": "分类",
        "formula": "计算公式",
        "numerator": "分子",
        "denominator": "分母",
        "definition_note": "口径说明",
        "time_window": "时间窗",
        "object_dimension": "对象维度",
        "unit": "单位",
        "value_range": "值域",
        "threshold_excellent": "阈值优良",
        "threshold_minimum": "阈值底线",
        "data_sources": "数据来源",
        "collection_frequency": "采集频率",
        "version": "版本",
        "priority": "优先级",
        "status": "状态",
    },
    # --- V3 新增：指标阈值配置 ---
    "indicator_threshold": {
        "indicator_code": "指标编码",
        "breed": "品种",
        "season": "季节",
        "farm_area": "场区",
        "threshold_excellent": "阈值优良",
        "threshold_good": "阈值良好",
        "threshold_warning": "阈值警告",
        "threshold_danger": "阈值危险",
        "effective_date": "生效日期",
        "expiry_date": "失效日期",
        "is_active": "是否启用",
        "remark": "备注",
    },
    # --- V3 新增：指标计算日志 ---
    "indicator_computation_log": {
        "indicator_code": "指标编码",
        "indicator_name": "指标名称",
        "object_type": "计算对象类型",
        "object_id": "计算对象ID",
        "period_type": "周期类型",
        "period_start": "周期开始",
        "period_end": "周期结束",
        "computed_value": "计算值",
        "unit": "单位",
        "threshold_status": "阈值状态",
        "formula_applied": "应用公式",
        "data_sources": "数据来源",
        "compute_duration_ms": "计算耗时ms",
        "computed_at": "计算时间",
        "is_success": "是否成功",
        "error_message": "错误信息",
    },
}


class RepositoryFactory:
    """Repository 工厂，集中管理所有表的 Repository 实例"""

    def __init__(
        self,
        client: FeishuBaseClient,
        cache: Optional[Any] = None,
        table_ids: Optional[dict[str, str]] = None,
    ):
        self.client = client
        self.cache = cache
        self.table_ids = {**DEFAULT_TABLE_IDS, **(table_ids or {})}

        # V2 业务表
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
        self.farming_events = self._repo("farming_events", None)
        self.device_ledger = self._repo("device_ledger", None)
        self.data_sources = self._repo("data_sources", None)
        self.users = self._repo("users", "username")
        # V3 指标层表
        self.indicator_dictionary = self._repo("indicator_dictionary", "indicator_code")
        self.indicator_threshold = self._repo("indicator_threshold", None)
        self.indicator_computation_log = self._repo("indicator_computation_log", None)

    def _repo(self, table_name: str, primary_key_field: Optional[str]) -> BaseRepository:
        table_id = self.table_ids.get(table_name, table_name)
        field_mapping = FIELD_MAPPINGS.get(table_name)
        return BaseRepository(
            client=self.client,
            table_id=table_id,
            primary_key_field=primary_key_field,
            cache=self.cache,
            cache_ttl=300,
            field_mapping=field_mapping,
        )

    async def close(self):
        await self.client.close()


# ── FastAPI Depends 依赖注入函数 ──

# 模块级全局引用，由 main.py startup 事件注入
_repositories: RepositoryFactory | None = None
_base_client: FeishuBaseClient | None = None
_cache_instance = None
_init_lock = None


def _get_init_lock():
    global _init_lock
    if _init_lock is None:
        import asyncio
        _init_lock = asyncio.Lock()
    return _init_lock


async def get_repositories() -> RepositoryFactory:
    global _repositories, _base_client, _cache_instance
    if _repositories is not None:
        return _repositories

    lock = _get_init_lock()
    async with lock:
        # 双检锁，防止并发重复初始化
        if _repositories is not None:
            return _repositories

        # 懒加载：从配置初始化 FeishuBaseClient 和 RepositoryFactory
        from app.config import get_settings
        settings = get_settings()
        client = FeishuBaseClient(
            app_id=settings.LARK_APP_ID,
            app_secret=settings.LARK_APP_SECRET,
            base_token=settings.LARK_BASE_TOKEN,
            cache_dir=settings.CACHE_DIR,
        )
        repos = RepositoryFactory(client=client, cache=client.cache)
        _repositories = repos
        _base_client = client
        _cache_instance = client.cache
        return repos


async def get_base_client() -> FeishuBaseClient:
    if _base_client is None:
        await get_repositories()  # 触发懒加载
    return _base_client


async def get_cache():
    if _cache_instance is None:
        await get_repositories()  # 触发懒加载
    return _cache_instance


__all__ = [
    "BaseRepository",
    "RepositoryFactory",
    "get_repositories",
    "get_base_client",
    "get_cache",
]
