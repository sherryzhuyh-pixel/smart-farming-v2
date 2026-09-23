"""品种管理 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/breeds", tags=["品种管理"])


@router.get("")
async def list_breeds(
    keyword: Optional[str] = Query(None, description="关键字搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询品种列表"""
    breeds = await repos.breed.list_all()

    if keyword:
        kw = keyword.lower()
        breeds = [
            b for b in breeds
            if kw in (b.get("breed_name") or "").lower()
            or kw in (b.get("breed_code") or "").lower()
        ]

    total = len(breeds)
    start = (page - 1) * page_size
    page_items = breeds[start : start + page_size]

    data = [
        {
            "id": b.get("_record_id"),
            "breed_code": b.get("breed_code"),
            "breed_name": b.get("breed_name"),
            "breed_type": b.get("breed_type"),
            "origin": b.get("origin"),
            "description": b.get("description"),
            "avg_weight_male": b.get("avg_weight_male"),
            "avg_weight_female": b.get("avg_weight_female"),
            "avg_egg_rate": b.get("avg_egg_rate"),
            "feed_meat_ratio": b.get("feed_meat_ratio"),
            "survival_rate_std": b.get("survival_rate_std"),
            "daily_gain_std": b.get("daily_gain_std"),
            "created_at": b.get("created_at"),
        }
        for b in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/{breed_id}")
async def get_breed_detail(breed_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """获取品种详情"""
    breed = await repos.breed.get_by_id(breed_id)
    if not breed:
        return error_response(404, "品种不存在")

    return success_response({
        "id": breed.get("_record_id"),
        "breed_code": breed.get("breed_code"),
        "breed_name": breed.get("breed_name"),
        "breed_type": breed.get("breed_type"),
        "origin": breed.get("origin"),
        "description": breed.get("description"),
        "avg_weight_male": breed.get("avg_weight_male"),
        "avg_weight_female": breed.get("avg_weight_female"),
        "avg_egg_rate": breed.get("avg_egg_rate"),
        "feed_meat_ratio": breed.get("feed_meat_ratio"),
        "survival_rate_std": breed.get("survival_rate_std"),
        "daily_gain_std": breed.get("daily_gain_std"),
        "created_at": breed.get("created_at"),
    })


@router.post("")
async def create_breed(data: dict, repos: RepositoryFactory = Depends(get_repositories)):
    """创建品种"""
    breed = await repos.breed.create(data)
    return success_response(breed, "创建成功")


@router.put("/{breed_id}")
async def update_breed(breed_id: str, data: dict, repos: RepositoryFactory = Depends(get_repositories)):
    """更新品种"""
    existing = await repos.breed.get_by_id(breed_id)
    if not existing:
        return error_response(404, "品种不存在")
    updated = await repos.breed.update(breed_id, data)
    return success_response(updated, "更新成功")


@router.delete("/{breed_id}")
async def delete_breed(breed_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """删除品种"""
    existing = await repos.breed.get_by_id(breed_id)
    if not existing:
        return error_response(404, "品种不存在")
    await repos.breed.delete(breed_id)
    return success_response(None, "删除成功")
