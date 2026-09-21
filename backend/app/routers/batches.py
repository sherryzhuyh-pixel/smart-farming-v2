"""批次全生命周期 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date

from app.database import get_db
from app.models import Batch, Breed, House, AnimalIndividual, GrowthRecord, HealthRecord, BreedingOperation, FeedConsumption
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/batches", tags=["批次管理"])


@router.get("")
def list_batches(
    status: Optional[int] = Query(None, description="批次状态"),
    breed_id: Optional[int] = Query(None, description="品种ID"),
    house_id: Optional[int] = Query(None, description="鸡舍ID"),
    keyword: Optional[str] = Query(None, description="关键字搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询批次列表"""
    query = db.query(Batch, Breed.breed_name, House.house_name).join(Breed, Batch.breed_id == Breed.id).join(House, Batch.house_id == House.id)
    if status is not None:
        query = query.filter(Batch.status == status)
    if breed_id is not None:
        query = query.filter(Batch.breed_id == breed_id)
    if house_id is not None:
        query = query.filter(Batch.house_id == house_id)
    if keyword:
        query = query.filter(
            (Batch.batch_no.contains(keyword)) |
            (Batch.batch_name.contains(keyword)) |
            (Batch.responsible_person.contains(keyword))
        )
    total = query.count()
    items = query.order_by(desc(Batch.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    data = []
    for b, breed_name, house_name in items:
        data.append({
            "id": b.id,
            "batch_no": b.batch_no,
            "batch_name": b.batch_name,
            "breed_id": b.breed_id,
            "breed_name": breed_name,
            "house_id": b.house_id,
            "house_name": house_name,
            "quantity_initial": b.quantity_initial,
            "quantity_current": b.quantity_current,
            "survival_rate": round(b.quantity_current / b.quantity_initial * 100, 2) if b.quantity_initial else 0,
            "date_in": str(b.date_in) if b.date_in else None,
            "date_out": str(b.date_out) if b.date_out else None,
            "age_days": (date.today() - b.date_in).days + b.age_day_in if b.date_in else None,
            "status": b.status,
            "responsible_person": b.responsible_person,
            "pilot_flag": b.pilot_flag,
        })
    return paginated_response(data, page, page_size, total)


@router.get("/{batch_id}")
def get_batch_detail(batch_id: int, db: Session = Depends(get_db)):
    """获取批次详情"""
    result = db.query(Batch, Breed, House).join(Breed, Batch.breed_id == Breed.id).join(House, Batch.house_id == House.id).filter(Batch.id == batch_id).first()
    if not result:
        return error_response(404, "批次不存在")
    b, breed, house = result
    age_days = (date.today() - b.date_in).days + b.age_day_in if b.date_in else None
    survival_rate = round(b.quantity_current / b.quantity_initial * 100, 2) if b.quantity_initial else 0
    return success_response({
        "id": b.id,
        "batch_no": b.batch_no,
        "batch_name": b.batch_name,
        "breed": {"id": breed.id, "breed_name": breed.breed_name, "breed_code": breed.breed_code},
        "house": {"id": house.id, "house_name": house.house_name, "house_code": house.house_code},
        "quantity_initial": b.quantity_initial,
        "quantity_current": b.quantity_current,
        "survival_rate": survival_rate,
        "date_in": str(b.date_in) if b.date_in else None,
        "date_out": str(b.date_out) if b.date_out else None,
        "age_day_in": b.age_day_in,
        "age_days": age_days,
        "source_type": b.source_type,
        "status": b.status,
        "responsible_person": b.responsible_person,
        "pilot_flag": b.pilot_flag,
    })


@router.get("/{batch_id}/lifecycle")
def get_batch_lifecycle(batch_id: int, db: Session = Depends(get_db)):
    """批次全生命周期数据聚合"""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        return error_response(404, "批次不存在")

    # 个体统计
    individual_stats = db.query(AnimalIndividual.status, func.count(AnimalIndividual.id)).filter(AnimalIndividual.batch_id == batch_id).group_by(AnimalIndividual.status).all()
    status_distribution = {f"status_{s}": c for s, c in individual_stats}

    # 健康记录（死淘）
    mortality = db.query(func.count(HealthRecord.id)).filter(HealthRecord.batch_id == batch_id, HealthRecord.mortality_flag == 1).scalar() or 0
    cull_reasons = db.query(HealthRecord.event_name, func.count(HealthRecord.id)).filter(HealthRecord.batch_id == batch_id, HealthRecord.mortality_flag == 1).group_by(HealthRecord.event_name).all()

    # 最近操作
    recent_ops = db.query(BreedingOperation).filter(BreedingOperation.batch_id == batch_id).order_by(desc(BreedingOperation.op_date)).limit(10).all()

    # 饲料消耗汇总
    feed_total = db.query(func.sum(FeedConsumption.feed_quantity)).filter(FeedConsumption.batch_id == batch_id).scalar() or 0

    return success_response({
        "batch_id": batch_id,
        "batch_no": batch.batch_no,
        "individual_count": {
            "total": sum(c for _, c in individual_stats),
            "status_distribution": status_distribution,
        },
        "mortality": {
            "total": mortality,
            "reasons": [{"reason": r, "count": c} for r, c in cull_reasons],
        },
        "recent_operations": [
            {"id": o.id, "op_type": o.op_type, "op_date": str(o.op_date), "operator": o.operator, "remark": o.remark}
            for o in recent_ops
        ],
        "feed_total": float(feed_total) if feed_total else 0,
    })


@router.get("/{batch_id}/growth-summary")
def get_batch_growth_summary(batch_id: int, db: Session = Depends(get_db)):
    """批次生长汇总"""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        return error_response(404, "批次不存在")

    # 最新体重统计
    subq = db.query(GrowthRecord.animal_id, func.max(GrowthRecord.record_date).label("max_date")).filter(GrowthRecord.batch_id == batch_id).group_by(GrowthRecord.animal_id).subquery()
    latest_weights = db.query(GrowthRecord.weight).join(subq, (GrowthRecord.animal_id == subq.c.animal_id) & (GrowthRecord.record_date == subq.c.max_date)).all()
    weights = [float(w[0]) for w in latest_weights if w[0] is not None]

    if weights:
        avg_weight = sum(weights) / len(weights)
        min_weight = min(weights)
        max_weight = max(weights)
        # 简单标准差
        variance = sum((w - avg_weight) ** 2 for w in weights) / len(weights)
        std_weight = variance ** 0.5
        uniformity = round((1 - std_weight / avg_weight) * 100, 2) if avg_weight else 0
    else:
        avg_weight = min_weight = max_weight = std_weight = uniformity = 0

    # 生长记录数量
    record_count = db.query(func.count(GrowthRecord.id)).filter(GrowthRecord.batch_id == batch_id).scalar() or 0

    return success_response({
        "batch_id": batch_id,
        "batch_no": batch.batch_no,
        "sample_size": len(weights),
        "avg_weight": round(avg_weight, 3),
        "min_weight": round(min_weight, 3),
        "max_weight": round(max_weight, 3),
        "std_weight": round(std_weight, 3),
        "uniformity": uniformity,
        "record_count": record_count,
    })


@router.get("/{batch_id}/performance")
def get_batch_performance(batch_id: int, db: Session = Depends(get_db)):
    """批次性能偏差"""
    batch = db.query(Batch, Breed).join(Breed, Batch.breed_id == Breed.id).filter(Batch.id == batch_id).first()
    if not batch:
        return error_response(404, "批次不存在")
    b, breed = batch

    # 成活率
    survival_rate = round(b.quantity_current / b.quantity_initial * 100, 2) if b.quantity_initial else 0
    survival_deviation = round(survival_rate - (float(breed.survival_rate_std) if breed.survival_rate_std else 0), 2)

    # 日增重（基于最近两次称重）
    from sqlalchemy import asc
    growth_records = db.query(GrowthRecord).filter(GrowthRecord.batch_id == batch_id).order_by(asc(GrowthRecord.record_date)).all()
    if len(growth_records) >= 2:
        first = growth_records[0]
        last = growth_records[-1]
        days_diff = (last.record_date - first.record_date).days
        weight_diff = float(last.weight) - float(first.weight)
        actual_daily_gain = round(weight_diff / days_diff, 3) if days_diff > 0 else 0
    else:
        actual_daily_gain = 0
    std_daily_gain = float(breed.daily_gain_std) if breed.daily_gain_std else 0
    daily_gain_deviation = round(actual_daily_gain - std_daily_gain, 3)
    daily_gain_deviation_pct = round(daily_gain_deviation / std_daily_gain * 100, 2) if std_daily_gain else 0

    # 料肉比
    feed_total = db.query(func.sum(FeedConsumption.feed_quantity)).filter(FeedConsumption.batch_id == batch_id).scalar() or 0
    weight_gain = float(growth_records[-1].weight) - float(growth_records[0].weight) if len(growth_records) >= 2 else 0
    actual_fmr = round(float(feed_total) / weight_gain, 3) if weight_gain > 0 else 0
    std_fmr = float(breed.feed_meat_ratio) if breed.feed_meat_ratio else 0
    fmr_deviation = round(actual_fmr - std_fmr, 3)

    return success_response({
        "batch_id": batch_id,
        "batch_no": b.batch_no,
        "survival_rate": {
            "actual": survival_rate,
            "standard": float(breed.survival_rate_std) if breed.survival_rate_std else None,
            "deviation": survival_deviation,
        },
        "daily_gain": {
            "actual": actual_daily_gain,
            "standard": std_daily_gain,
            "deviation": daily_gain_deviation,
            "deviation_pct": daily_gain_deviation_pct,
        },
        "feed_meat_ratio": {
            "actual": actual_fmr,
            "standard": std_fmr,
            "deviation": fmr_deviation,
        },
    })


@router.get("/{batch_id}/profit")
def get_batch_profit(batch_id: int, db: Session = Depends(get_db)):
    """批次利润分析"""
    from app.models import ProfitAnalysis, CostAllocation, FinancialTransaction
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        return error_response(404, "批次不存在")

    profit = db.query(ProfitAnalysis).filter(ProfitAnalysis.batch_id == batch_id).order_by(desc(ProfitAnalysis.analysis_date)).first()
    if profit:
        return success_response({
            "batch_id": batch_id,
            "batch_no": batch.batch_no,
            "total_revenue": float(profit.total_revenue),
            "total_cost": float(profit.total_cost),
            "gross_profit": float(profit.gross_profit),
            "profit_margin": float(profit.profit_margin),
            "cost_per_bird": float(profit.cost_per_bird) if profit.cost_per_bird else None,
            "revenue_per_bird": float(profit.revenue_per_bird) if profit.revenue_per_bird else None,
            "analysis_date": str(profit.analysis_date),
        })

    # 动态计算
    total_revenue = db.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.batch_id == batch_id, FinancialTransaction.transaction_type == 1
    ).scalar() or 0
    total_cost = db.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.batch_id == batch_id, FinancialTransaction.transaction_type == 2
    ).scalar() or 0
    gross_profit = float(total_revenue) - float(total_cost)
    profit_margin = round(gross_profit / float(total_revenue) * 100, 2) if total_revenue else 0
    bird_count = batch.quantity_initial or 1

    return success_response({
        "batch_id": batch_id,
        "batch_no": batch.batch_no,
        "total_revenue": float(total_revenue),
        "total_cost": float(total_cost),
        "gross_profit": round(gross_profit, 2),
        "profit_margin": profit_margin,
        "cost_per_bird": round(float(total_cost) / bird_count, 2),
        "revenue_per_bird": round(float(total_revenue) / bird_count, 2),
        "profit_per_bird": round(gross_profit / bird_count, 2),
        "computed": True,
    })
