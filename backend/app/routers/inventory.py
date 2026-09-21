"""库存管理 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, timedelta

from app.database import get_db
from app.models import Inventory, InventoryTransaction
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/inventory", tags=["库存管理"])


@router.get("")
def list_inventory(
    item_category: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    low_stock: Optional[bool] = Query(None),
    near_expiry: Optional[bool] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询库存列表"""
    query = db.query(Inventory)
    if item_category is not None:
        query = query.filter(Inventory.item_category == item_category)
    if status is not None:
        query = query.filter(Inventory.status == status)
    if low_stock:
        query = query.filter(Inventory.quantity < Inventory.safety_stock)
    if near_expiry:
        query = query.filter(Inventory.expiry_date <= date.today() + timedelta(days=30))
    if keyword:
        query = query.filter(
            (Inventory.item_code.contains(keyword)) |
            (Inventory.item_name.contains(keyword))
        )

    total = query.count()
    items = query.order_by(desc(Inventory.updated_at)).offset((page - 1) * page_size).limit(page_size).all()

    category_map = {1: "饲料", 2: "药品", 3: "疫苗", 4: "设备", 5: "种鸡", 6: "其他"}
    status_map = {1: "正常", 2: "临期", 3: "过期", 4: "冻结"}

    data = []
    for inv in items:
        is_low = inv.safety_stock is not None and float(inv.quantity) < float(inv.safety_stock)
        days_to_expiry = (inv.expiry_date - date.today()).days if inv.expiry_date else None
        data.append({
            "id": inv.id,
            "item_code": inv.item_code,
            "item_name": inv.item_name,
            "item_category": inv.item_category,
            "item_category_text": category_map.get(inv.item_category, "未知"),
            "quantity": float(inv.quantity),
            "safety_stock": float(inv.safety_stock) if inv.safety_stock else None,
            "stock_status": "预警" if is_low else "充足",
            "storage_location": inv.storage_location,
            "expiry_date": str(inv.expiry_date) if inv.expiry_date else None,
            "days_to_expiry": days_to_expiry,
            "status": inv.status,
            "status_text": status_map.get(inv.status, "未知"),
            "updated_at": str(inv.updated_at),
        })

    # 汇总
    low_stock_count = db.query(func.count(Inventory.id)).filter(Inventory.quantity < Inventory.safety_stock).scalar() or 0
    near_expiry_count = db.query(func.count(Inventory.id)).filter(Inventory.expiry_date <= date.today() + timedelta(days=30), Inventory.expiry_date >= date.today()).scalar() or 0

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
def create_inventory(
    data: dict = Body(...),
    db: Session = Depends(get_db),
):
    """创建库存物料"""
    inv = Inventory(
        item_code=data.get("item_code"),
        item_name=data.get("item_name"),
        item_category=data.get("item_category"),
        item_spec=data.get("item_spec"),
        unit=data.get("unit"),
        quantity=data.get("quantity", 0),
        safety_stock=data.get("safety_stock"),
        storage_location=data.get("storage_location"),
        batch_no=data.get("batch_no"),
        expiry_date=data.get("expiry_date"),
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return success_response({
        "id": inv.id,
        "item_code": inv.item_code,
        "item_name": inv.item_name,
        "status": inv.status,
        "created_at": str(inv.created_at),
    }, "创建成功")


@router.put("/{inventory_id}")
def update_inventory(inventory_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    """更新库存物料"""
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        return error_response(404, "库存物料不存在")
    for k, v in data.items():
        if hasattr(inv, k) and v is not None:
            setattr(inv, k, v)
    db.commit()
    db.refresh(inv)
    return success_response({"id": inv.id, "item_code": inv.item_code, "quantity": float(inv.quantity)})


@router.get("/{inventory_id}/transactions")
def list_inventory_transactions(
    inventory_id: int,
    trans_type: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """库存流水查询"""
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        return error_response(404, "库存物料不存在")

    query = db.query(InventoryTransaction).filter(InventoryTransaction.inventory_id == inventory_id)
    if trans_type is not None:
        query = query.filter(InventoryTransaction.trans_type == trans_type)
    if start_date:
        query = query.filter(InventoryTransaction.trans_date >= start_date)
    if end_date:
        query = query.filter(InventoryTransaction.trans_date <= end_date)

    total = query.count()
    items = query.order_by(desc(InventoryTransaction.trans_date)).offset((page - 1) * page_size).limit(page_size).all()

    trans_type_map = {1: "入库", 2: "出库", 3: "盘点调整", 4: "损耗"}
    ref_type_map = {1: "采购", 2: "销售", 3: "领用", 4: "调拨", 5: "孵化"}

    data = [
        {
            "id": t.id,
            "trans_type": t.trans_type,
            "trans_type_text": trans_type_map.get(t.trans_type, "未知"),
            "trans_date": str(t.trans_date),
            "quantity": float(t.quantity),
            "balance": float(t.balance),
            "ref_type": t.ref_type,
            "ref_type_text": ref_type_map.get(t.ref_type, "") if t.ref_type else None,
            "ref_id": t.ref_id,
            "operator": t.operator,
            "remark": t.remark,
        }
        for t in items
    ]

    return {
        "code": 0,
        "message": "success",
        "data": {
            "inventory": {
                "id": inv.id,
                "item_code": inv.item_code,
                "item_name": inv.item_name,
                "current_quantity": float(inv.quantity),
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
def create_transaction(
    inventory_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
):
    """创建库存流水（出入库）- 使用悲观锁防止并发超卖"""
    # 使用 SELECT ... FOR UPDATE 锁定库存记录，防止并发竞争
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).with_for_update().first()
    if not inv:
        return error_response(404, "库存物料不存在")

    qty = float(data.get("quantity", 0))
    # 支持字符串 transaction_type ("in"/"out") 和整数 trans_type
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

    # 余额计算方向（按出库/损耗扣减），但 quantity 字段保留正数作为变动幅度
    if ttype_int in (2, 4):  # 出库/损耗
        balance_delta = -abs(qty)
    else:  # 入库/调整
        balance_delta = abs(qty)
    new_balance = float(inv.quantity) + balance_delta
    if new_balance < 0:
        return error_response(422, "库存不足，无法出库")

    # 处理日期字符串
    trans_date_raw = data.get("trans_date")
    if isinstance(trans_date_raw, str):
        from datetime import datetime as _dt
        try:
            trans_date_val = _dt.strptime(trans_date_raw, "%Y-%m-%d").date()
        except ValueError:
            trans_date_val = date.today()
    else:
        trans_date_val = trans_date_raw or date.today()

    trans = InventoryTransaction(
        inventory_id=inventory_id,
        trans_type=ttype_int,
        trans_date=trans_date_val,
        quantity=qty,
        balance=new_balance,
        ref_type=data.get("ref_type"),
        ref_id=data.get("ref_id"),
        operator=data.get("operator"),
        remark=data.get("remark") or data.get("reason"),
    )
    db.add(trans)
    inv.quantity = new_balance
    db.commit()
    db.refresh(trans)
    return success_response({
        "id": trans.id,
        "transaction_type": ttype_str,
        "trans_type": trans.trans_type,
        "quantity": float(trans.quantity),
        "balance": float(trans.balance),
        "trans_date": str(trans.trans_date),
    }, "操作成功")


@router.get("/alerts")
def get_inventory_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """库存预警查询（分页）"""
    low_stock = db.query(Inventory).filter(Inventory.quantity < Inventory.safety_stock).offset((page - 1) * page_size).limit(page_size).all()
    near_expiry = db.query(Inventory).filter(
        Inventory.expiry_date <= date.today() + timedelta(days=30),
        Inventory.expiry_date >= date.today()
    ).offset((page - 1) * page_size).limit(page_size).all()
    expired = db.query(Inventory).filter(Inventory.expiry_date < date.today()).offset((page - 1) * page_size).limit(page_size).all()

    def to_alert_dict(inv, alert_type):
        return {
            "id": inv.id,
            "item_code": inv.item_code,
            "item_name": inv.item_name,
            "quantity": float(inv.quantity),
            "safety_stock": float(inv.safety_stock) if inv.safety_stock else None,
            "expiry_date": str(inv.expiry_date) if inv.expiry_date else None,
            "days_to_expiry": (inv.expiry_date - date.today()).days if inv.expiry_date else None,
            "status": inv.status,
            "alert_type": alert_type,
        }

    alerts = []
    alerts.extend([to_alert_dict(inv, "low_stock") for inv in low_stock])
    alerts.extend([to_alert_dict(inv, "near_expiry") for inv in near_expiry])
    alerts.extend([to_alert_dict(inv, "expired") for inv in expired])

    return success_response(alerts)
