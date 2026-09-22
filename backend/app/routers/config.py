"""系统配置 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/config", tags=["系统配置"])


@router.get("")
async def get_config(
    config_key: Optional[str] = Query(None),
    scope_type: Optional[int] = Query(None),
    scope_id: Optional[str] = Query(None),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询系统配置（支持三级作用域读取）"""
    items = await repos.sys_config.list_all()
    filtered = []
    for c in items:
        if config_key and c.get("config_key") != config_key:
            continue
        if scope_type is not None and c.get("scope_type") != scope_type:
            continue
        if scope_id is not None and c.get("scope_id") != scope_id:
            continue
        filtered.append(c)

    data = [
        {
            "id": c.get("_record_id"),
            "config_key": c.get("config_key"),
            "config_value": c.get("config_value"),
            "value_type": c.get("value_type"),
            "scope_type": c.get("scope_type"),
            "scope_type_text": "全局" if c.get("scope_type") == 1 else ("养殖场" if c.get("scope_type") == 2 else "批次"),
            "scope_id": c.get("scope_id"),
            "description": c.get("description"),
            "is_editable": c.get("is_editable"),
        }
        for c in filtered
    ]
    return success_response(data)


@router.post("")
async def create_config(data: dict = Body(...), repos: RepositoryFactory = Depends(get_repositories)):
    """创建配置项"""
    record = await repos.sys_config.create({
        "config_key": data.get("config_key"),
        "config_value": data.get("config_value"),
        "value_type": data.get("value_type", "STRING"),
        "scope_type": data.get("scope_type", 1),
        "scope_id": data.get("scope_id"),
        "description": data.get("description"),
        "is_editable": data.get("is_editable", 1),
    })
    return success_response({
        "id": record.get("_record_id"),
        "config_key": record.get("config_key"),
        "config_value": record.get("config_value"),
        "scope_type": record.get("scope_type"),
    }, "创建成功")


@router.put("/{config_id}")
async def update_config(config_id: str, data: dict = Body(...), repos: RepositoryFactory = Depends(get_repositories)):
    """更新配置项"""
    config = await repos.sys_config.get_by_id(config_id)
    if not config:
        return error_response(404, "配置项不存在")

    old_value = config.get("config_value")
    update_data = {k: v for k, v in data.items() if v is not None}
    updated = await repos.sys_config.update(config_id, update_data)

    # 记录变更历史
    if "config_value" in data and data["config_value"] != old_value:
        try:
            await repos.sys_config_history.create({
                "config_id": config_id,
                "old_value": old_value,
                "new_value": data["config_value"],
                "changed_by": data.get("changed_by"),
            })
        except Exception:
            pass  # 历史记录失败不影响主流程

    return success_response({
        "id": updated.get("_record_id"),
        "config_key": updated.get("config_key"),
        "config_value": updated.get("config_value"),
    }, "更新成功")


@router.delete("/{config_id}")
async def delete_config(config_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """删除配置项"""
    config = await repos.sys_config.get_by_id(config_id)
    if not config:
        return error_response(404, "配置项不存在")
    await repos.sys_config.delete(config_id)
    return success_response(None, "删除成功")


@router.get("/{config_id}/history")
async def get_config_history(
    config_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询配置变更历史"""
    histories = await repos.sys_config_history.list_all()
    histories = [h for h in histories if h.get("config_id") == config_id]
    total = len(histories)
    histories.sort(key=lambda x: x.get("changed_at") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = histories[start : start + page_size]

    data = [
        {
            "id": h.get("_record_id"),
            "config_id": h.get("config_id"),
            "old_value": h.get("old_value"),
            "new_value": h.get("new_value"),
            "changed_by": h.get("changed_by"),
            "changed_at": str(h.get("changed_at")),
        }
        for h in page_items
    ]
    return paginated_response(data, page, page_size, total)
