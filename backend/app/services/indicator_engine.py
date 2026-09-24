"""
Indicator Engine - S4 Phase 1: 10 个可直接计算指标实现
负责指标实时计算、阈值对比和计算日志记录
"""
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.repositories import RepositoryFactory
from app.schemas.indicators import (
    ComputeRequest,
    ComputeResult,
    ComputeResponse,
    ThresholdStatus,
)


class IndicatorEngine:
    """
    指标计算引擎 - S4 Phase 1
    - 实现 10 个可直接计算指标的真实公式
    - 保留阈值对比和计算日志记录
    """

    def __init__(self, repositories: Optional[RepositoryFactory] = None, tenant_access_token: Optional[str] = None):
        self.repositories = repositories
        self.tenant_access_token = tenant_access_token
        self._indicator_repo = None
        self._threshold_repo = None
        self._log_repo = None

    @property
    def indicator_repo(self):
        if self._indicator_repo is None:
            if self.repositories and hasattr(self.repositories, 'indicator_dictionary'):
                self._indicator_repo = self.repositories.indicator_dictionary
            else:
                raise RuntimeError("indicator_dictionary repository not available")
        return self._indicator_repo

    @property
    def threshold_repo(self):
        if self._threshold_repo is None:
            if self.repositories and hasattr(self.repositories, 'indicator_threshold'):
                self._threshold_repo = self.repositories.indicator_threshold
            else:
                raise RuntimeError("indicator_threshold repository not available")
        return self._threshold_repo

    @property
    def log_repo(self):
        if self._log_repo is None:
            if self.repositories and hasattr(self.repositories, 'indicator_computation_log'):
                self._log_repo = self.repositories.indicator_computation_log
            else:
                raise RuntimeError("indicator_computation_log repository not available")
        return self._log_repo

    # ── 便捷属性：数据仓库访问 ──

    @property
    def batch_repo(self):
        return self.repositories.batch if self.repositories else None

    @property
    def growth_repo(self):
        return self.repositories.growth if self.repositories else None

    @property
    def hatching_repo(self):
        return self.repositories.hatching if self.repositories else None

    @property
    def feed_repo(self):
        return self.repositories.feed if self.repositories else None

    # ============================================================
    # 公共接口
    # ============================================================

    async def compute_single(
        self,
        indicator_code: str,
        object_type: str,
        object_id: str,
        period_type: str,
        period_start: str,
        period_end: str,
    ) -> ComputeResult:
        """计算单个指标"""
        start_time = time.time()

        # 1. 查询指标字典定义
        indicator_def = await self.indicator_repo.get_by_field(
            "indicator_code", indicator_code
        )
        if not indicator_def:
            raise ValueError(f"指标编码不存在: {indicator_code}")

        # 2. 查询阈值配置
        thresholds = await self.threshold_repo.filter_by(
            "indicator_code", indicator_code
        )
        active_threshold = None
        for t in thresholds:
            if t.get("is_active"):
                active_threshold = t
                break

        # 3. 执行真实公式计算
        computed_value = await self._execute_formula(
            indicator_def=indicator_def,
            object_type=object_type,
            object_id=object_id,
            period_start=period_start,
            period_end=period_end,
        )

        # 4. 阈值对比
        threshold_status = self._evaluate_threshold(
            computed_value, active_threshold
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # 5. 记录计算日志
        log_data = {
            "indicator_code": indicator_code,
            "indicator_name": indicator_def.get("indicator_name_cn", ""),
            "object_type": self._map_object_type(object_type),
            "object_id": object_id,
            "period_type": self._map_period_type(period_type),
            "period_start": period_start,
            "period_end": period_end,
            "computed_value": computed_value,
            "unit": indicator_def.get("unit", ""),
            "threshold_status": threshold_status.value,
            "formula_applied": indicator_def.get("formula", ""),
            "data_sources": indicator_def.get("data_sources", ""),
            "compute_duration_ms": duration_ms,
            "computed_at": datetime.now().isoformat(),
            "is_success": True,
            "error_message": "",
        }
        try:
            await self.log_repo.create(log_data)
        except Exception:
            pass

        return ComputeResult(
            indicator_code=indicator_code,
            indicator_name=indicator_def.get("indicator_name_cn", ""),
            value=computed_value,
            unit=indicator_def.get("unit", ""),
            threshold_status=threshold_status,
            formula_applied=indicator_def.get("formula", ""),
            data_sources=[indicator_def.get("data_sources", "")],
            computed_at=datetime.now(),
            compute_duration_ms=duration_ms,
        )

    async def compute_batch(self, request: ComputeRequest) -> ComputeResponse:
        """批量计算指标"""
        total_start = time.time()
        results = []
        success_count = 0
        fail_count = 0

        for code in request.indicator_codes:
            try:
                result = await self.compute_single(
                    indicator_code=code,
                    object_type=request.object_type,
                    object_id=request.object_id,
                    period_type=request.period_type,
                    period_start=request.period_start,
                    period_end=request.period_end,
                )
                results.append(result)
                success_count += 1
            except Exception as e:
                fail_count += 1
                log_data = {
                    "indicator_code": code,
                    "indicator_name": "",
                    "object_type": self._map_object_type(request.object_type),
                    "object_id": request.object_id,
                    "period_type": self._map_period_type(request.period_type),
                    "period_start": request.period_start,
                    "period_end": request.period_end,
                    "computed_value": None,
                    "unit": "",
                    "threshold_status": "未配置",
                    "formula_applied": "",
                    "data_sources": "",
                    "compute_duration_ms": 0,
                    "computed_at": datetime.now().isoformat(),
                    "is_success": False,
                    "error_message": str(e),
                }
                try:
                    await self.log_repo.create(log_data)
                except Exception:
                    pass

        total_duration_ms = int((time.time() - total_start) * 1000)
        return ComputeResponse(
            results=results,
            total_duration_ms=total_duration_ms,
            success_count=success_count,
            fail_count=fail_count,
        )

    # ============================================================
    # 公式计算路由
    # ============================================================

    async def _execute_formula(
        self,
        indicator_def: Dict[str, Any],
        object_type: str,
        object_id: str,
        period_start: str,
        period_end: str,
    ) -> float:
        """根据指标编码路由到具体计算方法"""
        code = indicator_def.get("indicator_code", "")

        method_map = {
            # 孵化性能 (3个)
            "IND-HAT-001": self._calc_fertility_rate,
            "IND-HAT-002": self._calc_hatch_rate,
            "IND-HAT-004": self._calc_total_hatch_rate,
            # 生长发育 (3个)
            "IND-BRE-002": self._calc_daily_gain,
            "IND-BRE-003": self._calc_relative_growth,
            "IND-BRE-004": self._calc_uniformity,
            # 存活率 (3个)
            "IND-SUR-001": self._calc_survival_rate,
            "IND-SUR-002": self._calc_survival_rate,
            "IND-SUR-003": self._calc_survival_rate,
            # 饲料利用 (1个)
            "IND-FEE-002": self._calc_avg_daily_feed,
        }

        method = method_map.get(code)
        if method:
            return await method(
                object_type=object_type,
                object_id=object_id,
                period_start=period_start,
                period_end=period_end,
                indicator_code=code,
            )

        # 未实现指标返回 0（占位，后续 Phase 2/3 补充）
        return 0.0

    # ============================================================
    # 孵化性能指标
    # ============================================================

    async def _calc_fertility_rate(
        self, object_type: str, object_id: str,
        period_start: str, period_end: str, indicator_code: str
    ) -> float:
        """
        IND-HAT-001 受精率 = 受精蛋数 / 入孵蛋数 * 100%
        """
        records = await self._get_hatching_records(object_id, period_start, period_end)
        if not records:
            return 0.0

        total_incubated = sum(self._to_float(self._get_field(r, ["入孵蛋数", "incubated_count", "incubated"])) for r in records)
        total_fertilized = sum(self._to_float(self._get_field(r, ["受精蛋数", "fertilized_count", "fertilized"])) for r in records)

        if total_incubated <= 0:
            return 0.0
        return round(total_fertilized / total_incubated * 100, 2)

    async def _calc_hatch_rate(
        self, object_type: str, object_id: str,
        period_start: str, period_end: str, indicator_code: str
    ) -> float:
        """
        IND-HAT-002 孵化率 = 出雏数 / 受精蛋数 * 100%
        """
        records = await self._get_hatching_records(object_id, period_start, period_end)
        if not records:
            return 0.0

        total_fertilized = sum(self._to_float(self._get_field(r, ["受精蛋数", "fertilized_count", "fertilized"])) for r in records)
        total_hatched = sum(self._to_float(self._get_field(r, ["出雏数", "hatched_count", "hatched"])) for r in records)

        if total_fertilized <= 0:
            return 0.0
        return round(total_hatched / total_fertilized * 100, 2)

    async def _calc_total_hatch_rate(
        self, object_type: str, object_id: str,
        period_start: str, period_end: str, indicator_code: str
    ) -> float:
        """
        IND-HAT-004 入孵蛋孵化率 = 出雏数 / 入孵蛋数 * 100%
        """
        records = await self._get_hatching_records(object_id, period_start, period_end)
        if not records:
            return 0.0

        total_incubated = sum(self._to_float(self._get_field(r, ["入孵蛋数", "incubated_count", "incubated"])) for r in records)
        total_hatched = sum(self._to_float(self._get_field(r, ["出雏数", "hatched_count", "hatched"])) for r in records)

        if total_incubated <= 0:
            return 0.0
        return round(total_hatched / total_incubated * 100, 2)

    async def _get_hatching_records(
        self, object_id: str, period_start: str, period_end: str
    ) -> List[Dict[str, Any]]:
        """获取孵化记录，按批次和日期范围过滤"""
        if not self.hatching_repo:
            return []

        # 获取批次 record_id（用于匹配 Link 字段）
        batch_record_id = await self._get_batch_record_id(object_id)

        all_records = await self.hatching_repo.list_all()
        filtered = []
        for r in all_records:
            # 按批次过滤
            batch_link = self._get_field(r, ["养殖批次", "batch_id", "batch", "批次"])
            if batch_link and batch_record_id and str(batch_link) != str(batch_record_id):
                continue
            # 按日期范围过滤
            record_date = self._get_field(r, ["record_date", "event_date", "日期", "date"])
            if record_date and period_start and period_end:
                date_str = str(record_date)[:10]
                if not (period_start <= date_str <= period_end):
                    continue
            filtered.append(r)
        return filtered

    # ============================================================
    # 生长发育指标
    # ============================================================

    async def _calc_daily_gain(
        self, object_type: str, object_id: str,
        period_start: str, period_end: str, indicator_code: str
    ) -> float:
        """
        IND-BRE-002 日增重 = (末重 - 初重) / 日龄差  (g/天)
        """
        records = await self._get_growth_records(object_id, period_start, period_end)
        if len(records) < 2:
            return 0.0

        sorted_records = sorted(records, key=lambda r: self._to_float(r.get("age_days", 0)))
        first = sorted_records[0]
        last = sorted_records[-1]

        weight_first = self._to_float(first.get("weight", 0))
        weight_last = self._to_float(last.get("weight", 0))
        age_first = self._to_float(first.get("age_days", 0))
        age_last = self._to_float(last.get("age_days", 0))

        age_diff = age_last - age_first
        if age_diff <= 0:
            return 0.0

        return round((weight_last - weight_first) / age_diff, 2)

    async def _calc_relative_growth(
        self, object_type: str, object_id: str,
        period_start: str, period_end: str, indicator_code: str
    ) -> float:
        """
        IND-BRE-003 相对生长率 = (末重 - 初重) / 初重 * 100%
        """
        records = await self._get_growth_records(object_id, period_start, period_end)
        if len(records) < 2:
            return 0.0

        sorted_records = sorted(records, key=lambda r: self._to_float(r.get("age_days", 0)))
        first = sorted_records[0]
        last = sorted_records[-1]

        weight_first = self._to_float(first.get("weight", 0))
        weight_last = self._to_float(last.get("weight", 0))

        if weight_first <= 0:
            return 0.0

        return round((weight_last - weight_first) / weight_first * 100, 2)

    async def _calc_uniformity(
        self, object_type: str, object_id: str,
        period_start: str, period_end: str, indicator_code: str
    ) -> float:
        """
        IND-BRE-004 均匀度 = 体重在均值±10%内的个体比例 * 100%
        """
        records = await self._get_growth_records(object_id, period_start, period_end)
        if len(records) < 2:
            return 0.0

        weights = [self._to_float(r.get("weight", 0)) for r in records if self._to_float(r.get("weight", 0)) > 0]
        if len(weights) < 2:
            return 0.0

        mean_weight = sum(weights) / len(weights)
        lower = mean_weight * 0.9
        upper = mean_weight * 1.1

        within_range = sum(1 for w in weights if lower <= w <= upper)
        return round(within_range / len(weights) * 100, 2)

    async def _get_growth_records(
        self, object_id: str, period_start: str, period_end: str
    ) -> List[Dict[str, Any]]:
        """获取生长记录，按批次和日期范围过滤"""
        if not self.growth_repo:
            return []

        # 获取批次 record_id（用于匹配 Link 字段）
        batch_record_id = await self._get_batch_record_id(object_id)

        all_records = await self.growth_repo.list_all()
        filtered = []
        for r in all_records:
            # 按批次过滤（batch_id 是 Link 字段，值为 record_id）
            batch_link = r.get("batch_id")
            if batch_link and batch_record_id and str(batch_link) != str(batch_record_id):
                continue
            # 按日期范围过滤
            record_date = r.get("record_date")
            if record_date and period_start and period_end:
                date_str = str(record_date)[:10]
                if period_start <= date_str <= period_end:
                    filtered.append(r)
            else:
                filtered.append(r)
        return filtered

    # ============================================================
    # 存活率指标
    # ============================================================

    async def _calc_survival_rate(
        self, object_type: str, object_id: str,
        period_start: str, period_end: str, indicator_code: str
    ) -> float:
        """
        IND-SUR-001~003 存活率
        - 育雏/育成期: 存栏 / 入栏 * 100%
        - 产蛋期: 出栏 / 入栏 * 100%
        """
        if not self.batch_repo:
            return 0.0

        batch = await self.batch_repo.get_by_pk(object_id)
        if not batch:
            return 0.0

        qty_initial = self._to_float(batch.get("quantity_initial", 0))
        if qty_initial <= 0:
            return 0.0

        if indicator_code == "IND-SUR-003":
            # 产蛋期存活率 = 出栏数 / 入栏数 * 100%
            qty_out = self._to_float(batch.get("quantity_out", 0))
            return round(qty_out / qty_initial * 100, 2)
        else:
            # 育雏/育成期存活率 = 存栏数 / 入栏数 * 100%
            qty_current = self._to_float(batch.get("quantity_current", 0))
            return round(qty_current / qty_initial * 100, 2)

    # ============================================================
    # 饲料利用指标
    # ============================================================

    async def _calc_avg_daily_feed(
        self, object_type: str, object_id: str,
        period_start: str, period_end: str, indicator_code: str
    ) -> float:
        """
        IND-FEE-002 平均日耗料 = 总耗料量(kg) / 总动物饲养日 (kg/羽/天)
        = SUM(feed_quantity_kg) / SUM(animal_count)
        """
        if not self.feed_repo:
            return 0.0

        # 获取批次 record_id（用于匹配 Link 字段）
        batch_record_id = await self._get_batch_record_id(object_id)

        all_records = await self.feed_repo.list_all()
        total_feed = 0.0
        total_animal_days = 0.0

        for r in all_records:
            # 按批次过滤（batch 是 Link 字段，值为 record_id）
            batch_link = r.get("batch")
            if batch_link and batch_record_id and str(batch_link) != str(batch_record_id):
                continue

            # 按日期范围过滤
            record_date = r.get("record_date")
            if record_date and period_start and period_end:
                date_str = str(record_date)[:10]
                if not (period_start <= date_str <= period_end):
                    continue

            feed_qty = self._to_float(r.get("feed_quantity_kg", 0))
            animal_count = self._to_float(r.get("animal_count", 0))

            total_feed += feed_qty
            total_animal_days += animal_count

        if total_animal_days <= 0:
            return 0.0

        return round(total_feed / total_animal_days, 4)

    # ============================================================
    # 通用辅助方法
    # ============================================================

    async def _get_batch_record_id(self, batch_no: str) -> Optional[str]:
        """通过 batch_no 获取批次的 Feishu record_id（用于 Link 字段匹配）"""
        if not self.batch_repo:
            return None
        batch = await self.batch_repo.get_by_pk(batch_no)
        if not batch:
            return None
        return batch.get("_record_id")

    def _get_field(self, record: Dict[str, Any], possible_names: List[str]) -> Any:
        """从记录中按多个可能的字段名获取值"""
        for name in possible_names:
            if name in record:
                return record[name]
        return None

    def _to_float(self, value: Any, default: Any = 0.0) -> float:
        """安全转换为浮点数"""
        if value is None:
            return default if default is not None else 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return default if default is not None else 0.0

    def _evaluate_threshold(
        self,
        value: float,
        threshold: Optional[Dict[str, Any]],
    ) -> ThresholdStatus:
        """根据阈值配置评估指标状态"""
        if threshold is None:
            return ThresholdStatus.UNCONFIGURED

        excellent = self._to_float(threshold.get("threshold_excellent"), None)
        good = self._to_float(threshold.get("threshold_good"), None)
        warning = self._to_float(threshold.get("threshold_warning"), None)
        danger = self._to_float(threshold.get("threshold_danger"), None)

        if excellent is not None and value >= excellent:
            return ThresholdStatus.EXCELLENT
        if good is not None and value >= good:
            return ThresholdStatus.GOOD
        if danger is not None and value <= danger:
            return ThresholdStatus.DANGER
        if warning is not None and value <= warning:
            return ThresholdStatus.WARNING
        return ThresholdStatus.GOOD

    def _map_object_type(self, code: str) -> str:
        mapping = {
            "farm": "场",
            "house": "舍",
            "flock": "群",
            "batch": "批次",
            "individual": "个体",
        }
        return mapping.get(code, code)

    def _map_period_type(self, code: str) -> str:
        mapping = {
            "day": "日",
            "week": "周",
            "period": "期",
            "full": "全期",
        }
        return mapping.get(code, code)
