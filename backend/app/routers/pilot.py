"""中试效果对比 API (Feishu Base 版本)"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from collections import defaultdict

from app.repositories import get_repositories, RepositoryFactory
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/pilots", tags=["中试效果对比"])


@router.get("")
async def list_pilot_projects(
    status: Optional[int] = Query(None),
    project_type: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询中试项目列表"""
    projects = await repos.pilot_project.list_all()
    if status is not None:
        projects = [p for p in projects if p.get("status") == status]
    if project_type is not None:
        projects = [p for p in projects if p.get("project_type") == project_type]

    total = len(projects)
    projects.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = projects[start : start + page_size]

    data = [
        {
            "id": p.get("_record_id"),
            "project_code": p.get("project_code"),
            "project_name": p.get("project_name"),
            "project_type": p.get("project_type"),
            "tech_partner": p.get("tech_partner"),
            "channel_partner": p.get("channel_partner"),
            "target_scale": p.get("target_scale"),
            "phase": p.get("phase"),
            "status": p.get("status"),
            "start_date": str(p.get("start_date")) if p.get("start_date") else None,
            "end_date": str(p.get("end_date")) if p.get("end_date") else None,
            "principal": p.get("principal"),
        }
        for p in page_items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/{project_id}")
async def get_pilot_project(project_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """获取中试项目详情"""
    project = await repos.pilot_project.get_by_id(project_id)
    if not project:
        return error_response(404, "中试项目不存在")

    # 实验组/对照组批次
    batches_map = {b.get("_record_id"): b for b in await repos.batch.list_all()}
    breeds_map = {b.get("_record_id"): b for b in await repos.breed.list_all()}

    pilot_batches_all = await repos.pilot_batch.list_all()
    pilot_batches = [pb for pb in pilot_batches_all if pb.get("pilot_project_id") == project_id]

    experiment_batches = []
    control_batches = []
    for pb in pilot_batches:
        batch = batches_map.get(str(pb.get("batch_id")), {})
        breed = breeds_map.get(str(batch.get("breed_id")), {})
        info = {
            "id": pb.get("_record_id"),
            "batch_id": pb.get("batch_id"),
            "batch_no": batch.get("batch_no"),
            "breed_name": breed.get("breed_name"),
            "group_type": pb.get("group_type"),
            "treatment_desc": pb.get("treatment_desc"),
            "dosage": pb.get("dosage"),
            "frequency": pb.get("frequency"),
            "start_date": str(pb.get("start_date")) if pb.get("start_date") else None,
            "end_date": str(pb.get("end_date")) if pb.get("end_date") else None,
        }
        if pb.get("group_type") == 1:
            experiment_batches.append(info)
        elif pb.get("group_type") == 2:
            control_batches.append(info)

    return success_response({
        "id": project.get("_record_id"),
        "project_code": project.get("project_code"),
        "project_name": project.get("project_name"),
        "project_type": project.get("project_type"),
        "description": project.get("description"),
        "tech_partner": project.get("tech_partner"),
        "channel_partner": project.get("channel_partner"),
        "target_scale": project.get("target_scale"),
        "phase": project.get("phase"),
        "status": project.get("status"),
        "start_date": str(project.get("start_date")) if project.get("start_date") else None,
        "end_date": str(project.get("end_date")) if project.get("end_date") else None,
        "principal": project.get("principal"),
        "experiment_batches": experiment_batches,
        "control_batches": control_batches,
    })


@router.get("/{project_id}/comparison")
async def get_pilot_comparison(project_id: str, repos: RepositoryFactory = Depends(get_repositories)):
    """中试效果对比"""
    project = await repos.pilot_project.get_by_id(project_id)
    if not project:
        return error_response(404, "中试项目不存在")

    # 获取实验组和对照组的指标
    indicators_all = await repos.pilot_indicator.list_all()
    indicators = [i for i in indicators_all if i.get("pilot_project_id") == project_id]
    indicators.sort(key=lambda x: x.get("record_date") or "")

    batches_map = {b.get("_record_id"): b.get("batch_no") for b in await repos.batch.list_all()}

    # 获取 pilot_batch 的 group_type 映射
    pilot_batches_all = await repos.pilot_batch.list_all()
    pb_map = {pb.get("batch_id"): pb.get("group_type") for pb in pilot_batches_all if pb.get("pilot_project_id") == project_id}

    exp_data = defaultdict(list)
    ctrl_data = defaultdict(list)

    for ind in indicators:
        group = pb_map.get(ind.get("batch_id"))
        item = {
            "record_date": str(ind.get("record_date")),
            "indicator_type": ind.get("indicator_type"),
            "indicator_name": ind.get("indicator_name"),
            "value": float(ind.get("value", 0) or 0),
            "unit": ind.get("unit"),
            "batch_no": batches_map.get(str(ind.get("batch_id"))),
        }
        key = ind.get("indicator_type")
        if group == 1:
            exp_data[key].append(item)
        elif group == 2:
            ctrl_data[key].append(item)

    # 计算均值对比
    comparison = []
    for ind_type in set(list(exp_data.keys()) + list(ctrl_data.keys())):
        exp_values = [i["value"] for i in exp_data[ind_type]]
        ctrl_values = [i["value"] for i in ctrl_data[ind_type]]
        exp_avg = round(sum(exp_values) / len(exp_values), 4) if exp_values else None
        ctrl_avg = round(sum(ctrl_values) / len(ctrl_values), 4) if ctrl_values else None
        diff_pct = round((exp_avg - ctrl_avg) / ctrl_avg * 100, 2) if ctrl_avg and exp_avg else None

        comparison.append({
            "indicator_type": ind_type,
            "indicator_name": exp_data[ind_type][0]["indicator_name"] if exp_data[ind_type] else (ctrl_data[ind_type][0]["indicator_name"] if ctrl_data[ind_type] else ""),
            "experiment_avg": exp_avg,
            "control_avg": ctrl_avg,
            "difference": round(exp_avg - ctrl_avg, 4) if exp_avg and ctrl_avg else None,
            "difference_pct": diff_pct,
        })

    # 生长曲线对比
    exp_batch_ids = [pb.get("batch_id") for pb in pilot_batches_all if pb.get("pilot_project_id") == project_id and pb.get("group_type") == 1]
    ctrl_batch_ids = [pb.get("batch_id") for pb in pilot_batches_all if pb.get("pilot_project_id") == project_id and pb.get("group_type") == 2]

    exp_growth = []
    ctrl_growth = []
    all_growth = await repos.growth.list_all()
    if exp_batch_ids:
        exp_gr = [g for g in all_growth if g.get("batch_id") in exp_batch_ids]
        exp_gr.sort(key=lambda x: x.get("record_date") or "")
        for gr in exp_gr:
            exp_growth.append({"record_date": str(gr.get("record_date")), "age_days": gr.get("age_days"), "weight": float(gr.get("weight", 0) or 0)})
    if ctrl_batch_ids:
        ctrl_gr = [g for g in all_growth if g.get("batch_id") in ctrl_batch_ids]
        ctrl_gr.sort(key=lambda x: x.get("record_date") or "")
        for gr in ctrl_gr:
            ctrl_growth.append({"record_date": str(gr.get("record_date")), "age_days": gr.get("age_days"), "weight": float(gr.get("weight", 0) or 0)})

    return success_response({
        "project_id": project_id,
        "project_name": project.get("project_name"),
        "comparison": comparison,
        "growth_curve": {
            "experiment": exp_growth[:100],
            "control": ctrl_growth[:100],
        },
    })


@router.get("/{project_id}/indicators")
async def list_pilot_indicators(
    project_id: str,
    indicator_type: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """查询中试指标列表"""
    indicators = await repos.pilot_indicator.list_all()
    indicators = [i for i in indicators if i.get("pilot_project_id") == project_id]
    if indicator_type is not None:
        indicators = [i for i in indicators if i.get("indicator_type") == indicator_type]

    total = len(indicators)
    indicators.sort(key=lambda x: x.get("record_date") or "", reverse=True)
    start = (page - 1) * page_size
    page_items = indicators[start : start + page_size]

    data = [
        {
            "id": i.get("_record_id"),
            "pilot_batch_id": i.get("pilot_batch_id"),
            "batch_id": i.get("batch_id"),
            "record_date": str(i.get("record_date")),
            "indicator_type": i.get("indicator_type"),
            "indicator_name": i.get("indicator_name"),
            "value": float(i.get("value", 0) or 0),
            "unit": i.get("unit"),
            "sample_size": i.get("sample_size"),
            "test_method": i.get("test_method"),
        }
        for i in page_items
    ]
    return paginated_response(data, page, page_size, total)
