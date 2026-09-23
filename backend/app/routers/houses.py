"""鸡舍管理 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/houses", tags=["鸡舍管理"])


@router.get("")
async def list_houses(
    status: Optional[int] = Query(None, description="状态"),
    keyword: Optional[str] = Query(None, description="关键字搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询鸡舍列表"""
    houses = await repos.house.list_all()

    if status is not None:
        houses = [h for h in houses if h.get("status") == status]
    if keyword:
        kw = keyword.lower()
        houses = [
            h for h in houses
            if kw in (h.get("house_name") or "").lower()
            or kw in (h.get("house_code") or "").lower()
            or kw in (h.get("location") or "").lower()
        ]

    total = len(houses)
    start = (page - 1) * page_size
    page_items = houses[start : start + page_size]

    data = [
        {
            "id": h.get("_record_id"),
            "house_code": h.get("house_code"),
            "house_name": h.get("house_name"),
            "house_type": h.get("house_type"),
            "area_sqm": h.get("area_sqm"),
            "capacity": h.get("capacity"),
            "location": h.get("location"),
            "env_device_id": h.get("env_device_id"),
            "camera_ids": h.get("camera_ids"),
            "status": h.get("status"),
            "created_at": h.get("created_at"),
        }
        for h in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/{house_id}")
async def get_house_detail(house_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """获取鸡舍详情"""
    house = await repos.house.get_by_id(house_id)
    if not house:
        return error_response(404, "鸡舍不存在")

    return success_response({
        "id": house.get("_record_id"),
        "house_code": house.get("house_code"),
        "house_name": house.get("house_name"),
        "house_type": house.get("house_type"),
        "area_sqm": house.get("area_sqm"),
        "capacity": house.get("capacity"),
        "location": house.get("location"),
        "env_device_id": house.get("env_device_id"),
        "camera_ids": house.get("camera_ids"),
        "status": house.get("status"),
        "created_at": house.get("created_at"),
    })


@router.post("")
async def create_house(data: dict, repos: RepositoryFactory = Depends(get_repositories)):
    """创建鸡舍"""
    house = await repos.house.create(data)
    return success_response(house, "创建成功")


@router.put("/{house_id}")
async def update_house(house_id: str, data: dict, repos: RepositoryFactory = Depends(get_repositories)):
    """更新鸡舍"""
    existing = await repos.house.get_by_id(house_id)
    if not existing:
        return error_response(404, "鸡舍不存在")
    updated = await repos.house.update(house_id, data)
    return success_response(updated, "更新成功")


@router.delete("/{house_id}")
async def delete_house(house_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """删除鸡舍"""
    existing = await repos.house.get_by_id(house_id)
    if not existing:
        return error_response(404, "鸡舍不存在")
    await repos.house.delete(house_id)
    return success_response(None, "删除成功")
