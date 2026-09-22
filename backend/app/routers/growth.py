"""个体生长曲线 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from datetime import date

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/individuals", tags=["个体生长曲线"])


@router.get("/{animal_id}/growth-curve")
async def get_individual_growth_curve(
    animal_id: str,
    repos: RepositoryFactory = Depends(get_repositories),
):
    """获取单只鸡的生长曲线"""
    ai = await repos.animal.get_by_id(animal_id)
    if not ai:
        return error_response(404, "个体不存在")

    batch = await repos.batch.get_by_id(str(ai.get("batch_id", ""))) if ai.get("batch_id") else None
    breed = await repos.breed.get_by_id(str(ai.get("breed_id", ""))) if ai.get("breed_id") else None

    # 获取生长记录
    all_growth = await repos.growth.filter_by("animal_id", animal_id)
    all_growth.sort(key=lambda x: x.get("record_date") or "")

    if not all_growth:
        return success_response({
            "animal": {
                "id": ai.get("_record_id"),
                "animal_no": ai.get("animal_no"),
                "breed_name": breed.get("breed_name") if breed else None,
            },
            "growth_data": [],
            "standard_curve": [],
        })

    # 实际生长数据
    growth_data = []
    for r in all_growth:
        growth_data.append({
            "record_date": str(r.get("record_date")),
            "age_days": r.get("age_days"),
            "weight": float(r.get("weight", 0) or 0),
            "body_length": float(r.get("body_length")) if r.get("body_length") else None,
            "chest_girth": float(r.get("chest_girth")) if r.get("chest_girth") else None,
            "shank_length": float(r.get("shank_length")) if r.get("shank_length") else None,
            "recorder": r.get("recorder"),
        })

    # 品种标准曲线
    standard_curve = []
    weight_in = float(ai.get("weight_in")) if ai.get("weight_in") else 0
    daily_gain = float(breed.get("daily_gain_std")) if breed and breed.get("daily_gain_std") else 0
    if daily_gain:
        max_age = max(r.get("age_days", 0) or 0 for r in all_growth)
        step = max(1, (max_age - (ai.get("age_day_in") or 1)) // 20)
        for age in range(ai.get("age_day_in") or 1, max_age + 1, step):
            standard_curve.append({
                "age_days": age,
                "weight": round(weight_in + daily_gain * (age - (ai.get("age_day_in") or 1)), 3),
            })

    # 日增重偏差分析
    deviations = []
    for i in range(1, len(all_growth)):
        prev = all_growth[i - 1]
        curr = all_growth[i]
        try:
            days_diff = (date.fromisoformat(str(curr.get("record_date"))) - date.fromisoformat(str(prev.get("record_date")))).days
        except Exception:
            days_diff = 0
        if days_diff > 0:
            actual_adg = (float(curr.get("weight", 0) or 0) - float(prev.get("weight", 0) or 0)) / days_diff
            std_adg = daily_gain
            deviation_pct = round((actual_adg - std_adg) / std_adg * 100, 2) if std_adg else 0
            deviations.append({
                "period": f"{prev.get('record_date')} ~ {curr.get('record_date')}",
                "actual_adg": round(actual_adg, 3),
                "standard_adg": std_adg,
                "deviation_pct": deviation_pct,
            })

    return success_response({
        "animal": {
            "id": ai.get("_record_id"),
            "animal_no": ai.get("animal_no"),
            "breed_name": breed.get("breed_name") if breed else None,
            "gender": ai.get("gender"),
            "date_in": str(ai.get("date_in")),
            "weight_in": float(ai.get("weight_in")) if ai.get("weight_in") else None,
        },
        "growth_data": growth_data,
        "standard_curve": standard_curve,
        "deviation_analysis": deviations,
    })


@router.get("/{animal_id}/growth-records")
async def list_growth_records(
    animal_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询个体生长记录列表"""
    ai = await repos.animal.get_by_id(animal_id)
    if not ai:
        return error_response(404, "个体不存在")

    records = await repos.growth.filter_by("animal_id", animal_id)
    records.sort(key=lambda x: x.get("record_date") or "", reverse=True)
    total = len(records)
    start = (page - 1) * page_size
    page_items = records[start : start + page_size]

    data = [
        {
            "id": r.get("_record_id"),
            "record_date": str(r.get("record_date")),
            "age_days": r.get("age_days"),
            "weight": float(r.get("weight", 0) or 0),
            "body_length": float(r.get("body_length")) if r.get("body_length") else None,
            "chest_girth": float(r.get("chest_girth")) if r.get("chest_girth") else None,
            "shank_length": float(r.get("shank_length")) if r.get("shank_length") else None,
            "recorder": r.get("recorder"),
        }
        for r in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("")
async def list_individuals(
    batch_id: Optional[str] = Query(None),
    house_id: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询动物个体列表"""
    # 预加载关联表
    batches_map = {b.get("_record_id"): b for b in await repos.batch.list_all()}
    houses_map = {h.get("_record_id"): h for h in await repos.house.list_all()}
    breeds_map = {b.get("_record_id"): b for b in await repos.breed.list_all()}

    # 获取动物数据
    if batch_id:
        animals = await repos.animal.filter_by("batch_id", batch_id)
    elif house_id:
        animals = await repos.animal.filter_by("house_id", house_id)
    else:
        animals = await repos.animal.list_all()

    # 内存过滤
    filtered = []
    for a in animals:
        if house_id is not None and a.get("house_id") != house_id:
            continue
        if status is not None and a.get("status") != status:
            continue
        if keyword:
            kw = keyword.lower()
            if not (
                kw in (a.get("animal_no") or "").lower()
                or kw in (a.get("traceability_code") or "").lower()
            ):
                continue
        filtered.append(a)

    total = len(filtered)
    filtered.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    data = [
        {
            "id": a.get("_record_id"),
            "animal_no": a.get("animal_no"),
            "batch_id": a.get("batch_id"),
            "batch_no": batches_map.get(str(a.get("batch_id")), {}).get("batch_no"),
            "house_id": a.get("house_id"),
            "house_name": houses_map.get(str(a.get("house_id")), {}).get("house_name"),
            "breed_name": breeds_map.get(str(a.get("breed_id")), {}).get("breed_name"),
            "gender": a.get("gender"),
            "status": a.get("status"),
            "date_in": str(a.get("date_in")),
            "traceability_code": a.get("traceability_code"),
        }
        for a in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/{animal_id}/pedigree")
async def get_pedigree(animal_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """获取个体系谱（3代）"""
    async def get_animal_info(aid: Optional[str]):
        if not aid:
            return None
        a = await repos.animal.get_by_id(aid)
        if not a:
            return None
        return {"id": a.get("_record_id"), "animal_no": a.get("animal_no"), "gender": a.get("gender")}

    animal = await repos.animal.get_by_id(animal_id)
    if not animal:
        return error_response(404, "个体不存在")

    dam_id = animal.get("dam_id")
    sire_id = animal.get("sire_id")

    dam = await get_animal_info(str(dam_id)) if dam_id else None
    sire = await get_animal_info(str(sire_id)) if sire_id else None

    granddam_dam = None
    grandsire_dam = None
    if dam_id:
        dam_record = await repos.animal.get_by_id(str(dam_id))
        if dam_record:
            granddam_dam = await get_animal_info(str(dam_record.get("dam_id"))) if dam_record.get("dam_id") else None
            grandsire_dam = await get_animal_info(str(dam_record.get("sire_id"))) if dam_record.get("sire_id") else None

    granddam_sire = None
    grandsire_sire = None
    if sire_id:
        sire_record = await repos.animal.get_by_id(str(sire_id))
        if sire_record:
            granddam_sire = await get_animal_info(str(sire_record.get("dam_id"))) if sire_record.get("dam_id") else None
            grandsire_sire = await get_animal_info(str(sire_record.get("sire_id"))) if sire_record.get("sire_id") else None

    return success_response({
        "self": await get_animal_info(animal_id),
        "dam": dam,
        "sire": sire,
        "granddam_dam": granddam_dam,
        "grandsire_dam": grandsire_dam,
        "granddam_sire": granddam_sire,
        "grandsire_sire": grandsire_sire,
    })
