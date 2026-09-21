"""财务收支管理 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import date

from app.database import get_db
from app.models import FinancialTransaction, Batch
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/financial-transactions", tags=["财务收支管理"])


@router.get("")
def list_transactions(
    transaction_type: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    batch_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询收支列表"""
    query = db.query(FinancialTransaction, Batch.batch_no).outerjoin(Batch, FinancialTransaction.batch_id == Batch.id)
    if transaction_type is not None:
        query = query.filter(FinancialTransaction.transaction_type == transaction_type)
    if category:
        query = query.filter(FinancialTransaction.category == category)
    if batch_id is not None:
        query = query.filter(FinancialTransaction.batch_id == batch_id)
    if start_date:
        query = query.filter(FinancialTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(FinancialTransaction.transaction_date <= end_date)
    if keyword:
        query = query.filter(
            (FinancialTransaction.category.contains(keyword)) |
            (FinancialTransaction.payee_payer.contains(keyword)) |
            (FinancialTransaction.remark.contains(keyword))
        )

    # 汇总
    income = db.query(func.sum(FinancialTransaction.amount)).filter(FinancialTransaction.transaction_type == 1)
    expense = db.query(func.sum(FinancialTransaction.amount)).filter(FinancialTransaction.transaction_type == 2)
    if start_date:
        income = income.filter(FinancialTransaction.transaction_date >= start_date)
        expense = expense.filter(FinancialTransaction.transaction_date >= start_date)
    if end_date:
        income = income.filter(FinancialTransaction.transaction_date <= end_date)
    if batch_id is not None:
        income = income.filter(FinancialTransaction.batch_id == batch_id)
        expense = expense.filter(FinancialTransaction.batch_id == batch_id)

    total_income = income.scalar() or 0
    total_expense = expense.scalar() or 0
    net_profit = float(total_income) - float(total_expense)

    total = query.count()
    items = query.order_by(desc(FinancialTransaction.transaction_date)).offset((page - 1) * page_size).limit(page_size).all()
    data = [
        {
            "id": ft.id,
            "transaction_type": ft.transaction_type,
            "transaction_type_text": "收入" if ft.transaction_type == 1 else "支出",
            "category": ft.category,
            "amount": float(ft.amount),
            "batch_id": ft.batch_id,
            "batch_no": batch_no,
            "transaction_date": str(ft.transaction_date),
            "payee_payer": ft.payee_payer,
            "remark": ft.remark,
            "voucher_no": ft.voucher_no,
        }
        for ft, batch_no in items
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
def create_transaction(
    data: dict = Body(...),
    db: Session = Depends(get_db),
):
    """创建收支记录"""
    # 必填字段校验
    if not data.get("transaction_type"):
        return error_response(422, "transaction_type不能为空")
    if data.get("amount") is None:
        return error_response(422, "amount不能为空")
    if not data.get("transaction_date"):
        return error_response(422, "transaction_date不能为空")

    # 处理日期字段，SQLite/通用驱动不接受Python date对象以外的输入
    txn_date_raw = data.get("transaction_date")
    if isinstance(txn_date_raw, str):
        try:
            txn_date_val = date.fromisoformat(txn_date_raw)
        except ValueError:
            return error_response(422, f"transaction_date格式非法: {txn_date_raw}")
    else:
        txn_date_val = txn_date_raw or date.today()

    ft = FinancialTransaction(
        transaction_type=data.get("transaction_type"),
        category=data.get("category", ""),
        amount=data.get("amount"),
        batch_id=data.get("batch_id"),
        ref_table=data.get("ref_table"),
        ref_id=data.get("ref_id"),
        transaction_date=txn_date_val,
        payee_payer=data.get("payee_payer"),
        remark=data.get("remark"),
        voucher_no=data.get("voucher_no"),
        created_by=data.get("created_by"),
    )
    db.add(ft)
    db.commit()
    db.refresh(ft)
    return success_response({
        "id": ft.id,
        "transaction_type": ft.transaction_type,
        "category": ft.category,
        "amount": float(ft.amount),
        "transaction_date": str(ft.transaction_date),
        "created_at": str(ft.created_at),
    }, "创建成功")


@router.get("/summary")
def get_finance_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    group_by: Optional[str] = Query(None, description="month|category|batch"),
    db: Session = Depends(get_db),
):
    """收支汇总查询"""
    query = db.query(FinancialTransaction)
    if start_date:
        query = query.filter(FinancialTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(FinancialTransaction.transaction_date <= end_date)

    total_income = db.query(func.sum(FinancialTransaction.amount)).filter(FinancialTransaction.transaction_type == 1)
    total_expense = db.query(func.sum(FinancialTransaction.amount)).filter(FinancialTransaction.transaction_type == 2)
    if start_date:
        total_income = total_income.filter(FinancialTransaction.transaction_date >= start_date)
        total_expense = total_expense.filter(FinancialTransaction.transaction_date >= start_date)
    if end_date:
        total_income = total_income.filter(FinancialTransaction.transaction_date <= end_date)
        total_expense = total_expense.filter(FinancialTransaction.transaction_date <= end_date)

    ti = total_income.scalar() or 0
    te = total_expense.scalar() or 0
    net = float(ti) - float(te)
    margin = round(net / float(ti) * 100, 2) if ti else 0

    result = {
        "period": {
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
        },
        "summary": {
            "total_income": float(ti),
            "total_expense": float(te),
            "net_profit": round(net, 2),
            "profit_margin": margin,
        },
        "grouped_data": [],
        "category_breakdown": [],
    }

    # 按分组维度聚合
    if group_by == "month":
        from sqlalchemy import extract
        grouped = db.query(
            extract("year", FinancialTransaction.transaction_date).label("year"),
            extract("month", FinancialTransaction.transaction_date).label("month"),
            FinancialTransaction.transaction_type,
            func.sum(FinancialTransaction.amount).label("total")
        )
        if start_date:
            grouped = grouped.filter(FinancialTransaction.transaction_date >= start_date)
        if end_date:
            grouped = grouped.filter(FinancialTransaction.transaction_date <= end_date)
        grouped = grouped.group_by("year", "month", FinancialTransaction.transaction_type).order_by("year", "month").all()

        month_map = {}
        for yr, mo, ttype, total_amt in grouped:
            mkey = f"{int(yr)}-{int(mo):02d}"
            if mkey not in month_map:
                month_map[mkey] = {"group_key": mkey, "income": 0, "expense": 0}
            if ttype == 1:
                month_map[mkey]["income"] = float(total_amt)
            else:
                month_map[mkey]["expense"] = float(total_amt)

        for k, v in month_map.items():
            v["net_profit"] = round(v["income"] - v["expense"], 2)
            v["profit_margin"] = round(v["net_profit"] / v["income"] * 100, 2) if v["income"] else 0
            result["grouped_data"].append(v)

    # 科目占比
    cats = db.query(FinancialTransaction.category, FinancialTransaction.transaction_type, func.sum(FinancialTransaction.amount)).filter(FinancialTransaction.transaction_type.in_([1, 2]))
    if start_date:
        cats = cats.filter(FinancialTransaction.transaction_date >= start_date)
    if end_date:
        cats = cats.filter(FinancialTransaction.transaction_date <= end_date)
    cats = cats.group_by(FinancialTransaction.category, FinancialTransaction.transaction_type).all()

    for cat, ttype, amt in cats:
        result["category_breakdown"].append({
            "category": cat,
            "type": "income" if ttype == 1 else "expense",
            "amount": float(amt),
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
