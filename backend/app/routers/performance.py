"""性能偏差看板 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import PerformanceAnalysis, BenchmarkStandard, Batch, Breed
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/performance", tags=["性能偏差看板"])


@router.get("/benchmark")
def list_benchmarks(
    breed_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询基准标准列表"""
    query = db.query(BenchmarkStandard, Breed.breed_name).join(Breed, BenchmarkStandard.breed_id == Breed.id)
    if breed_id:
        query = query.filter(BenchmarkStandard.breed_id == breed_id)
    total = query.count()
    items = query.order_by(BenchmarkStandard.breed_id, BenchmarkStandard.age_from).offset((page - 1) * page_size).limit(page_size).all()
    data = [
        {
            "id": b.id,
            "breed_id": b.breed_id,
            "breed_name": breed_name,
            "standard_name": b.standard_name,
            "age_from": b.age_from,
            "age_to": b.age_to,
            "target_weight": float(b.target_weight) if b.target_weight else None,
            "target_daily_gain": float(b.target_daily_gain) if b.target_daily_gain else None,
            "target_feed_meat_ratio": float(b.target_feed_meat_ratio) if b.target_feed_meat_ratio else None,
            "target_survival_rate": float(b.target_survival_rate) if b.target_survival_rate else None,
        }
        for b, breed_name in items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/deviation")
def list_performance_analysis(
    batch_id: Optional[int] = Query(None),
    analysis_type: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询性能分析记录"""
    query = db.query(PerformanceAnalysis, Batch.batch_no).join(Batch, PerformanceAnalysis.batch_id == Batch.id)
    if batch_id:
        query = query.filter(PerformanceAnalysis.batch_id == batch_id)
    if analysis_type is not None:
        query = query.filter(PerformanceAnalysis.analysis_type == analysis_type)
    total = query.count()
    items = query.order_by(desc(PerformanceAnalysis.analysis_date)).offset((page - 1) * page_size).limit(page_size).all()
    data = [
        {
            "id": pa.id,
            "batch_id": pa.batch_id,
            "batch_no": batch_no,
            "analysis_type": pa.analysis_type,
            "analysis_date": str(pa.analysis_date),
            "age_days": pa.age_days,
            "actual_weight": float(pa.actual_weight) if pa.actual_weight else None,
            "target_weight": float(pa.target_weight) if pa.target_weight else None,
            "weight_deviation_pct": float(pa.weight_deviation_pct) if pa.weight_deviation_pct else None,
            "actual_daily_gain": float(pa.actual_daily_gain) if pa.actual_daily_gain else None,
            "target_daily_gain": float(pa.target_daily_gain) if pa.target_daily_gain else None,
            "daily_gain_deviation_pct": float(pa.daily_gain_deviation_pct) if pa.daily_gain_deviation_pct else None,
            "actual_feed_meat_ratio": float(pa.actual_feed_meat_ratio) if pa.actual_feed_meat_ratio else None,
            "target_feed_meat_ratio": float(pa.target_feed_meat_ratio) if pa.target_feed_meat_ratio else None,
            "fmr_deviation_pct": float(pa.fmr_deviation_pct) if pa.fmr_deviation_pct else None,
            "actual_survival_rate": float(pa.actual_survival_rate) if pa.actual_survival_rate else None,
            "target_survival_rate": float(pa.target_survival_rate) if pa.target_survival_rate else None,
            "survival_deviation_pct": float(pa.survival_deviation_pct) if pa.survival_deviation_pct else None,
        }
        for pa, batch_no in items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/dashboard")
def get_deviation_summary(
    batch_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """获取性能偏差汇总"""
    query = db.query(PerformanceAnalysis)
    if batch_id:
        query = query.filter(PerformanceAnalysis.batch_id == batch_id)
    records = query.order_by(desc(PerformanceAnalysis.analysis_date)).limit(100).all()

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
        if r.daily_gain_deviation_pct is not None:
            dg_sum += float(r.daily_gain_deviation_pct)
            dg_count += 1
            if float(r.daily_gain_deviation_pct) >= 0:
                summary["daily_gain"]["positive"] += 1
            else:
                summary["daily_gain"]["negative"] += 1
        if r.survival_deviation_pct is not None:
            sr_sum += float(r.survival_deviation_pct)
            sr_count += 1
            if float(r.survival_deviation_pct) >= 0:
                summary["survival_rate"]["positive"] += 1
            else:
                summary["survival_rate"]["negative"] += 1
        if r.fmr_deviation_pct is not None:
            fmr_sum += float(r.fmr_deviation_pct)
            fmr_count += 1
            if float(r.fmr_deviation_pct) <= 0:  # 料肉比越低越好
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
