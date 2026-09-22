"""饲料管理 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/feed", tags=["饲料管理"])


@router.get("/consumption")
async def list_feed_consumption(
    batch_id: Optional[str] = Query(None),
    house_id: Optional[str] = Query(None),
    feed_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询饲料消耗记录列表"""
    if batch_id:
        records = await repos.feed.filter_by("batch_id", batch_id)
    elif house_id:
        records = await repos.feed.filter_by("house_id", house_id)
    else:
        records = await repos.feed.list_all()

    if feed_type:
        records = [r for r in records if r.get("feed_type") == feed_type]

    total = len(records)
    records.sort(key=lambda x: x.get("record_date") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = records[start : start + page_size]

    data = [
        {
            "id": r.get("_record_id"),
            "batch_id": r.get("batch_id"),
            "house_id": r.get("house_id"),
            "record_date": str(r.get("record_date")),
            "feed_type": r.get("feed_type"),
            "feed_quantity": float(r.get("feed_quantity", 0) or 0),
            "actual_consumption": float(r.get("actual_consumption")) if r.get("actual_consumption") else None,
            "waste_amount": float(r.get("waste_amount")) if r.get("waste_amount") else None,
            "avg_consumption_per_bird": float(r.get("avg_consumption_per_bird")) if r.get("avg_consumption_per_bird") else None,
            "feed_meat_ratio_day": float(r.get("feed_meat_ratio_day")) if r.get("feed_meat_ratio_day") else None,
            "cost": float(r.get("cost")) if r.get("cost") else None,
            "recorder": r.get("recorder"),
        }
        for r in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.post("/consumption")
async def create_feed_consumption(
    data: dict = Body(...),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """创建饲料消耗记录"""
    record = await repos.feed.create({
        "batch_id": data.get("batch_id"),
        "house_id": data.get("house_id"),
        "record_date": data.get("record_date"),
        "feed_type": data.get("feed_type"),
        "feed_quantity": data.get("feed_quantity"),
        "actual_consumption": data.get("actual_consumption"),
        "waste_amount": data.get("waste_amount"),
        "avg_consumption_per_bird": data.get("avg_consumption_per_bird"),
        "feed_meat_ratio_day": data.get("feed_meat_ratio_day"),
        "cost": data.get("cost"),
        "recorder": data.get("recorder"),
    })
    return success_response({
        "id": record.get("_record_id"),
        "batch_id": record.get("batch_id"),
        "feed_type": record.get("feed_type"),
        "feed_quantity": float(record.get("feed_quantity", 0) or 0),
        "record_date": str(record.get("record_date")),
    }, "创建成功")
