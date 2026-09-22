"""财务收支管理 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from datetime import date
from collections import defaultdict

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/financial-transactions", tags=["财务收支管理"])


@router.get("")
async def list_transactions(
    transaction_type: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    batch_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询收支列表"""
    # 预加载批次映射
    batches_map = {b.get("_record_id"): b.get("batch_no") for b in await repos.batch.list_all()}

    transactions = await repos.financial.list_all()
    filtered = []
    for ft in transactions:
        if transaction_type is not None and ft.get("transaction_type") != transaction_type:
            continue
        if category and ft.get("category") != category:
            continue
        if batch_id is not None and ft.get("batch_id") != batch_id:
            continue
        txn_date = ft.get("transaction_date")
        if start_date and txn_date:
            try:
                if date.fromisoformat(str(txn_date)) < start_date:
                    continue
            except Exception:
                pass
        if end_date and txn_date:
            try:
                if date.fromisoformat(str(txn_date)) > end_date:
                    continue
            except Exception:
                pass
        if keyword:
            kw = keyword.lower()
            if not (
                kw in (ft.get("category") or "").lower()
                or kw in (ft.get("payee_payer") or "").lower()
                or kw in (ft.get("remark") or "").lower()
            ):
                continue
        filtered.append(ft)

    # 汇总
    def _amount_sum(t_type, s_date, e_date, b_id):
        total = 0
        for ft in transactions:
            if ft.get("transaction_type") != t_type:
                continue
            if b_id is not None and ft.get("batch_id") != b_id:
                continue
            txn_date = ft.get("transaction_date")
            if s_date and txn_date:
                try:
                    if date.fromisoformat(str(txn_date)) < s_date:
                        continue
                except Exception:
                    pass
            if e_date and txn_date:
                try:
                    if date.fromisoformat(str(txn_date)) > e_date:
                        continue
                except Exception:
                    pass
            total += float(ft.get("amount", 0) or 0)
        return total

    total_income = _amount_sum(1, start_date, end_date, batch_id)
    total_expense = _amount_sum(2, start_date, end_date, batch_id)
    net_profit = total_income - total_expense

    total = len(filtered)
    filtered.sort(key=lambda x: x.get("transaction_date") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    data = [
        {
            "id": ft.get("_record_id"),
            "transaction_type": ft.get("transaction_type"),
            "transaction_type_text": "收入" if ft.get("transaction_type") == 1 else "支出",
            "category": ft.get("category"),
            "amount": float(ft.get("amount", 0) or 0),
            "batch_id": ft.get("batch_id"),
            "batch_no": batches_map.get(str(ft.get("batch_id"))),
            "transaction_date": str(ft.get("transaction_date")),
            "payee_payer": ft.get("payee_payer"),
            "remark": ft.get("remark"),
            "voucher_no": ft.get("voucher_no"),
        }
        for ft in page_items
    ]
    return {
        "code": 0,
        "message": "success",
        "data": {
            "summary": {
                "total_income": float(total_income),
                "total_expense": float(total_expense),
                "net_profit": round(net_profit, 2),
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
async def create_transaction(
    data: dict = Body(...),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """创建收支记录"""
    if not data.get("transaction_type"):
        return error_response(422, "transaction_type不能为空")
    if data.get("amount") is None:
        return error_response(422, "amount不能为空")
    if not data.get("transaction_date"):
        return error_response(422, "transaction_date不能为空")

    txn_date_raw = data.get("transaction_date")
    if isinstance(txn_date_raw, str):
        try:
            txn_date_val = date.fromisoformat(txn_date_raw)
        except ValueError:
            return error_response(422, f"transaction_date格式非法: {txn_date_raw}")
    else:
        txn_date_val = txn_date_raw or date.today()

    record = await repos.financial.create({
        "transaction_type": data.get("transaction_type"),
        "category": data.get("category", ""),
        "amount": data.get("amount"),
        "batch_id": data.get("batch_id"),
        "ref_table": data.get("ref_table"),
        "ref_id": data.get("ref_id"),
        "transaction_date": str(txn_date_val),
        "payee_payer": data.get("payee_payer"),
        "remark": data.get("remark"),
        "voucher_no": data.get("voucher_no"),
        "created_by": data.get("created_by"),
    })
    return success_response({
        "id": record.get("_record_id"),
        "transaction_type": record.get("transaction_type"),
        "category": record.get("category"),
        "amount": float(record.get("amount", 0) or 0),
        "transaction_date": str(record.get("transaction_date")),
        "created_at": str(record.get("created_at")),
    }, "创建成功")


@router.get("/summary")
async def get_finance_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    group_by: Optional[str] = Query(None, description="month|category|batch"),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """收支汇总查询"""
    transactions = await repos.financial.list_all()
    filtered = []
    for ft in transactions:
        txn_date = ft.get("transaction_date")
        if start_date and txn_date:
            try:
                if date.fromisoformat(str(txn_date)) < start_date:
                    continue
            except Exception:
                pass
        if end_date and txn_date:
            try:
                if date.fromisoformat(str(txn_date)) > end_date:
                    continue
            except Exception:
                pass
        filtered.append(ft)

    total_income = sum(float(ft.get("amount", 0) or 0) for ft in filtered if ft.get("transaction_type") == 1)
    total_expense = sum(float(ft.get("amount", 0) or 0) for ft in filtered if ft.get("transaction_type") == 2)
    net = total_income - total_expense
    margin = round(net / total_income * 100, 2) if total_income else 0

    result = {
        "period": {
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
        },
        "summary": {
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "net_profit": round(net, 2),
            "profit_margin": margin,
        },
        "grouped_data": [],
        "category_breakdown": [],
    }

    # 按分组维度聚合
    if group_by == "month":
        month_map = defaultdict(lambda: {"group_key": "", "income": 0, "expense": 0})
        for ft in filtered:
            txn_date = ft.get("transaction_date")
            if not txn_date:
                continue
            try:
                d = date.fromisoformat(str(txn_date))
                mkey = f"{d.year}-{d.month:02d}"
            except Exception:
                continue
            month_map[mkey]["group_key"] = mkey
            if ft.get("transaction_type") == 1:
                month_map[mkey]["income"] += float(ft.get("amount", 0) or 0)
            else:
                month_map[mkey]["expense"] += float(ft.get("amount", 0) or 0)

        for k, v in month_map.items():
            v["net_profit"] = round(v["income"] - v["expense"], 2)
            v["profit_margin"] = round(v["net_profit"] / v["income"] * 100, 2) if v["income"] else 0
            result["grouped_data"].append(v)

    # 科目占比
    cats = defaultdict(lambda: {"income": 0, "expense": 0})
    for ft in filtered:
        cat = ft.get("category", "")
        if ft.get("transaction_type") == 1:
            cats[cat]["income"] += float(ft.get("amount", 0) or 0)
        else:
            cats[cat]["expense"] += float(ft.get("amount", 0) or 0)

    for cat, amounts in cats.items():
        if amounts["income"] > 0:
            result["category_breakdown"].append({
                "category": cat,
                "type": "income",
                "amount": round(amounts["income"], 2),
            })
        if amounts["expense"] > 0:
            result["category_breakdown"].append({
                "category": cat,
                "type": "expense",
                "amount": round(amounts["expense"], 2),
            })

    # 计算百分比
    total_income_all = sum(c["amount"] for c in result["category_breakdown"] if c["type"] == "income")
    total_expense_all = sum(c["amount"] for c in result["category_breakdown"] if c["type"] == "expense")
    for c in result["category_breakdown"]:
        if c["type"] == "income" and total_income_all:
            c["pct"] = round(c["amount"] / total_income_all * 100, 2)
        elif c["type"] == "expense" and total_expense_all:
            c["pct"] = round(c["amount"] / total_expense_all * 100, 2)
        else:
            c["pct"] = 0

    return success_response(result)
