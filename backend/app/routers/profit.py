"""批次利润分析 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from datetime import date

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/profit", tags=["批次利润分析"])


@router.get("/ranking")
async def get_profit_ranking(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    sort_by: Optional[str] = Query("profit_margin", description="profit_margin|gross_profit|roi"),
    breed_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """利润排行榜"""
    profits = await repos.profit.list_all()
    batches_map = {b.get("_record_id"): b for b in await repos.batch.list_all()}
    breeds_map = {b.get("_record_id"): b for b in await repos.breed.list_all()}

    # 日期过滤
    filtered = []
    for pa in profits:
        ad = pa.get("analysis_date")
        if start_date and ad:
            try:
                if date.fromisoformat(str(ad)) < start_date:
                    continue
            except Exception:
                pass
        if end_date and ad:
            try:
                if date.fromisoformat(str(ad)) > end_date:
                    continue
            except Exception:
                pass
        filtered.append(pa)

    # 每个 batch 取最新的分析记录
    from collections import defaultdict
    batch_latest = {}
    for pa in filtered:
        bid = pa.get("batch_id")
        ad = pa.get("analysis_date") or ""
        if bid not in batch_latest or ad > batch_latest[bid].get("analysis_date", ""):
            batch_latest[bid] = pa

    items = list(batch_latest.values())

    # breed 过滤
    if breed_id:
        items = [
            pa for pa in items
            if batches_map.get(str(pa.get("batch_id")), {}).get("breed_id") == breed_id
        ]

    # 排序
    def sort_key(pa):
        if sort_by == "gross_profit":
            return float(pa.get("gross_profit", 0) or 0)
        elif sort_by == "roi":
            tc = float(pa.get("total_cost", 0) or 0)
            return (float(pa.get("gross_profit", 0) or 0) / tc * 100) if tc else 0
        else:
            return float(pa.get("profit_margin", 0) or 0)

    items.sort(key=sort_key, reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]

    data = []
    rank = start + 1
    for pa in page_items:
        batch = batches_map.get(str(pa.get("batch_id")), {})
        breed = breeds_map.get(str(batch.get("breed_id")), {})
        roi = round(float(pa.get("gross_profit", 0) or 0) / float(pa.get("total_cost", 0) or 0) * 100, 2) if pa.get("total_cost") else 0
        data.append({
            "batch_id": pa.get("batch_id"),
            "batch_no": batch.get("batch_no"),
            "breed_name": breed.get("breed_name"),
            "total_revenue": float(pa.get("total_revenue", 0) or 0),
            "total_cost": float(pa.get("total_cost", 0) or 0),
            "gross_profit": float(pa.get("gross_profit", 0) or 0),
            "profit_margin": float(pa.get("profit_margin", 0) or 0),
            "cost_per_bird": float(pa.get("cost_per_bird")) if pa.get("cost_per_bird") else None,
            "revenue_per_bird": float(pa.get("revenue_per_bird")) if pa.get("revenue_per_bird") else None,
            "profit_per_bird": round(float(pa.get("revenue_per_bird") or 0) - float(pa.get("cost_per_bird") or 0), 2) if pa.get("revenue_per_bird") and pa.get("cost_per_bird") else None,
            "roi": roi,
            "rank": rank,
            "analysis_date": str(pa.get("analysis_date")),
        })
        rank += 1

    return paginated_response(data, page, page_size, total)


@router.get("/trend")
async def get_profit_overview(repos: RepositoryFactory = Depends(get_repositories)):
    """利润总览"""
    profits = await repos.profit.list_all()
    # 每个 batch 取最新的分析记录
    from collections import defaultdict
    batch_latest = {}
    for pa in profits:
        bid = pa.get("batch_id")
        ad = pa.get("analysis_date") or ""
        if bid not in batch_latest or ad > batch_latest[bid].get("analysis_date", ""):
            batch_latest[bid] = pa

    latest = list(batch_latest.values())
    total_profit = sum(float(p.get("gross_profit", 0) or 0) for p in latest)
    profitable = sum(1 for p in latest if float(p.get("gross_profit", 0) or 0) > 0)
    loss = sum(1 for p in latest if float(p.get("gross_profit", 0) or 0) <= 0)
    avg_margin = round(sum(float(p.get("profit_margin", 0) or 0) for p in latest) / len(latest), 2) if latest else 0

    return success_response({
        "total_batches": len(latest),
        "total_profit": round(total_profit, 2),
        "profitable_batches": profitable,
        "loss_batches": loss,
        "average_profit_margin": avg_margin,
    })


@router.get("/cost-structure")
async def get_cost_structure(
    batch_id: str = Query(...),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """成本结构分析"""
    costs = await repos.cost.filter_by("batch_id", batch_id)
    cost_type_map = {
        1: "饲料", 2: "疫苗药品", 3: "人工", 4: "折旧", 5: "水电", 6: "其他"
    }
    data = []
    total = 0
    for c in costs:
        data.append({
            "cost_type": c.get("cost_type"),
            "cost_type_text": cost_type_map.get(c.get("cost_type"), "未知"),
            "amount": float(c.get("amount", 0) or 0),
            "quantity": float(c.get("quantity")) if c.get("quantity") else None,
            "unit_cost": float(c.get("unit_cost")) if c.get("unit_cost") else None,
            "period_start": str(c.get("period_start")),
            "period_end": str(c.get("period_end")),
        })
        total += float(c.get("amount", 0) or 0)

    for d in data:
        d["pct"] = round(d["amount"] / total * 100, 2) if total else 0

    return success_response({"batch_id": batch_id, "total_cost": round(total, 2), "structure": data})
