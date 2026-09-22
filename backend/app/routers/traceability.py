"""溯源查询 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/traceability", tags=["溯源查询"])

stage_text_map = {1: "种鸡", 2: "种蛋", 3: "孵化", 4: "鸡苗", 5: "养殖", 6: "出栏", 7: "销售"}


@router.get("/completeness")
async def get_traceability_completeness(
    batch_id: Optional[str] = Query(None),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """批次溯源完整度"""
    if batch_id is not None:
        batch = await repos.batch.get_by_id(batch_id)
        if not batch:
            return error_response(404, "批次不存在")

        chains = await repos.traceability.filter_by("batch_id", batch_id)

        stage_details = []
        total_stages = 7
        covered = set()
        for stage in range(1, 8):
            nodes = [c for c in chains if c.get("stage") == stage]
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
            "batch_no": batch.get("batch_no"),
            "completeness": {
                "total_stages": total_stages,
                "covered_stages": len(covered),
                "completeness_pct": completeness_pct,
                "missing_stages": [stage_text_map.get(s, str(s)) for s in set(range(1, 8)) - covered],
            },
            "stage_details": stage_details,
        })

    # 不传 batch_id：返回全量批次的完整度统计
    batches = await repos.batch.list_all()
    batches = batches[:500]
    if not batches:
        return success_response({"message": "暂无批次数据", "summary": {"total_batches": 0, "avg_completeness": 0}})

    batch_ids = [b.get("_record_id") for b in batches]
    all_chains = await repos.traceability.list_all()
    chains_by_batch = {}
    for c in all_chains:
        bid = c.get("batch_id")
        if bid in batch_ids:
            chains_by_batch.setdefault(bid, []).append(c)

    total_pct = 0
    items = []
    for b in batches:
        bid = b.get("_record_id")
        chain = chains_by_batch.get(bid, [])
        expected = {1, 2, 3, 4, 5, 6, 7}
        covered = {c.get("stage") for c in chain}
        pct = round(len(covered & expected) / len(expected) * 100, 2)
        total_pct += pct
        items.append({
            "batch_id": bid,
            "batch_no": b.get("batch_no"),
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
async def trace_by_code(code: str, repos: RepositoryFactory = Depends(get_repositories)):
    """溯源码查询"""
    # 先尝试按个体溯源码查询
    animals = await repos.animal.list_all()
    animal = next((a for a in animals if a.get("traceability_code") == code), None)

    batches_map = {b.get("_record_id"): b for b in await repos.batch.list_all()}
    breeds_map = {b.get("_record_id"): b for b in await repos.breed.list_all()}
    houses_map = {h.get("_record_id"): h for h in await repos.house.list_all()}

    if animal:
        batch = batches_map.get(str(animal.get("batch_id", "")))
        breed = breeds_map.get(str(animal.get("breed_id", "")))
        house = houses_map.get(str(batch.get("house_id")) if batch else "")
        trace_type = 2
        trace_type_text = "个体溯源"
        ai = animal
    else:
        # 尝试按批次溯源码查询
        batch = next((b for b in batches_map.values() if b.get("batch_no") == code), None)
        if batch:
            breed = breeds_map.get(str(batch.get("breed_id", "")))
            house = houses_map.get(str(batch.get("house_id", "")))
            trace_type = 1
            trace_type_text = "批次溯源"
            ai = None
        else:
            return error_response(404, "溯源码不存在")

    # 构建溯源链
    batch_id = batch.get("_record_id")
    all_chains = await repos.traceability.list_all()
    chain_items = [c for c in all_chains if c.get("batch_id") == batch_id]
    chain_items.sort(key=lambda x: x.get("event_date") or "")

    chain = []
    for tc in chain_items:
        chain.append({
            "stage": tc.get("stage"),
            "stage_text": stage_text_map.get(tc.get("stage"), "未知"),
            "event_date": str(tc.get("event_date")) if tc.get("event_date") else None,
            "event_desc": tc.get("event_desc"),
            "location": tc.get("location"),
            "operator": tc.get("operator"),
        })

    # 补充健康记录作为溯源节点
    all_health = await repos.health.list_all()
    health_records = [h for h in all_health if h.get("batch_id") == batch_id]
    health_records.sort(key=lambda x: x.get("record_date") or "")
    for hr in health_records:
        chain.append({
            "stage": 5,
            "stage_text": "养殖",
            "event_date": str(hr.get("record_date")),
            "event_desc": f"{hr.get('event_name')}: {hr.get('drug_name') or ''}",
            "location": house.get("house_name") if house else None,
            "operator": hr.get("veterinarian"),
        })

    chain.sort(key=lambda x: x["event_date"] or "")

    # 完整度计算
    expected_stages = {4, 5, 6, 7}
    covered = set(c["stage"] for c in chain)
    total_stages = len(expected_stages)
    covered_stages = len(covered & expected_stages)
    completeness = round(covered_stages / total_stages * 100, 2) if total_stages else 0

    result = {
        "traceability_code": code,
        "trace_type": trace_type,
        "trace_type_text": trace_type_text,
        "batch": {
            "batch_no": batch.get("batch_no"),
            "house_name": house.get("house_name") if house else None,
            "responsible_person": batch.get("responsible_person"),
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
            "animal_no": ai.get("animal_no"),
            "breed_name": breed.get("breed_name") if breed else None,
            "gender": ai.get("gender"),
            "gender_text": "公" if ai.get("gender") == 1 else ("母" if ai.get("gender") == 2 else "未知"),
            "date_birth": str(ai.get("date_birth")) if ai.get("date_birth") else None,
            "date_in": str(ai.get("date_in")) if ai.get("date_in") else None,
        }

    return success_response(result)
