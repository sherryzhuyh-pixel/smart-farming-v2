"""性能偏差看板 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/performance", tags=["性能偏差看板"])


@router.get("/benchmark")
async def list_benchmarks(
    breed_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询基准标准列表"""
    breeds_map = {b.get("_record_id"): b for b in await repos.breed.list_all()}
    benchmarks = await repos.benchmark.list_all()

    if breed_id:
        benchmarks = [b for b in benchmarks if b.get("breed_id") == breed_id]

    total = len(benchmarks)
    benchmarks.sort(key=lambda x: (x.get("breed_id") or "", x.get("age_from") or 0))
    start = (page - 1) * page_size
    page_items = benchmarks[start : start + page_size]

    data = [
        {
            "id": b.get("_record_id"),
            "breed_id": b.get("breed_id"),
            "breed_name": breeds_map.get(str(b.get("breed_id")), {}).get("breed_name"),
            "standard_name": b.get("standard_name"),
            "age_from": b.get("age_from"),
            "age_to": b.get("age_to"),
            "target_weight": float(b.get("target_weight")) if b.get("target_weight") else None,
            "target_daily_gain": float(b.get("target_daily_gain")) if b.get("target_daily_gain") else None,
            "target_feed_meat_ratio": float(b.get("target_feed_meat_ratio")) if b.get("target_feed_meat_ratio") else None,
            "target_survival_rate": float(b.get("target_survival_rate")) if b.get("target_survival_rate") else None,
        }
        for b in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/deviation")
async def list_performance_analysis(
    batch_id: Optional[str] = Query(None),
    analysis_type: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询性能分析记录"""
    batches_map = {b.get("_record_id"): b.get("batch_no") for b in await repos.batch.list_all()}
    records = await repos.performance.list_all()

    if batch_id:
        records = [r for r in records if r.get("batch_id") == batch_id]
    if analysis_type is not None:
        records = [r for r in records if r.get("analysis_type") == analysis_type]

    total = len(records)
    records.sort(key=lambda x: x.get("analysis_date") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = records[start : start + page_size]

    data = [
        {
            "id": r.get("_record_id"),
            "batch_id": r.get("batch_id"),
            "batch_no": batches_map.get(str(r.get("batch_id"))),
            "analysis_type": r.get("analysis_type"),
            "analysis_date": str(r.get("analysis_date")),
            "age_days": r.get("age_days"),
            "actual_weight": float(r.get("actual_weight")) if r.get("actual_weight") else None,
            "target_weight": float(r.get("target_weight")) if r.get("target_weight") else None,
            "weight_deviation_pct": float(r.get("weight_deviation_pct")) if r.get("weight_deviation_pct") else None,
            "actual_daily_gain": float(r.get("actual_daily_gain")) if r.get("actual_daily_gain") else None,
            "target_daily_gain": float(r.get("target_daily_gain")) if r.get("target_daily_gain") else None,
            "daily_gain_deviation_pct": float(r.get("daily_gain_deviation_pct")) if r.get("daily_gain_deviation_pct") else None,
            "actual_feed_meat_ratio": float(r.get("actual_feed_meat_ratio")) if r.get("actual_feed_meat_ratio") else None,
            "target_feed_meat_ratio": float(r.get("target_feed_meat_ratio")) if r.get("target_feed_meat_ratio") else None,
            "fmr_deviation_pct": float(r.get("fmr_deviation_pct")) if r.get("fmr_deviation_pct") else None,
            "actual_survival_rate": float(r.get("actual_survival_rate")) if r.get("actual_survival_rate") else None,
            "target_survival_rate": float(r.get("target_survival_rate")) if r.get("target_survival_rate") else None,
            "survival_deviation_pct": float(r.get("survival_deviation_pct")) if r.get("survival_deviation_pct") else None,
        }
        for r in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/dashboard")
async def get_deviation_summary(
    batch_id: Optional[str] = Query(None),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """获取性能偏差汇总"""
    records = await repos.performance.list_all()
    if batch_id:
        records = [r for r in records if r.get("batch_id") == batch_id]

    records.sort(key=lambda x: x.get("analysis_date") or "", reverse=True)
    records = records[:100]

    if not records:
        return success_response({"message": "暂无性能分析数据"})

    summary = {
        "total_records": len(records),
        "daily_gain": {"positive": 0, "negative": 0, "avg_deviation": 0},
        "survival_rate": {"positive": 0, "negative": 0, "avg_deviation": 0},
        "feed_meat_ratio": {"positive": 0, "negative": 0, "avg_deviation": 0},
    }

    dg_sum = sr_sum = fmr_sum = 0
    dg_count = sr_count = fmr_count = 0
    for r in records:
        dgp = r.get("daily_gain_deviation_pct")
        if dgp is not None:
            v = float(dgp)
            dg_sum += v
            dg_count += 1
            if v >= 0:
                summary["daily_gain"]["positive"] += 1
            else:
                summary["daily_gain"]["negative"] += 1
        srp = r.get("survival_deviation_pct")
        if srp is not None:
            v = float(srp)
            sr_sum += v
            sr_count += 1
            if v >= 0:
                summary["survival_rate"]["positive"] += 1
            else:
                summary["survival_rate"]["negative"] += 1
        fmrp = r.get("fmr_deviation_pct")
        if fmrp is not None:
            v = float(fmrp)
            fmr_sum += v
            fmr_count += 1
            if v <= 0:  # 料肉比越低越好
                summary["feed_meat_ratio"]["positive"] += 1
            else:
                summary["feed_meat_ratio"]["negative"] += 1

    if dg_count:
        summary["daily_gain"]["avg_deviation"] = round(dg_sum / dg_count, 2)
    if sr_count:
        summary["survival_rate"]["avg_deviation"] = round(sr_sum / sr_count, 2)
    if fmr_count:
        summary["feed_meat_ratio"]["avg_deviation"] = round(fmr_sum / fmr_count, 2)

    return success_response(summary)
