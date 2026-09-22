"""市场行情 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/market", tags=["市场行情"])


@router.get("/prices")
async def list_market_prices(
    region: Optional[str] = Query(None),
    product_type: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询市场行情列表"""
    records = await repos.market.list_all()
    if region:
        records = [r for r in records if r.get("region") == region]
    if product_type is not None:
        records = [r for r in records if r.get("product_type") == product_type]

    total = len(records)
    records.sort(key=lambda x: x.get("record_date") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = records[start : start + page_size]

    data = [
        {
            "id": r.get("_record_id"),
            "record_date": str(r.get("record_date")),
            "region": r.get("region"),
            "product_type": r.get("product_type"),
            "price": float(r.get("price", 0) or 0),
            "unit": r.get("unit"),
            "price_change": float(r.get("price_change")) if r.get("price_change") else None,
            "price_change_pct": float(r.get("price_change_pct")) if r.get("price_change_pct") else None,
            "source": r.get("source"),
        }
        for r in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.post("/prices")
async def create_market_price(
    data: dict = Body(...),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """创建市场行情记录"""
    record = await repos.market.create({
        "record_date": data.get("record_date"),
        "region": data.get("region"),
        "product_type": data.get("product_type"),
        "price": data.get("price"),
        "unit": data.get("unit"),
        "price_change": data.get("price_change"),
        "price_change_pct": data.get("price_change_pct"),
        "source": data.get("source"),
    })
    return success_response({
        "id": record.get("_record_id"),
        "record_date": str(record.get("record_date")),
        "region": record.get("region"),
        "price": float(record.get("price", 0) or 0),
        "unit": record.get("unit"),
    }, "创建成功")
