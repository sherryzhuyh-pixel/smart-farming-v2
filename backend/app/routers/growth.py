"""个体生长曲线 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from app.database import get_db
from app.models import GrowthRecord, AnimalIndividual, Batch, Breed
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/individuals", tags=["个体生长曲线"])


@router.get("/{animal_id}/growth-curve")
def get_individual_growth_curve(
    animal_id: int,
    db: Session = Depends(get_db),
):
    """获取单只鸡的生长曲线"""
    animal = db.query(AnimalIndividual, Batch, Breed).join(Batch, AnimalIndividual.batch_id == Batch.id).join(Breed, AnimalIndividual.breed_id == Breed.id).filter(AnimalIndividual.id == animal_id).first()
    if not animal:
        return error_response(404, "个体不存在")
    ai, batch, breed = animal

    records = db.query(GrowthRecord).filter(GrowthRecord.animal_id == animal_id).order_by(asc(GrowthRecord.record_date)).all()
    if not records:
        return success_response({
            "animal": {"id": ai.id, "animal_no": ai.animal_no, "breed_name": breed.breed_name},
            "growth_data": [],
            "standard_curve": [],
        })

    # 实际生长数据
    growth_data = []
    for r in records:
        growth_data.append({
            "record_date": str(r.record_date),
            "age_days": r.age_days,
            "weight": float(r.weight),
            "body_length": float(r.body_length) if r.body_length else None,
            "chest_girth": float(r.chest_girth) if r.chest_girth else None,
            "shank_length": float(r.shank_length) if r.shank_length else None,
            "recorder": r.recorder,
        })

    # 品种标准曲线（基于daily_gain_std和入栏体重）
    standard_curve = []
    weight_in = float(ai.weight_in) if ai.weight_in else 0
    daily_gain = float(breed.daily_gain_std) if breed.daily_gain_std else 0
    if daily_gain:
        max_age = max(r.age_days for r in records)
        for age in range(ai.age_day_in, max_age + 1, max(1, (max_age - ai.age_day_in) // 20)):
            standard_curve.append({
                "age_days": age,
                "weight": round(weight_in + daily_gain * (age - ai.age_day_in), 3),
            })

    # 日增重偏差分析
    deviations = []
    for i in range(1, len(records)):
        prev = records[i - 1]
        curr = records[i]
        days_diff = (curr.record_date - prev.record_date).days
        if days_diff > 0:
            actual_adg = (float(curr.weight) - float(prev.weight)) / days_diff
            std_adg = daily_gain
            deviation_pct = round((actual_adg - std_adg) / std_adg * 100, 2) if std_adg else 0
            deviations.append({
                "period": f"{prev.record_date} ~ {curr.record_date}",
                "actual_adg": round(actual_adg, 3),
                "standard_adg": std_adg,
                "deviation_pct": deviation_pct,
            })

    return success_response({
        "animal": {
            "id": ai.id,
            "animal_no": ai.animal_no,
            "breed_name": breed.breed_name,
            "gender": ai.gender,
            "date_in": str(ai.date_in),
            "weight_in": float(ai.weight_in) if ai.weight_in else None,
        },
        "growth_data": growth_data,
        "standard_curve": standard_curve,
        "deviation_analysis": deviations,
    })


@router.get("/{animal_id}/growth-records")
def list_growth_records(
    animal_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询个体生长记录列表"""
    animal = db.query(AnimalIndividual).filter(AnimalIndividual.id == animal_id).first()
    if not animal:
        return error_response(404, "个体不存在")
    query = db.query(GrowthRecord).filter(GrowthRecord.animal_id == animal_id)
    total = query.count()
    records = query.order_by(desc(GrowthRecord.record_date)).offset((page - 1) * page_size).limit(page_size).all()
    data = [
        {
            "id": r.id,
            "record_date": str(r.record_date),
            "age_days": r.age_days,
            "weight": float(r.weight),
            "body_length": float(r.body_length) if r.body_length else None,
            "chest_girth": float(r.chest_girth) if r.chest_girth else None,
            "shank_length": float(r.shank_length) if r.shank_length else None,
            "recorder": r.recorder,
        }
        for r in records
    ]
    return paginated_response(data, page, page_size, total)


@router.get("")
def list_individuals(
    batch_id: Optional[int] = Query(None),
    house_id: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询动物个体列表"""
    query = db.query(AnimalIndividual, Batch.batch_no, House.house_name, Breed.breed_name).join(Batch, AnimalIndividual.batch_id == Batch.id).join(House, AnimalIndividual.house_id == House.id).join(Breed, AnimalIndividual.breed_id == Breed.id)
    if batch_id:
        query = query.filter(AnimalIndividual.batch_id == batch_id)
    if house_id:
        query = query.filter(AnimalIndividual.house_id == house_id)
    if status is not None:
        query = query.filter(AnimalIndividual.status == status)
    if keyword:
        query = query.filter(
            (AnimalIndividual.animal_no.contains(keyword)) |
            (AnimalIndividual.traceability_code.contains(keyword))
        )
    total = query.count()
    items = query.order_by(desc(AnimalIndividual.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    data = [
        {
            "id": ai.id,
            "animal_no": ai.animal_no,
            "batch_id": ai.batch_id,
            "batch_no": bn,
            "house_id": ai.house_id,
            "house_name": hn,
            "breed_name": brn,
            "gender": ai.gender,
            "status": ai.status,
            "date_in": str(ai.date_in),
            "traceability_code": ai.traceability_code,
        }
        for ai, bn, hn, brn in items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/{animal_id}/pedigree")
def get_pedigree(animal_id: int, db: Session = Depends(get_db)):
    """获取个体系谱（3代）"""
    def get_animal_info(aid):
        if not aid:
            return None
        a = db.query(AnimalIndividual).filter(AnimalIndividual.id == aid).first()
        if not a:
            return None
        return {"id": a.id, "animal_no": a.animal_no, "gender": a.gender}

    animal = db.query(AnimalIndividual).filter(AnimalIndividual.id == animal_id).first()
    if not animal:
        return error_response(404, "个体不存在")

    return success_response({
        "self": get_animal_info(animal.id),
        "dam": get_animal_info(animal.dam_id),
        "sire": get_animal_info(animal.sire_id),
        "granddam_dam": get_animal_info(db.query(AnimalIndividual.dam_id).filter(AnimalIndividual.id == animal.dam_id).scalar()) if animal.dam_id else None,
        "grandsire_dam": get_animal_info(db.query(AnimalIndividual.sire_id).filter(AnimalIndividual.id == animal.dam_id).scalar()) if animal.dam_id else None,
        "granddam_sire": get_animal_info(db.query(AnimalIndividual.dam_id).filter(AnimalIndividual.id == animal.sire_id).scalar()) if animal.sire_id else None,
        "grandsire_sire": get_animal_info(db.query(AnimalIndividual.sire_id).filter(AnimalIndividual.id == animal.sire_id).scalar()) if animal.sire_id else None,
    })
