"""溯源查询 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, asc

from app.database import get_db
from app.models import TraceabilityChain, AnimalIndividual, Batch, Breed, House, HealthRecord
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/traceability", tags=["溯源查询"])


@router.get("/completeness")
def get_traceability_completeness(
    batch_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """批次溯源完整度（batch_id为可选，不传则返回全部批次的完整度统计）"""
    if batch_id is not None:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return error_response(404, "批次不存在")

        stage_text_map = {1: "种鸡", 2: "种蛋", 3: "孵化", 4: "鸡苗", 5: "养殖", 6: "出栏", 7: "销售"}
        chain_items = db.query(TraceabilityChain).filter(TraceabilityChain.batch_id == batch_id).all()

        stage_details = []
        total_stages = 7
        covered = set()
        for stage in range(1, 8):
            nodes = [c for c in chain_items if c.stage == stage]
            is_complete = len(nodes) > 0
            if is_complete:
                covered.add(stage)
            stage_details.append({
                "stage": stage,
                "stage_text": stage_text_map.get(stage, "未知"),
                "node_count": len(nodes),
                "is_complete": is_complete,
            })

        completeness_pct = round(len(covered) / total_stages * 100, 2)

        return success_response({
            "batch_id": batch_id,
            "batch_no": batch.batch_no,
            "completeness": {
                "total_stages": total_stages,
                "covered_stages": len(covered),
                "completeness_pct": completeness_pct,
                "missing_stages": [stage_text_map.get(s, str(s)) for s in set(range(1, 8)) - covered],
            },
            "stage_details": stage_details,
        })

    # 不传batch_id：返回全量批次的完整度统计
    # 使用分页防止OOM
    batches = db.query(Batch).limit(500).all()
    if not batches:
        return success_response({"message": "暂无批次数据", "summary": {"total_batches": 0, "avg_completeness": 0}})

    # 优化：使用IN查询一次性拉取所有chain数据，避免N+1
    batch_ids = [b.id for b in batches]
    all_chains = db.query(TraceabilityChain).filter(TraceabilityChain.batch_id.in_(batch_ids)).all()
    # 按batch_id分组
    chains_by_batch = {}
    for c in all_chains:
        chains_by_batch.setdefault(c.batch_id, []).append(c)

    # 汇总各批次的溯源完整度
    total_pct = 0
    items = []
    for b in batches:
        chain = chains_by_batch.get(b.id, [])
        expected = {1, 2, 3, 4, 5, 6, 7}
        covered = {c.stage for c in chain}
        pct = round(len(covered & expected) / len(expected) * 100, 2)
        total_pct += pct
        items.append({
            "batch_id": b.id,
            "batch_no": b.batch_no,
            "completeness_pct": pct,
            "covered_stages": len(covered & expected),
        })
    avg = round(total_pct / len(batches), 2) if batches else 0

    return success_response({
        "summary": {
            "total_batches": len(batches),
            "avg_completeness": avg,
        },
        "batches": items,
    })


@router.get("/{code}")
def trace_by_code(code: str, db: Session = Depends(get_db)):
    """溯源码查询"""
    # 先尝试按个体溯源码查询
    animal = db.query(AnimalIndividual, Batch, Breed, House).join(Batch, AnimalIndividual.batch_id == Batch.id).join(Breed, AnimalIndividual.breed_id == Breed.id).join(House, AnimalIndividual.house_id == House.id).filter(AnimalIndividual.traceability_code == code).first()

    if animal:
        ai, batch, breed, house = animal
        trace_type = 2
        trace_type_text = "个体溯源"
    else:
        # 尝试按批次溯源码查询
        batch = db.query(Batch, Breed, House).join(Breed, Batch.breed_id == Breed.id).join(House, Batch.house_id == House.id).filter(Batch.batch_no == code).first()
        if batch:
            b, breed, house = batch
            trace_type = 1
            trace_type_text = "批次溯源"
            ai = None
            batch = b
        else:
            return error_response(404, "溯源码不存在")

    # 构建溯源链
    batch_id = batch.id
    chain_items = db.query(TraceabilityChain).filter(TraceabilityChain.batch_id == batch_id).order_by(asc(TraceabilityChain.event_date)).all()

    stage_text_map = {
        1: "种鸡", 2: "种蛋", 3: "孵化", 4: "鸡苗", 5: "养殖", 6: "出栏", 7: "销售"
    }

    chain = []
    for tc in chain_items:
        chain.append({
            "stage": tc.stage,
            "stage_text": stage_text_map.get(tc.stage, "未知"),
            "event_date": str(tc.event_date) if tc.event_date else None,
            "event_desc": tc.event_desc,
            "location": tc.location,
            "operator": tc.operator,
        })

    # 补充健康记录作为溯源节点
    health_records = db.query(HealthRecord).filter(HealthRecord.batch_id == batch_id).order_by(asc(HealthRecord.record_date)).all()
    for hr in health_records:
        chain.append({
            "stage": 5,
            "stage_text": "养殖",
            "event_date": str(hr.record_date),
            "event_desc": f"{hr.event_name}: {hr.drug_name or ''}",
            "location": house.house_name if house else None,
            "operator": hr.veterinarian,
        })

    chain.sort(key=lambda x: x["event_date"] or "")

    # 完整度计算
    expected_stages = {4, 5, 6, 7}  # 鸡苗、养殖、出栏、销售
    covered = set(c["stage"] for c in chain)
    total_stages = len(expected_stages)
    covered_stages = len(covered & expected_stages)
    completeness = round(covered_stages / total_stages * 100, 2) if total_stages else 0

    result = {
        "traceability_code": code,
        "trace_type": trace_type,
        "trace_type_text": trace_type_text,
        "batch": {
            "batch_no": batch.batch_no,
            "house_name": house.house_name if house else None,
            "responsible_person": batch.responsible_person,
        },
        "chain": chain,
        "completeness": {
            "total_stages": total_stages,
            "covered_stages": covered_stages,
            "completeness_pct": completeness,
            "missing_stages": [stage_text_map.get(s, str(s)) for s in expected_stages - covered],
        },
    }

    if ai:
        result["animal"] = {
            "animal_no": ai.animal_no,
            "breed_name": breed.breed_name if breed else None,
            "gender": ai.gender,
            "gender_text": "公" if ai.gender == 1 else ("母" if ai.gender == 2 else "未知"),
            "date_birth": str(ai.date_birth) if ai.date_birth else None,
            "date_in": str(ai.date_in) if ai.date_in else None,
        }

    return success_response(result)
