"""销售订单 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/sales", tags=["销售管理"])


@router.get("")
async def list_sales(
    status: Optional[int] = Query(None, description="订单状态"),
    customer_name: Optional[str] = Query(None, description="客户名称"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询销售订单列表"""
    orders = await repos.sales.list_all()

    if status is not None:
        orders = [o for o in orders if o.get("status") == status]
    if customer_name:
        kw = customer_name.lower()
        orders = [o for o in orders if kw in (o.get("customer_name") or "").lower()]
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
            "customer_name": o.get("customer_name"),
            "customer_phone": o.get("customer_phone"),
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
async def get_sale_detail(order_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """获取销售订单详情"""
    order = await repos.sales.get_by_id(order_id)
    if not order:
        return error_response(404, "销售订单不存在")

    # 获取订单明细
    items = await repos.sales_item.filter_by("order_id", order_id)

    return success_response({
        "id": order.get("_record_id"),
        "order_no": order.get("order_no"),
        "customer_name": order.get("customer_name"),
        "customer_phone": order.get("customer_phone"),
        "customer_address": order.get("customer_address"),
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
                "product_name": item.get("product_name"),
                "batch_id": item.get("batch_id"),
                "quantity": item.get("quantity"),
                "unit_price": float(item.get("unit_price", 0) or 0),
                "subtotal": float(item.get("subtotal", 0) or 0),
            }
            for item in items
        ],
    })


@router.post("")
async def create_sale(data: dict, repos: RepositoryFactory = Depends(get_repositories)):
    """创建销售订单"""
    order = await repos.sales.create(data)
    return success_response(order, "创建成功")


@router.put("/{order_id}")
async def update_sale(order_id: str, data: dict, repos: RepositoryFactory = Depends(get_repositories)):
    """更新销售订单"""
    existing = await repos.sales.get_by_id(order_id)
    if not existing:
        return error_response(404, "销售订单不存在")
    updated = await repos.sales.update(order_id, data)
    return success_response(updated, "更新成功")


@router.delete("/{order_id}")
async def delete_sale(order_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """删除销售订单"""
    existing = await repos.sales.get_by_id(order_id)
    if not existing:
        return error_response(404, "销售订单不存在")
    await repos.sales.delete(order_id)
    return success_response(None, "删除成功")
