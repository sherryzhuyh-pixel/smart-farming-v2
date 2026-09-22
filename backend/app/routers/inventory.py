"""库存管理 API (Feishu Base 版本)"""
from typing import Optional
import asyncio
from fastapi import APIRouter, Depends, Query, Body
from datetime import date, timedelta

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

# 进程级库存锁（防止并发超卖）
_inventory_locks: dict[str, asyncio.Lock] = {}


def _get_inv_lock(inventory_id: str) -> asyncio.Lock:
    """获取指定库存物料的锁"""
    if inventory_id not in _inventory_locks:
        _inventory_locks[inventory_id] = asyncio.Lock()
    return _inventory_locks[inventory_id]

router = APIRouter(prefix="/inventory", tags=["库存管理"])


category_map = {1: "饲料", 2: "药品", 3: "疫苗", 4: "设备", 5: "种鸡", 6: "其他"}
status_map = {1: "正常", 2: "临期", 3: "过期", 4: "冻结"}
trans_type_map = {1: "入库", 2: "出库", 3: "盘点调整", 4: "损耗"}
ref_type_map = {1: "采购", 2: "销售", 3: "领用", 4: "调拨", 5: "孵化"}


@router.get("")
async def list_inventory(
    item_category: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    low_stock: Optional[bool] = Query(None),
    near_expiry: Optional[bool] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询库存列表"""
    items = await repos.inventory.list_all()

    filtered = []
    for inv in items:
        if item_category is not None and inv.get("item_category") != item_category:
            continue
        if status is not None and inv.get("status") != status:
            continue
        qty = float(inv.get("quantity", 0) or 0)
        safety = float(inv.get("safety_stock")) if inv.get("safety_stock") is not None else None
        if low_stock and (safety is None or qty >= safety):
            continue
        expiry = inv.get("expiry_date")
        if near_expiry:
            if not expiry:
                continue
            try:
                days = (date.fromisoformat(str(expiry)) - date.today()).days
                if days > 30 or days < 0:
                    continue
            except Exception:
                continue
        if keyword:
            kw = keyword.lower()
            if not (
                kw in (inv.get("item_code") or "").lower()
                or kw in (inv.get("item_name") or "").lower()
            ):
                continue
        filtered.append(inv)

    total = len(filtered)
    filtered.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    data = []
    for inv in page_items:
        qty = float(inv.get("quantity", 0) or 0)
        safety = float(inv.get("safety_stock")) if inv.get("safety_stock") is not None else None
        is_low = safety is not None and qty < safety
        expiry = inv.get("expiry_date")
        days_to_expiry = None
        if expiry:
            try:
                days_to_expiry = (date.fromisoformat(str(expiry)) - date.today()).days
            except Exception:
                pass
        data.append({
            "id": inv.get("_record_id"),
            "item_code": inv.get("item_code"),
            "item_name": inv.get("item_name"),
            "item_category": inv.get("item_category"),
            "item_category_text": category_map.get(inv.get("item_category"), "未知"),
            "quantity": qty,
            "safety_stock": safety,
            "stock_status": "预警" if is_low else "充足",
            "storage_location": inv.get("storage_location"),
            "expiry_date": str(expiry) if expiry else None,
            "days_to_expiry": days_to_expiry,
            "status": inv.get("status"),
            "status_text": status_map.get(inv.get("status"), "未知"),
            "updated_at": str(inv.get("updated_at")),
        })

    # 汇总
    low_stock_count = sum(
        1 for inv in items
        if inv.get("safety_stock") is not None
        and float(inv.get("quantity", 0) or 0) < float(inv.get("safety_stock"))
    )
    near_expiry_count = sum(
        1 for inv in items
        if inv.get("expiry_date")
        and 0 <= (date.fromisoformat(str(inv.get("expiry_date"))) - date.today()).days <= 30
    )

    return {
        "code": 0,
        "message": "success",
        "data": {
            "summary": {
                "total_items": total,
                "low_stock_count": low_stock_count,
                "near_expiry_count": near_expiry_count,
            },
            "list": data,
        },
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        }
    }


@router.post("")
async def create_inventory(
    data: dict = Body(...),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """创建库存物料"""
    record = await repos.inventory.create({
        "item_code": data.get("item_code"),
        "item_name": data.get("item_name"),
        "item_category": data.get("item_category"),
        "item_spec": data.get("item_spec"),
        "unit": data.get("unit"),
        "quantity": data.get("quantity", 0),
        "safety_stock": data.get("safety_stock"),
        "storage_location": data.get("storage_location"),
        "batch_no": data.get("batch_no"),
        "expiry_date": data.get("expiry_date"),
        "status": 1,
    })
    return success_response({
        "id": record.get("_record_id"),
        "item_code": record.get("item_code"),
        "item_name": record.get("item_name"),
        "status": record.get("status"),
        "created_at": str(record.get("created_at")),
    }, "创建成功")


@router.put("/{inventory_id}")
async def update_inventory(inventory_id: str, data: dict = Body(...), repos: RepositoryFactory = Depends(get_repositories)):
    """更新库存物料"""
    inv = await repos.inventory.get_by_id(inventory_id)
    if not inv:
        return error_response(404, "库存物料不存在")
    update_data = {k: v for k, v in data.items() if v is not None}
    updated = await repos.inventory.update(inventory_id, update_data)
    return success_response({
        "id": updated.get("_record_id"),
        "item_code": updated.get("item_code"),
        "quantity": float(updated.get("quantity", 0) or 0),
    })


@router.get("/{inventory_id}/transactions")
async def list_inventory_transactions(
    inventory_id: str,
    trans_type: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """库存流水查询"""
    inv = await repos.inventory.get_by_id(inventory_id)
    if not inv:
        return error_response(404, "库存物料不存在")

    transactions = await repos.inv_trans.filter_by("inventory_id", inventory_id)
    filtered = []
    for t in transactions:
        if trans_type is not None and t.get("trans_type") != trans_type:
            continue
        t_date = t.get("trans_date")
        if start_date and t_date:
            try:
                if date.fromisoformat(str(t_date)) < start_date:
                    continue
            except Exception:
                pass
        if end_date and t_date:
            try:
                if date.fromisoformat(str(t_date)) > end_date:
                    continue
            except Exception:
                pass
        filtered.append(t)

    total = len(filtered)
    filtered.sort(key=lambda x: x.get("trans_date") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    data = [
        {
            "id": t.get("_record_id"),
            "trans_type": t.get("trans_type"),
            "trans_type_text": trans_type_map.get(t.get("trans_type"), "未知"),
            "trans_date": str(t.get("trans_date")),
            "quantity": float(t.get("quantity", 0) or 0),
            "balance": float(t.get("balance", 0) or 0),
            "ref_type": t.get("ref_type"),
            "ref_type_text": ref_type_map.get(t.get("ref_type"), "") if t.get("ref_type") else None,
            "ref_id": t.get("ref_id"),
            "operator": t.get("operator"),
            "remark": t.get("remark"),
        }
        for t in page_items
    ]

    return {
        "code": 0,
        "message": "success",
        "data": {
            "inventory": {
                "id": inv.get("_record_id"),
                "item_code": inv.get("item_code"),
                "item_name": inv.get("item_name"),
                "current_quantity": float(inv.get("quantity", 0) or 0),
            },
            "list": data,
        },
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        }
    }


@router.post("/{inventory_id}/transactions")
async def create_transaction(
    inventory_id: str,
    data: dict = Body(...),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """创建库存流水（出入库）"""
    inv = await repos.inventory.get_by_id(inventory_id)
    if not inv:
        return error_response(404, "库存物料不存在")

    qty = float(data.get("quantity", 0))
    raw_tt = data.get("transaction_type") or data.get("trans_type")
    if isinstance(raw_tt, str):
        ttype_map = {"in": 1, "out": 2, "adjust": 3, "loss": 4}
        ttype_int = ttype_map.get(raw_tt.lower())
        if ttype_int is None:
            return error_response(422, f"transaction_type 取值非法: {raw_tt}")
        ttype_str = raw_tt.lower()
    else:
        ttype_int = raw_tt
        ttype_str = {1: "in", 2: "out", 3: "adjust", 4: "loss"}.get(raw_tt, str(raw_tt))

    # 余额计算方向（在锁内重新读取库存，防止并发超卖）
    async with _get_inv_lock(inventory_id):
        inv = await repos.inventory.get_by_id(inventory_id)
        if not inv:
            return error_response(404, "库存物料不存在")

        if ttype_int in (2, 4):  # 出库/损耗
            balance_delta = -abs(qty)
        else:  # 入库/调整
            balance_delta = abs(qty)
        current_qty = float(inv.get("quantity", 0) or 0)
        new_balance = current_qty + balance_delta
        if new_balance < 0:
            return error_response(422, "库存不足，无法出库")

        # 处理日期
        trans_date_raw = data.get("trans_date")
        if isinstance(trans_date_raw, str):
            from datetime import datetime as _dt
            try:
                trans_date_val = _dt.strptime(trans_date_raw, "%Y-%m-%d").date()
            except ValueError:
                trans_date_val = date.today()
        else:
            trans_date_val = trans_date_raw or date.today()

        # 创建流水记录
        trans = await repos.inv_trans.create({
            "inventory_id": inventory_id,
            "trans_type": ttype_int,
            "trans_date": str(trans_date_val),
            "quantity": qty,
            "balance": new_balance,
            "ref_type": data.get("ref_type"),
            "ref_id": data.get("ref_id"),
            "operator": data.get("operator"),
            "remark": data.get("remark") or data.get("reason"),
        })

        # 更新库存数量
        await repos.inventory.update(inventory_id, {"quantity": new_balance})

    return success_response({
        "id": trans.get("_record_id"),
        "transaction_type": ttype_str,
        "trans_type": trans.get("trans_type"),
        "quantity": float(trans.get("quantity", 0) or 0),
        "balance": float(trans.get("balance", 0) or 0),
        "trans_date": str(trans.get("trans_date")),
    }, "操作成功")


@router.get("/alerts")
async def get_inventory_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """库存预警查询（分页）"""
    items = await repos.inventory.list_all()

    low_stock = []
    near_expiry = []
    expired = []
    for inv in items:
        qty = float(inv.get("quantity", 0) or 0)
        safety = float(inv.get("safety_stock")) if inv.get("safety_stock") is not None else None
        if safety is not None and qty < safety:
            low_stock.append(inv)
        expiry = inv.get("expiry_date")
        if expiry:
            try:
                days = (date.fromisoformat(str(expiry)) - date.today()).days
                if 0 <= days <= 30:
                    near_expiry.append(inv)
                elif days < 0:
                    expired.append(inv)
            except Exception:
                pass

    def to_alert_dict(inv, alert_type):
        qty = float(inv.get("quantity", 0) or 0)
        safety = float(inv.get("safety_stock")) if inv.get("safety_stock") is not None else None
        expiry = inv.get("expiry_date")
        days_to_expiry = None
        if expiry:
            try:
                days_to_expiry = (date.fromisoformat(str(expiry)) - date.today()).days
            except Exception:
                pass
        return {
            "id": inv.get("_record_id"),
            "item_code": inv.get("item_code"),
            "item_name": inv.get("item_name"),
            "quantity": qty,
            "safety_stock": safety,
            "expiry_date": str(expiry) if expiry else None,
            "days_to_expiry": days_to_expiry,
            "status": inv.get("status"),
            "alert_type": alert_type,
        }

    alerts = []
    alerts.extend([to_alert_dict(inv, "low_stock") for inv in low_stock])
    alerts.extend([to_alert_dict(inv, "near_expiry") for inv in near_expiry])
    alerts.extend([to_alert_dict(inv, "expired") for inv in expired])

    return success_response(alerts)
