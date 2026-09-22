"""环境监控 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/environment", tags=["环境监控"])


@router.get("/records")
async def list_environment_records(
    house_id: Optional[str] = Query(None),
    batch_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询环境参数记录列表"""
    if house_id:
        records = await repos.env_param.filter_by("house_id", house_id)
    elif batch_id:
        records = await repos.env_param.filter_by("batch_id", batch_id)
    else:
        records = await repos.env_param.list_all()

    total = len(records)
    records.sort(key=lambda x: x.get("record_time") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = records[start : start + page_size]

    data = [
        {
            "id": r.get("_record_id"),
            "house_id": r.get("house_id"),
            "batch_id": r.get("batch_id"),
            "record_time": str(r.get("record_time")),
            "temperature": float(r.get("temperature")) if r.get("temperature") else None,
            "humidity": float(r.get("humidity")) if r.get("humidity") else None,
            "ammonia": float(r.get("ammonia")) if r.get("ammonia") else None,
            "co2": float(r.get("co2")) if r.get("co2") else None,
            "light_intensity": float(r.get("light_intensity")) if r.get("light_intensity") else None,
            "ventilation_rate": float(r.get("ventilation_rate")) if r.get("ventilation_rate") else None,
            "device_id": r.get("device_id"),
        }
        for r in page_items
    ]
    return paginated_response(data, page, page_size, total)
