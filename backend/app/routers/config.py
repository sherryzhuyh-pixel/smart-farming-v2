"""系统配置 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import SysConfig, SysConfigHistory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/config", tags=["系统配置"])


@router.get("")
def get_config(
    config_key: Optional[str] = Query(None),
    scope_type: Optional[int] = Query(None),
    scope_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """查询系统配置（支持三级作用域读取）"""
    query = db.query(SysConfig)
    if config_key:
        query = query.filter(SysConfig.config_key == config_key)
    if scope_type is not None:
        query = query.filter(SysConfig.scope_type == scope_type)
    if scope_id is not None:
        query = query.filter(SysConfig.scope_id == scope_id)

    items = query.all()
    data = [
        {
            "id": c.id,
            "config_key": c.config_key,
            "config_value": c.config_value,
            "value_type": c.value_type,
            "scope_type": c.scope_type,
            "scope_type_text": "全局" if c.scope_type == 1 else ("养殖场" if c.scope_type == 2 else "批次"),
            "scope_id": c.scope_id,
            "description": c.description,
            "is_editable": c.is_editable,
        }
        for c in items
    ]
    return success_response(data)


@router.post("")
def create_config(data: dict = Body(...), db: Session = Depends(get_db)):
    """创建配置项"""
    config = SysConfig(
        config_key=data.get("config_key"),
        config_value=data.get("config_value"),
        value_type=data.get("value_type", "STRING"),
        scope_type=data.get("scope_type", 1),
        scope_id=data.get("scope_id"),
        description=data.get("description"),
        is_editable=data.get("is_editable", 1),
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return success_response({
        "id": config.id,
        "config_key": config.config_key,
        "config_value": config.config_value,
        "scope_type": config.scope_type,
    }, "创建成功")


@router.put("/{config_id}")
def update_config(config_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    """更新配置项"""
    config = db.query(SysConfig).filter(SysConfig.id == config_id).first()
    if not config:
        return error_response(404, "配置项不存在")

    old_value = config.config_value
    for k, v in data.items():
        if hasattr(config, k) and v is not None:
            setattr(config, k, v)

    # 记录变更历史
    if "config_value" in data and data["config_value"] != old_value:
        history = SysConfigHistory(
            config_id=config_id,
            old_value=old_value,
            new_value=data["config_value"],
            changed_by=data.get("changed_by"),
        )
        db.add(history)

    db.commit()
    db.refresh(config)
    return success_response({
        "id": config.id,
        "config_key": config.config_key,
        "config_value": config.config_value,
    }, "更新成功")


@router.delete("/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    """删除配置项"""
    config = db.query(SysConfig).filter(SysConfig.id == config_id).first()
    if not config:
        return error_response(404, "配置项不存在")
    db.delete(config)
    db.commit()
    return success_response(None, "删除成功")


@router.get("/{config_id}/history")
def get_config_history(
    config_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询配置变更历史"""
    query = db.query(SysConfigHistory).filter(SysConfigHistory.config_id == config_id)
    total = query.count()
    items = query.order_by(desc(SysConfigHistory.changed_at)).offset((page - 1) * page_size).limit(page_size).all()
    data = [
        {
            "id": h.id,
            "config_id": h.config_id,
            "old_value": h.old_value,
            "new_value": h.new_value,
            "changed_by": h.changed_by,
            "changed_at": str(h.changed_at),
        }
        for h in items
    ]
    return paginated_response(data, page, page_size, total)
