"""采购订单 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/purchases", tags=["采购管理"])


@router.get("")
async def list_purchases(
    status: Optional[int] = Query(None, description="订单状态"),
    supplier_name: Optional[str] = Query(None, description="供应商名称"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询采购订单列表"""
    orders = await repos.purchase.list_all()

    if status is not None:
        orders = [o for o in orders if o.get("status") == status]
    if supplier_name:
        kw = supplier_name.lower()
        orders = [o for o in orders if kw in (o.get("supplier_name") or "").lower()]
    if start_date:
        orders = [o for o in orders if (o.get("order_date") or "") >= start_date]
    if end_date:
        orders = [o for o in orders if (o.get("order_date") or "") <= end_date]

    total = len(orders)
    orders.sort(key=lambda x: x.get("order_date") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = orders[start : start + page_size]

    data = [
        {
            "id": o.get("_record_id"),
            "order_no": o.get("order_no"),
            "supplier_name": o.get("supplier_name"),
            "supplier_phone": o.get("supplier_phone"),
            "order_date": str(o.get("order_date")),
            "delivery_date": str(o.get("delivery_date")) if o.get("delivery_date") else None,
            "total_amount": float(o.get("total_amount", 0) or 0),
            "total_quantity": o.get("total_quantity"),
            "status": o.get("status"),
            "payment_status": o.get("payment_status"),
            "remark": o.get("remark"),
            "created_at": o.get("created_at"),
        }
        for o in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/{order_id}")
async def get_purchase_detail(order_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """获取采购订单详情"""
    order = await repos.purchase.get_by_id(order_id)
    if not order:
        return error_response(404, "采购订单不存在")

    # 获取订单明细
    items = await repos.purchase_item.filter_by("order_id", order_id)

    return success_response({
        "id": order.get("_record_id"),
        "order_no": order.get("order_no"),
        "supplier_name": order.get("supplier_name"),
        "supplier_phone": order.get("supplier_phone"),
        "supplier_address": order.get("supplier_address"),
        "order_date": str(order.get("order_date")),
        "delivery_date": str(order.get("delivery_date")) if order.get("delivery_date") else None,
        "total_amount": float(order.get("total_amount", 0) or 0),
        "total_quantity": order.get("total_quantity"),
        "status": order.get("status"),
        "payment_status": order.get("payment_status"),
        "remark": order.get("remark"),
        "items": [
            {
                "id": item.get("_record_id"),
                "item_name": item.get("item_name"),
                "item_type": item.get("item_type"),
                "quantity": item.get("quantity"),
                "unit_price": float(item.get("unit_price", 0) or 0),
                "subtotal": float(item.get("subtotal", 0) or 0),
            }
            for item in items
        ],
    })


@router.post("")
async def create_purchase(data: dict, repos: RepositoryFactory = Depends(get_repositories)):
    """创建采购订单"""
    order = await repos.purchase.create(data)
    return success_response(order, "创建成功")


@router.put("/{order_id}")
async def update_purchase(order_id: str, data: dict, repos: RepositoryFactory = Depends(get_repositories)):
    """更新采购订单"""
    existing = await repos.purchase.get_by_id(order_id)
    if not existing:
        return error_response(404, "采购订单不存在")
    updated = await repos.purchase.update(order_id, data)
    return success_response(updated, "更新成功")


@router.delete("/{order_id}")
async def delete_purchase(order_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """删除采购订单"""
    existing = await repos.purchase.get_by_id(order_id)
    if not existing:
        return error_response(404, "采购订单不存在")
    await repos.purchase.delete(order_id)
    return success_response(None, "删除成功")
