"""批次利润分析 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date

from app.database import get_db
from app.models import ProfitAnalysis, CostAllocation, Batch, Breed
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/profit", tags=["批次利润分析"])


@router.get("/ranking")
def get_profit_ranking(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    sort_by: Optional[str] = Query("profit_margin", description="profit_margin|gross_profit|roi"),
    breed_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """利润排行榜"""
    query = db.query(ProfitAnalysis, Batch, Breed.breed_name).join(Batch, ProfitAnalysis.batch_id == Batch.id).join(Breed, Batch.breed_id == Breed.id)
    if start_date:
        query = query.filter(ProfitAnalysis.analysis_date >= start_date)
    if end_date:
        query = query.filter(ProfitAnalysis.analysis_date <= end_date)
    if breed_id:
        query = query.filter(Batch.breed_id == breed_id)

    # 每个batch取最新的分析记录
    subq = db.query(ProfitAnalysis.batch_id, func.max(ProfitAnalysis.analysis_date).label("max_date")).group_by(ProfitAnalysis.batch_id).subquery()
    query = query.join(subq, (ProfitAnalysis.batch_id == subq.c.batch_id) & (ProfitAnalysis.analysis_date == subq.c.max_date))

    sort_field = {
        "profit_margin": ProfitAnalysis.profit_margin,
        "gross_profit": ProfitAnalysis.gross_profit,
        "roi": func.coalesce(ProfitAnalysis.gross_profit / ProfitAnalysis.total_cost * 100, 0),
    }.get(sort_by, ProfitAnalysis.profit_margin)

    total = query.count()
    items = query.order_by(desc(sort_field)).offset((page - 1) * page_size).limit(page_size).all()

    data = []
    rank = (page - 1) * page_size + 1
    for pa, batch, breed_name in items:
        roi = round(float(pa.gross_profit) / float(pa.total_cost) * 100, 2) if pa.total_cost else 0
        data.append({
            "batch_id": batch.id,
            "batch_no": batch.batch_no,
            "breed_name": breed_name,
            "total_revenue": float(pa.total_revenue),
            "total_cost": float(pa.total_cost),
            "gross_profit": float(pa.gross_profit),
            "profit_margin": float(pa.profit_margin),
            "cost_per_bird": float(pa.cost_per_bird) if pa.cost_per_bird else None,
            "revenue_per_bird": float(pa.revenue_per_bird) if pa.revenue_per_bird else None,
            "profit_per_bird": round(float(pa.revenue_per_bird or 0) - float(pa.cost_per_bird or 0), 2) if pa.revenue_per_bird and pa.cost_per_bird else None,
            "roi": roi,
            "rank": rank,
            "analysis_date": str(pa.analysis_date),
        })
        rank += 1

    return paginated_response(data, page, page_size, total)


@router.get("/trend")
def get_profit_overview(db: Session = Depends(get_db)):
    """利润总览"""
    subq = db.query(ProfitAnalysis.batch_id, func.max(ProfitAnalysis.analysis_date).label("max_date")).group_by(ProfitAnalysis.batch_id).subquery()
    latest = db.query(ProfitAnalysis).join(subq, (ProfitAnalysis.batch_id == subq.c.batch_id) & (ProfitAnalysis.analysis_date == subq.c.max_date)).all()

    total_profit = sum(float(p.gross_profit) for p in latest)
    profitable = sum(1 for p in latest if float(p.gross_profit) > 0)
    loss = sum(1 for p in latest if float(p.gross_profit) <= 0)
    avg_margin = round(sum(float(p.profit_margin) for p in latest) / len(latest), 2) if latest else 0

    return success_response({
        "total_batches": len(latest),
        "total_profit": round(total_profit, 2),
        "profitable_batches": profitable,
        "loss_batches": loss,
        "average_profit_margin": avg_margin,
    })


@router.get("/cost-structure")
def get_cost_structure(
    batch_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """成本结构分析"""
    costs = db.query(CostAllocation).filter(CostAllocation.batch_id == batch_id).all()
    cost_type_map = {
        1: "饲料", 2: "疫苗药品", 3: "人工", 4: "折旧", 5: "水电", 6: "其他"
    }
    data = []
    total = 0
    for c in costs:
        data.append({
            "cost_type": c.cost_type,
            "cost_type_text": cost_type_map.get(c.cost_type, "未知"),
            "amount": float(c.amount),
            "quantity": float(c.quantity) if c.quantity else None,
            "unit_cost": float(c.unit_cost) if c.unit_cost else None,
            "period_start": str(c.period_start),
            "period_end": str(c.period_end),
        })
        total += float(c.amount)

    for d in data:
        d["pct"] = round(d["amount"] / total * 100, 2) if total else 0

    return success_response({"batch_id": batch_id, "total_cost": round(total, 2), "structure": data})
