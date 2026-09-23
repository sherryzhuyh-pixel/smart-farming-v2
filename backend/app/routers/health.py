"""健康管理 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/health", tags=["健康管理"])


@router.get("/records")
async def list_health_records(
    batch_id: Optional[str] = Query(None),
    animal_id: Optional[str] = Query(None),
    record_type: Optional[int] = Query(None),
    mortality_flag: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询健康记录列表"""
    if batch_id:
        records = await repos.health.filter_by("batch_id", batch_id)
    elif animal_id:
        records = await repos.health.filter_by("animal_id", animal_id)
    else:
        records = await repos.health.list_all()

    if record_type is not None:
        records = [r for r in records if r.get("record_type") == record_type]
    if mortality_flag is not None:
        records = [r for r in records if r.get("mortality_flag") == mortality_flag]

    total = len(records)
    records.sort(key=lambda x: x.get("record_date") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = records[start : start + page_size]

    data = [
        {
            "id": r.get("_record_id"),
            "record_type": r.get("record_type"),
            "animal_id": r.get("animal_id"),
            "batch_id": r.get("batch_id"),
            "record_date": str(r.get("record_date")),
            "event_name": r.get("event_name"),
            "drug_name": r.get("drug_name"),
            "drug_dosage": r.get("drug_dosage"),
            "route": r.get("route"),
            "symptom": r.get("symptom"),
            "diagnosis": r.get("diagnosis"),
            "treatment_result": r.get("treatment_result"),
            "veterinarian": r.get("veterinarian"),
            "cost": float(r.get("cost")) if r.get("cost") else None,
            "mortality_flag": r.get("mortality_flag"),
        }
        for r in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.post("/records")
async def create_health_record(data: dict, repos: RepositoryFactory = Depends(get_repositories)):
    """创建健康记录"""
    record = await repos.health.create(data)
    return success_response(record, "创建成功")
