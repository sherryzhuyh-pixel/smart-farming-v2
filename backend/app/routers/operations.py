"""养殖操作记录 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/operations", tags=["养殖操作"])


@router.get("")
async def list_operations(
    batch_id: Optional[str] = Query(None, description="批次ID"),
    op_type: Optional[str] = Query(None, description="操作类型"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询操作记录列表"""
    if batch_id:
        records = await repos.operation.filter_by("batch_id", batch_id)
    else:
        records = await repos.operation.list_all()

    if op_type:
        records = [r for r in records if r.get("op_type") == op_type]
    if start_date:
        records = [r for r in records if (r.get("op_date") or "") >= start_date]
    if end_date:
        records = [r for r in records if (r.get("op_date") or "") <= end_date]

    total = len(records)
    records.sort(key=lambda x: x.get("op_date") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = records[start : start + page_size]

    data = [
        {
            "id": r.get("_record_id"),
            "batch_id": r.get("batch_id"),
            "op_type": r.get("op_type"),
            "op_date": str(r.get("op_date")),
            "operator": r.get("operator"),
            "house_id": r.get("house_id"),
            "quantity": r.get("quantity"),
            "remark": r.get("remark"),
            "created_at": r.get("created_at"),
        }
        for r in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/{operation_id}")
async def get_operation_detail(operation_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """获取操作记录详情"""
    record = await repos.operation.get_by_id(operation_id)
    if not record:
        return error_response(404, "操作记录不存在")

    return success_response({
        "id": record.get("_record_id"),
        "batch_id": record.get("batch_id"),
        "op_type": record.get("op_type"),
        "op_date": str(record.get("op_date")),
        "operator": record.get("operator"),
        "house_id": record.get("house_id"),
        "quantity": record.get("quantity"),
        "remark": record.get("remark"),
        "created_at": record.get("created_at"),
    })


@router.post("")
async def create_operation(data: dict, repos: RepositoryFactory = Depends(get_repositories)):
    """创建操作记录"""
    record = await repos.operation.create(data)
    return success_response(record, "创建成功")


@router.put("/{operation_id}")
async def update_operation(operation_id: str, data: dict, repos: RepositoryFactory = Depends(get_repositories)):
    """更新操作记录"""
    existing = await repos.operation.get_by_id(operation_id)
    if not existing:
        return error_response(404, "操作记录不存在")
    updated = await repos.operation.update(operation_id, data)
    return success_response(updated, "更新成功")


@router.delete("/{operation_id}")
async def delete_operation(operation_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """删除操作记录"""
    existing = await repos.operation.get_by_id(operation_id)
    if not existing:
        return error_response(404, "操作记录不存在")
    await repos.operation.delete(operation_id)
    return success_response(None, "删除成功")
