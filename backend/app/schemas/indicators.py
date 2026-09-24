"""
Indicators Schemas - 指标层 Pydantic 模型
"""
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ThresholdStatus(str, Enum):
    EXCELLENT = "优良"
    GOOD = "良好"
    WARNING = "警告"
    DANGER = "危险"
    UNCONFIGURED = "未配置"


# ============================================================
# 指标字典模型
# ============================================================

class IndicatorDictionaryBase(BaseModel):
    indicator_code: str = Field(..., description="指标编码")
    indicator_name_cn: Optional[str] = Field(None, description="中文名称")
    indicator_name_en: Optional[str] = Field(None, description="英文名称")
    category: Optional[str] = Field(None, description="分类")
    formula: Optional[str] = Field(None, description="计算公式")
    numerator: Optional[str] = Field(None, description="分子")
    denominator: Optional[str] = Field(None, description="分母")
    definition_note: Optional[str] = Field(None, description="口径说明")
    time_window: Optional[str] = Field(None, description="时间窗")
    object_dimension: Optional[str] = Field(None, description="对象维度")
    unit: Optional[str] = Field(None, description="单位")
    value_range: Optional[str] = Field(None, description="值域")
    threshold_excellent: Optional[float] = Field(None, description="阈值优良")
    threshold_minimum: Optional[float] = Field(None, description="阈值底线")
    data_sources: Optional[str] = Field(None, description="数据来源")
    collection_frequency: Optional[str] = Field(None, description="采集频率")
    version: Optional[str] = Field(None, description="版本")
    priority: Optional[str] = Field(None, description="优先级")
    status: Optional[str] = Field(None, description="状态")


class IndicatorDictionaryCreate(IndicatorDictionaryBase):
    pass


class IndicatorDictionaryUpdate(BaseModel):
    indicator_name_cn: Optional[str] = None
    indicator_name_en: Optional[str] = None
    category: Optional[str] = None
    formula: Optional[str] = None
    numerator: Optional[str] = None
    denominator: Optional[str] = None
    definition_note: Optional[str] = None
    time_window: Optional[str] = None
    object_dimension: Optional[str] = None
    unit: Optional[str] = None
    value_range: Optional[str] = None
    threshold_excellent: Optional[float] = None
    threshold_minimum: Optional[float] = None
    data_sources: Optional[str] = None
    collection_frequency: Optional[str] = None
    version: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class IndicatorDictionaryOut(IndicatorDictionaryBase):
    record_id: Optional[str] = Field(None, alias="record_id")

    class Config:
        populate_by_name = True


# ============================================================
# 指标阈值模型
# ============================================================

class IndicatorThresholdBase(BaseModel):
    indicator_code: str = Field(..., description="指标编码")
    breed: Optional[str] = Field(None, description="品种")
    season: Optional[str] = Field(None, description="季节")
    farm_area: Optional[str] = Field(None, description="场区")
    threshold_excellent: Optional[float] = Field(None, description="阈值优良")
    threshold_good: Optional[float] = Field(None, description="阈值良好")
    threshold_warning: Optional[float] = Field(None, description="阈值警告")
    threshold_danger: Optional[float] = Field(None, description="阈值危险")
    effective_date: Optional[str] = Field(None, description="生效日期")
    expiry_date: Optional[str] = Field(None, description="失效日期")
    is_active: Optional[bool] = Field(None, description="是否启用")
    remark: Optional[str] = Field(None, description="备注")


class IndicatorThresholdCreate(IndicatorThresholdBase):
    pass


class IndicatorThresholdUpdate(BaseModel):
    breed: Optional[str] = None
    season: Optional[str] = None
    farm_area: Optional[str] = None
    threshold_excellent: Optional[float] = None
    threshold_good: Optional[float] = None
    threshold_warning: Optional[float] = None
    threshold_danger: Optional[float] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    is_active: Optional[bool] = None
    remark: Optional[str] = None


class IndicatorThresholdOut(IndicatorThresholdBase):
    record_id: Optional[str] = Field(None, alias="record_id")

    class Config:
        populate_by_name = True


# ============================================================
# 计算请求/响应模型
# ============================================================

class ComputeRequest(BaseModel):
    indicator_codes: List[str] = Field(..., description="指标编码列表")
    object_type: str = Field(..., description="对象类型: farm/house/flock/batch/individual")
    object_id: str = Field(..., description="对象ID")
    period_type: str = Field(..., description="周期类型: day/week/period/full")
    period_start: str = Field(..., description="周期开始 YYYY-MM-DD")
    period_end: str = Field(..., description="周期结束 YYYY-MM-DD")


class ComputeResult(BaseModel):
    indicator_code: str
    indicator_name: str
    value: float
    unit: str
    threshold_status: ThresholdStatus
    formula_applied: str
    data_sources: List[str]
    computed_at: datetime
    compute_duration_ms: int


class ComputeResponse(BaseModel):
    results: List[ComputeResult]
    total_duration_ms: int
    success_count: int
    fail_count: int


class BatchComputeRequest(BaseModel):
    requests: List[ComputeRequest]


# ============================================================
# 历史查询模型
# ============================================================

class IndicatorHistoryQuery(BaseModel):
    indicator_code: str
    object_type: Optional[str] = None
    object_id: Optional[str] = None
    period_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class IndicatorHistoryItem(BaseModel):
    indicator_code: str
    indicator_name: str
    object_type: str
    object_id: str
    period_type: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    computed_value: float
    unit: str
    threshold_status: str
    computed_at: Optional[str] = None


class IndicatorHistoryResponse(BaseModel):
    items: List[IndicatorHistoryItem]
    total: int


# ============================================================
# 计算日志模型
# ============================================================

class IndicatorComputationLogOut(BaseModel):
    indicator_code: str
    indicator_name: Optional[str] = None
    object_type: Optional[str] = None
    object_id: Optional[str] = None
    period_type: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    computed_value: Optional[float] = None
    unit: Optional[str] = None
    threshold_status: Optional[str] = None
    formula_applied: Optional[str] = None
    data_sources: Optional[str] = None
    compute_duration_ms: Optional[int] = None
    computed_at: Optional[str] = None
    is_success: Optional[bool] = None
    error_message: Optional[str] = None
    record_id: Optional[str] = Field(None, alias="record_id")

    class Config:
        populate_by_name = True
