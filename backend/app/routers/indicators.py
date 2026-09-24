"""
Indicators Router - /api/v3/indicators/*
指标层 API 路由模块 (S4 Phase 1 适配版)
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel

from app.repositories import RepositoryFactory
from app.schemas.indicators import (
    IndicatorDictionaryOut,
    IndicatorDictionaryCreate,
    IndicatorDictionaryUpdate,
    IndicatorThresholdOut,
    IndicatorThresholdCreate,
    IndicatorThresholdUpdate,
    IndicatorComputationLogOut,
    ComputeRequest,
    ComputeResponse,
    BatchComputeRequest,
    IndicatorHistoryQuery,
    IndicatorHistoryItem,
    IndicatorHistoryResponse,
)
from app.services.indicator_engine import IndicatorEngine


router = APIRouter(prefix="/api/v3/indicators", tags=["Indicators V3"])


# ---- 依赖注入 ----

def get_indicator_repo(request: Request):
    return request.app.state.repositories.indicator_dictionary


def get_threshold_repo(request: Request):
    return request.app.state.repositories.indicator_threshold


def get_computation_log_repo(request: Request):
    return request.app.state.repositories.indicator_computation_log


def get_indicator_engine(request: Request):
    return IndicatorEngine(repositories=request.app.state.repositories)


# ============================================================
# 指标字典接口
# ============================================================

@router.get(
    "",
    response_model=List[IndicatorDictionaryOut],
    summary="指标字典查询",
)
async def list_indicators(
    category: Optional[str] = Query(None, description="分类筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选: P0/P1/P2"),
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(100, ge=1, le=2000, description="返回条数"),
    repo=Depends(get_indicator_repo),
):
    """查询指标字典列表"""
    conditions = []
    if category:
        conditions.append({"field_name": "分类", "operator": "is", "value": [category]})
    if priority:
        conditions.append({"field_name": "优先级", "operator": "is", "value": [priority]})
    if status:
        conditions.append({"field_name": "状态", "operator": "is", "value": [status]})

    structured_filter = {"conjunction": "and", "conditions": conditions} if conditions else None
    result = await repo.list_records_dict(filter_structured=structured_filter, limit=limit)
    return result["records"]


@router.get(
    "/{code}",
    response_model=IndicatorDictionaryOut,
    summary="单个指标详情",
)
async def get_indicator(
    code: str,
    repo=Depends(get_indicator_repo),
):
    """获取单个指标详情"""
    record = await repo.get_by_field("indicator_code", code)
    if not record:
        raise HTTPException(status_code=404, detail=f"指标编码不存在: {code}")
    return record


@router.post(
    "",
    response_model=IndicatorDictionaryOut,
    summary="创建指标字典条目",
)
async def create_indicator(
    data: IndicatorDictionaryCreate,
    repo=Depends(get_indicator_repo),
):
    """创建指标字典条目"""
    existing = await repo.get_by_field("indicator_code", data.indicator_code)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"指标编码已存在: {data.indicator_code}",
        )
    record_id = await repo.create(data.model_dump(exclude_unset=True))
    return await repo.get(record_id)


@router.put(
    "/{code}",
    response_model=IndicatorDictionaryOut,
    summary="更新指标字典条目",
)
async def update_indicator(
    code: str,
    data: IndicatorDictionaryUpdate,
    repo=Depends(get_indicator_repo),
):
    """更新指标字典条目"""
    existing = await repo.get_by_field("indicator_code", code)
    if not existing:
        raise HTTPException(status_code=404, detail=f"指标编码不存在: {code}")
    await repo.update(existing["record_id"], data.model_dump(exclude_unset=True))
    return await repo.get(existing["record_id"])


@router.delete(
    "/{code}",
    summary="删除指标字典条目",
)
async def delete_indicator(
    code: str,
    repo=Depends(get_indicator_repo),
):
    """删除指标字典条目"""
    existing = await repo.get_by_field("indicator_code", code)
    if not existing:
        raise HTTPException(status_code=404, detail=f"指标编码不存在: {code}")
    await repo.delete(existing["record_id"])
    return {"message": f"指标 {code} 已删除"}


# ============================================================
# 指标阈值接口
# ============================================================

@router.get(
    "/{code}/thresholds",
    response_model=List[IndicatorThresholdOut],
    summary="查询指标阈值配置",
)
async def list_indicator_thresholds(
    code: str,
    breed: Optional[str] = Query(None, description="品种筛选"),
    season: Optional[str] = Query(None, description="季节筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    repo=Depends(get_threshold_repo),
):
    """查询指标阈值配置列表"""
    conditions = [{"field_name": "指标编码", "operator": "is", "value": [code]}]
    if breed:
        conditions.append({"field_name": "品种", "operator": "is", "value": [breed]})
    if season:
        conditions.append({"field_name": "季节", "operator": "is", "value": [season]})
    if is_active is not None:
        conditions.append({"field_name": "是否启用", "operator": "is", "value": [str(is_active).lower()]})

    structured_filter = {"conjunction": "and", "conditions": conditions}
    result = await repo.list_records_dict(filter_structured=structured_filter)
    return result["records"]


@router.post(
    "/{code}/thresholds",
    response_model=IndicatorThresholdOut,
    summary="创建指标阈值配置",
)
async def create_indicator_threshold(
    code: str,
    data: IndicatorThresholdCreate,
    repo=Depends(get_threshold_repo),
):
    """创建指标阈值配置"""
    data.indicator_code = code
    record_id = await repo.create(data.model_dump(exclude_unset=True))
    return await repo.get(record_id)


@router.put(
    "/{code}/thresholds/{record_id}",
    response_model=IndicatorThresholdOut,
    summary="更新指标阈值配置",
)
async def update_indicator_threshold(
    code: str,
    record_id: str,
    data: IndicatorThresholdUpdate,
    repo=Depends(get_threshold_repo),
):
    """更新指标阈值配置"""
    await repo.update(record_id, data.model_dump(exclude_unset=True))
    return await repo.get(record_id)


# ============================================================
# 指标计算接口
# ============================================================

@router.post(
    "/compute",
    response_model=ComputeResponse,
    summary="指标实时计算",
)
async def compute_indicators(
    request: ComputeRequest,
    engine=Depends(get_indicator_engine),
):
    """指标实时计算接口"""
    return await engine.compute_batch(request)


@router.post(
    "/batch-compute",
    response_model=List[ComputeResponse],
    summary="批量指标计算",
)
async def batch_compute_indicators(
    request: BatchComputeRequest,
    engine=Depends(get_indicator_engine),
):
    """批量指标计算接口"""
    results = []
    for req in request.requests:
        result = await engine.compute_batch(req)
        results.append(result)
    return results


# ============================================================
# 指标历史查询接口
# ============================================================

@router.get(
    "/{code}/history",
    response_model=IndicatorHistoryResponse,
    summary="指标历史值查询",
)
async def get_indicator_history(
    code: str,
    object_type: Optional[str] = Query(None, description="对象类型"),
    object_id: Optional[str] = Query(None, description="对象ID"),
    period_type: Optional[str] = Query(None, description="周期类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=2000, description="返回条数"),
    repo=Depends(get_computation_log_repo),
):
    """查询指标历史值"""
    conditions = [{"field_name": "指标编码", "operator": "is", "value": [code]}]
    if object_type:
        conditions.append({"field_name": "计算对象类型", "operator": "is", "value": [object_type]})
    if object_id:
        conditions.append({"field_name": "计算对象ID", "operator": "is", "value": [object_id]})
    if period_type:
        conditions.append({"field_name": "周期类型", "operator": "is", "value": [period_type]})

    structured_filter = {"conjunction": "and", "conditions": conditions}
    result = await repo.list_records_dict(filter_structured=structured_filter, limit=limit)
    records = result["records"]

    # 日期范围本地过滤
    if start_date or end_date:
        filtered = []
        for r in records:
            period_start = r.get("period_start", "")
            if start_date and period_start and str(period_start) < start_date:
                continue
            if end_date and period_start and str(period_start) > end_date:
                continue
            filtered.append(r)
        records = filtered

    items = [
        IndicatorHistoryItem(
            indicator_code=r.get("indicator_code", ""),
            indicator_name=r.get("indicator_name", ""),
            object_type=r.get("object_type", ""),
            object_id=r.get("object_id", ""),
            period_type=r.get("period_type", ""),
            period_start=r.get("period_start"),
            period_end=r.get("period_end"),
            computed_value=r.get("computed_value") or 0.0,
            unit=r.get("unit", ""),
            threshold_status=r.get("threshold_status", ""),
            computed_at=r.get("computed_at"),
        )
        for r in records
    ]

    return IndicatorHistoryResponse(items=items, total=len(items))


# ============================================================
# 计算日志查询接口
# ============================================================

@router.get(
    "/logs/computation",
    response_model=List[IndicatorComputationLogOut],
    summary="计算日志查询",
)
async def list_computation_logs(
    indicator_code: Optional[str] = Query(None, description="指标编码筛选"),
    object_type: Optional[str] = Query(None, description="对象类型筛选"),
    is_success: Optional[bool] = Query(None, description="是否成功筛选"),
    limit: int = Query(50, ge=1, le=2000, description="返回条数"),
    repo=Depends(get_computation_log_repo),
):
    """查询计算日志"""
    conditions = []
    if indicator_code:
        conditions.append({"field_name": "指标编码", "operator": "is", "value": [indicator_code]})
    if object_type:
        conditions.append({"field_name": "计算对象类型", "operator": "is", "value": [object_type]})
    if is_success is not None:
        conditions.append({"field_name": "是否成功", "operator": "is", "value": [str(is_success).lower()]})

    structured_filter = {"conjunction": "and", "conditions": conditions} if conditions else None
    result = await repo.list_records_dict(filter_structured=structured_filter, limit=limit)
    return result["records"]
