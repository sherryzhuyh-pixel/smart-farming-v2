"""批次全生命周期 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from datetime import date

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/batches", tags=["批次管理"])


@router.get("")
async def list_batches(
    status: Optional[int] = Query(None, description="批次状态"),
    breed_id: Optional[int] = Query(None, description="品种ID"),
    house_id: Optional[int] = Query(None, description="鸡舍ID"),
    keyword: Optional[str] = Query(None, description="关键字搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询批次列表"""
    # 拉取全量小表做内存关联
    breeds = {b.get("_record_id"): b for b in await repos.breed.list_all()}
    houses = {h.get("_record_id"): h for h in await repos.house.list_all()}

    # 拉取批次数据（优先用 status 过滤减少数据量）
    if status is not None:
        batches = await repos.batch.filter_by("status", status)
    else:
        batches = await repos.batch.list_all()

    # 内存过滤
    filtered = []
    for b in batches:
        if breed_id is not None and b.get("breed_id") != breed_id:
            continue
        if house_id is not None and b.get("house_id") != house_id:
            continue
        if keyword:
            kw = keyword.lower()
            if not (
                kw in (b.get("batch_no") or "").lower()
                or kw in (b.get("batch_name") or "").lower()
                or kw in (b.get("responsible_person") or "").lower()
            ):
                continue
        filtered.append(b)

    total = len(filtered)
    # 按 created_at 降序分页
    filtered.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    data = []
    for b in page_items:
        breed = breeds.get(str(b.get("breed_id")), {})
        house = houses.get(str(b.get("house_id")), {})
        qty_initial = b.get("quantity_initial", 0) or 0
        qty_current = b.get("quantity_current", 0) or 0
        date_in = b.get("date_in")
        age_days = None
        if date_in:
            try:
                age_days = (date.today() - date.fromisoformat(str(date_in))).days + (b.get("age_day_in") or 1)
            except Exception:
                age_days = None
        data.append({
            "id": b.get("_record_id"),
            "batch_no": b.get("batch_no"),
            "batch_name": b.get("batch_name"),
            "breed_id": b.get("breed_id"),
            "breed_name": breed.get("breed_name"),
            "house_id": b.get("house_id"),
            "house_name": house.get("house_name"),
            "quantity_initial": qty_initial,
            "quantity_current": qty_current,
            "survival_rate": round(qty_current / qty_initial * 100, 2) if qty_initial else 0,
            "date_in": str(date_in) if date_in else None,
            "date_out": str(b.get("date_out")) if b.get("date_out") else None,
            "age_days": age_days,
            "status": b.get("status"),
            "responsible_person": b.get("responsible_person"),
            "pilot_flag": b.get("pilot_flag"),
        })
    return paginated_response(data, page, page_size, total)


@router.get("/{batch_id}")
async def get_batch_detail(batch_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """获取批次详情"""
    b = await repos.batch.get_by_id(batch_id)
    if not b:
        return error_response(404, "批次不存在")

    breed = await repos.breed.get_by_id(str(b.get("breed_id", ""))) if b.get("breed_id") else None
    house = await repos.house.get_by_id(str(b.get("house_id", ""))) if b.get("house_id") else None

    date_in = b.get("date_in")
    age_days = None
    if date_in:
        try:
            age_days = (date.today() - date.fromisoformat(str(date_in))).days + (b.get("age_day_in") or 1)
        except Exception:
            age_days = None
    qty_initial = b.get("quantity_initial", 0) or 0
    qty_current = b.get("quantity_current", 0) or 0
    survival_rate = round(qty_current / qty_initial * 100, 2) if qty_initial else 0

    return success_response({
        "id": b.get("_record_id"),
        "batch_no": b.get("batch_no"),
        "batch_name": b.get("batch_name"),
        "breed": {
            "id": breed.get("_record_id") if breed else None,
            "breed_name": breed.get("breed_name") if breed else None,
            "breed_code": breed.get("breed_code") if breed else None,
        },
        "house": {
            "id": house.get("_record_id") if house else None,
            "house_name": house.get("house_name") if house else None,
            "house_code": house.get("house_code") if house else None,
        },
        "quantity_initial": qty_initial,
        "quantity_current": qty_current,
        "survival_rate": survival_rate,
        "date_in": str(date_in) if date_in else None,
        "date_out": str(b.get("date_out")) if b.get("date_out") else None,
        "age_day_in": b.get("age_day_in"),
        "age_days": age_days,
        "source_type": b.get("source_type"),
        "status": b.get("status"),
        "responsible_person": b.get("responsible_person"),
        "pilot_flag": b.get("pilot_flag"),
    })


@router.get("/{batch_id}/lifecycle")
async def get_batch_lifecycle(batch_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """批次全生命周期数据聚合"""
    batch = await repos.batch.get_by_id(batch_id)
    if not batch:
        return error_response(404, "批次不存在")

    # 个体统计
    animals = await repos.animal.filter_by("batch_id", batch_id)
    status_distribution = {}
    for a in animals:
        s = a.get("status", 0)
        status_distribution[f"status_{s}"] = status_distribution.get(f"status_{s}", 0) + 1

    # 健康记录（死淘）
    health_records = await repos.health.filter_by("batch_id", batch_id)
    mortality_list = [h for h in health_records if h.get("mortality_flag") == 1]
    mortality = len(mortality_list)
    from collections import Counter
    cull_reasons = Counter(h.get("event_name") for h in mortality_list)

    # 最近操作
    all_ops = await repos.operation.filter_by("batch_id", batch_id)
    all_ops.sort(key=lambda x: x.get("op_date") or "", reverse=True)
    recent_ops = all_ops[:10]

    # 饲料消耗汇总
    feeds = await repos.feed.filter_by("batch_id", batch_id)
    feed_total = sum(float(f.get("feed_quantity", 0) or 0) for f in feeds)

    return success_response({
        "batch_id": batch_id,
        "batch_no": batch.get("batch_no"),
        "individual_count": {
            "total": len(animals),
            "status_distribution": status_distribution,
        },
        "mortality": {
            "total": mortality,
            "reasons": [{"reason": r, "count": c} for r, c in cull_reasons.items()],
        },
        "recent_operations": [
            {
                "id": o.get("_record_id"),
                "op_type": o.get("op_type"),
                "op_date": str(o.get("op_date")),
                "operator": o.get("operator"),
                "remark": o.get("remark"),
            }
            for o in recent_ops
        ],
        "feed_total": float(feed_total) if feed_total else 0,
    })


@router.get("/{batch_id}/growth-summary")
async def get_batch_growth_summary(batch_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """批次生长汇总"""
    batch = await repos.batch.get_by_id(batch_id)
    if not batch:
        return error_response(404, "批次不存在")

    # 获取该批次全部生长记录
    growth_records = await repos.growth.filter_by("batch_id", batch_id)
    growth_records.sort(key=lambda x: x.get("record_date") or "")

    # 每只动物的最新体重
    from collections import defaultdict
    animal_weights = defaultdict(list)
    for r in growth_records:
        animal_weights[r.get("animal_id")].append(r)

    latest_weights = []
    for records in animal_weights.values():
        records.sort(key=lambda x: x.get("record_date") or "")
        latest = records[-1]
        w = latest.get("weight")
        if w is not None:
            latest_weights.append(float(w))

    if latest_weights:
        avg_weight = sum(latest_weights) / len(latest_weights)
        min_weight = min(latest_weights)
        max_weight = max(latest_weights)
        variance = sum((w - avg_weight) ** 2 for w in latest_weights) / len(latest_weights)
        std_weight = variance ** 0.5
        uniformity = round((1 - std_weight / avg_weight) * 100, 2) if avg_weight else 0
    else:
        avg_weight = min_weight = max_weight = std_weight = uniformity = 0

    return success_response({
        "batch_id": batch_id,
        "batch_no": batch.get("batch_no"),
        "sample_size": len(latest_weights),
        "avg_weight": round(avg_weight, 3),
        "min_weight": round(min_weight, 3),
        "max_weight": round(max_weight, 3),
        "std_weight": round(std_weight, 3),
        "uniformity": uniformity,
        "record_count": len(growth_records),
    })


@router.get("/{batch_id}/performance")
async def get_batch_performance(batch_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """批次性能偏差"""
    batch = await repos.batch.get_by_id(batch_id)
    if not batch:
        return error_response(404, "批次不存在")

    breed = await repos.breed.get_by_id(str(batch.get("breed_id", ""))) if batch.get("breed_id") else None

    # 成活率
    qty_initial = batch.get("quantity_initial", 0) or 0
    qty_current = batch.get("quantity_current", 0) or 0
    survival_rate = round(qty_current / qty_initial * 100, 2) if qty_initial else 0
    survival_std = float(breed.get("survival_rate_std")) if breed and breed.get("survival_rate_std") else 0
    survival_deviation = round(survival_rate - survival_std, 2)

    # 日增重（基于最近两次称重）
    growth_records = await repos.growth.filter_by("batch_id", batch_id)
    growth_records.sort(key=lambda x: x.get("record_date") or "")
    if len(growth_records) >= 2:
        first = growth_records[0]
        last = growth_records[-1]
        try:
            days_diff = (date.fromisoformat(str(last.get("record_date"))) - date.fromisoformat(str(first.get("record_date")))).days
        except Exception:
            days_diff = 0
        weight_diff = float(last.get("weight", 0) or 0) - float(first.get("weight", 0) or 0)
        actual_daily_gain = round(weight_diff / days_diff, 3) if days_diff > 0 else 0
    else:
        actual_daily_gain = 0
    std_daily_gain = float(breed.get("daily_gain_std")) if breed and breed.get("daily_gain_std") else 0
    daily_gain_deviation = round(actual_daily_gain - std_daily_gain, 3)
    daily_gain_deviation_pct = round(daily_gain_deviation / std_daily_gain * 100, 2) if std_daily_gain else 0

    # 料肉比
    feeds = await repos.feed.filter_by("batch_id", batch_id)
    feed_total = sum(float(f.get("feed_quantity", 0) or 0) for f in feeds)
    weight_gain = float(growth_records[-1].get("weight", 0) or 0) - float(growth_records[0].get("weight", 0) or 0) if len(growth_records) >= 2 else 0
    actual_fmr = round(float(feed_total) / weight_gain, 3) if weight_gain > 0 else 0
    std_fmr = float(breed.get("feed_meat_ratio")) if breed and breed.get("feed_meat_ratio") else 0
    fmr_deviation = round(actual_fmr - std_fmr, 3)

    return success_response({
        "batch_id": batch_id,
        "batch_no": batch.get("batch_no"),
        "survival_rate": {
            "actual": survival_rate,
            "standard": survival_std if survival_std else None,
            "deviation": survival_deviation,
        },
        "daily_gain": {
            "actual": actual_daily_gain,
            "standard": std_daily_gain,
            "deviation": daily_gain_deviation,
            "deviation_pct": daily_gain_deviation_pct,
        },
        "feed_meat_ratio": {
            "actual": actual_fmr,
            "standard": std_fmr,
            "deviation": fmr_deviation,
        },
    })


@router.get("/{batch_id}/profit")
async def get_batch_profit(batch_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """批次利润分析"""
    batch = await repos.batch.get_by_id(batch_id)
    if not batch:
        return error_response(404, "批次不存在")

    # 尝试取最新利润分析
    profits = await repos.profit.filter_by("batch_id", batch_id)
    profits.sort(key=lambda x: x.get("analysis_date") or "", reverse=True)
    if profits:
        profit = profits[0]
        return success_response({
            "batch_id": batch_id,
            "batch_no": batch.get("batch_no"),
            "total_revenue": float(profit.get("total_revenue", 0) or 0),
            "total_cost": float(profit.get("total_cost", 0) or 0),
            "gross_profit": float(profit.get("gross_profit", 0) or 0),
            "profit_margin": float(profit.get("profit_margin", 0) or 0),
            "cost_per_bird": float(profit.get("cost_per_bird")) if profit.get("cost_per_bird") else None,
            "revenue_per_bird": float(profit.get("revenue_per_bird")) if profit.get("revenue_per_bird") else None,
            "analysis_date": str(profit.get("analysis_date")),
        })

    # 动态计算
    financials = await repos.financial.filter_by("batch_id", batch_id)
    total_revenue = sum(float(f.get("amount", 0) or 0) for f in financials if f.get("transaction_type") == 1)
    total_cost = sum(float(f.get("amount", 0) or 0) for f in financials if f.get("transaction_type") == 2)
    gross_profit = total_revenue - total_cost
    profit_margin = round(gross_profit / total_revenue * 100, 2) if total_revenue else 0
    bird_count = batch.get("quantity_initial") or 1

    return success_response({
        "batch_id": batch_id,
        "batch_no": batch.get("batch_no"),
        "total_revenue": float(total_revenue),
        "total_cost": float(total_cost),
        "gross_profit": round(gross_profit, 2),
        "profit_margin": profit_margin,
        "cost_per_bird": round(float(total_cost) / bird_count, 2),
        "revenue_per_bird": round(float(total_revenue) / bird_count, 2),
        "profit_per_bird": round(gross_profit / bird_count, 2),
        "computed": True,
    })
