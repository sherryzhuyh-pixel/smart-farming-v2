"""中试效果对比 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import PilotProject, PilotBatch, PilotIndicator, Batch, Breed, GrowthRecord
from app.utils.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/pilots", tags=["中试效果对比"])


@router.get("")
def list_pilot_projects(
    status: Optional[int] = Query(None),
    project_type: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询中试项目列表"""
    query = db.query(PilotProject)
    if status is not None:
        query = query.filter(PilotProject.status == status)
    if project_type is not None:
        query = query.filter(PilotProject.project_type == project_type)
    total = query.count()
    items = query.order_by(desc(PilotProject.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    data = [
        {
            "id": p.id,
            "project_code": p.project_code,
            "project_name": p.project_name,
            "project_type": p.project_type,
            "tech_partner": p.tech_partner,
            "channel_partner": p.channel_partner,
            "target_scale": p.target_scale,
            "phase": p.phase,
            "status": p.status,
            "start_date": str(p.start_date) if p.start_date else None,
            "end_date": str(p.end_date) if p.end_date else None,
            "principal": p.principal,
        }
        for p in items
    ]
    return paginated_response(data, page, page_size, total)


@router.get("/{project_id}")
def get_pilot_project(project_id: int, db: Session = Depends(get_db)):
    """获取中试项目详情"""
    project = db.query(PilotProject).filter(PilotProject.id == project_id).first()
    if not project:
        return error_response(404, "中试项目不存在")

    # 实验组/对照组批次
    pilot_batches = db.query(PilotBatch, Batch.batch_no, Breed.breed_name).join(Batch, PilotBatch.batch_id == Batch.id).join(Breed, Batch.breed_id == Breed.id).filter(PilotBatch.pilot_project_id == project_id).all()

    experiment_batches = []
    control_batches = []
    for pb, batch_no, breed_name in pilot_batches:
        info = {
            "id": pb.id,
            "batch_id": pb.batch_id,
            "batch_no": batch_no,
            "breed_name": breed_name,
            "group_type": pb.group_type,
            "treatment_desc": pb.treatment_desc,
            "dosage": pb.dosage,
            "frequency": pb.frequency,
            "start_date": str(pb.start_date) if pb.start_date else None,
            "end_date": str(pb.end_date) if pb.end_date else None,
        }
        if pb.group_type == 1:
            experiment_batches.append(info)
        elif pb.group_type == 2:
            control_batches.append(info)

    return success_response({
        "id": project.id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "project_type": project.project_type,
        "description": project.description,
        "tech_partner": project.tech_partner,
        "channel_partner": project.channel_partner,
        "target_scale": project.target_scale,
        "phase": project.phase,
        "status": project.status,
        "start_date": str(project.start_date) if project.start_date else None,
        "end_date": str(project.end_date) if project.end_date else None,
        "principal": project.principal,
        "experiment_batches": experiment_batches,
        "control_batches": control_batches,
    })


@router.get("/{project_id}/comparison")
def get_pilot_comparison(project_id: int, db: Session = Depends(get_db)):
    """中试效果对比"""
    project = db.query(PilotProject).filter(PilotProject.id == project_id).first()
    if not project:
        return error_response(404, "中试项目不存在")

    # 获取实验组和对照组的指标
    indicators = db.query(PilotIndicator, Batch.batch_no).join(Batch, PilotIndicator.batch_id == Batch.id).filter(PilotIndicator.pilot_project_id == project_id).order_by(PilotIndicator.record_date).all()

    # 按组别和指标类型分组
    from collections import defaultdict
    exp_data = defaultdict(list)
    ctrl_data = defaultdict(list)

    # 获取pilot_batch的group_type映射
    pb_map = {pb.batch_id: pb.group_type for pb in db.query(PilotBatch).filter(PilotBatch.pilot_project_id == project_id).all()}

    for ind, batch_no in indicators:
        group = pb_map.get(ind.batch_id)
        item = {
            "record_date": str(ind.record_date),
            "indicator_type": ind.indicator_type,
            "indicator_name": ind.indicator_name,
            "value": float(ind.value),
            "unit": ind.unit,
            "batch_no": batch_no,
        }
        key = ind.indicator_type
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
    exp_batch_ids = [pb.batch_id for pb in db.query(PilotBatch).filter(PilotBatch.pilot_project_id == project_id, PilotBatch.group_type == 1).all()]
    ctrl_batch_ids = [pb.batch_id for pb in db.query(PilotBatch).filter(PilotBatch.pilot_project_id == project_id, PilotBatch.group_type == 2).all()]

    exp_growth = []
    ctrl_growth = []
    if exp_batch_ids:
        exp_gr = db.query(GrowthRecord).filter(GrowthRecord.batch_id.in_(exp_batch_ids)).order_by(GrowthRecord.record_date).all()
        for gr in exp_gr:
            exp_growth.append({"record_date": str(gr.record_date), "age_days": gr.age_days, "weight": float(gr.weight)})
    if ctrl_batch_ids:
        ctrl_gr = db.query(GrowthRecord).filter(GrowthRecord.batch_id.in_(ctrl_batch_ids)).order_by(GrowthRecord.record_date).all()
        for gr in ctrl_gr:
            ctrl_growth.append({"record_date": str(gr.record_date), "age_days": gr.age_days, "weight": float(gr.weight)})

    return success_response({
        "project_id": project_id,
        "project_name": project.project_name,
        "comparison": comparison,
        "growth_curve": {
            "experiment": exp_growth[:100],
            "control": ctrl_growth[:100],
        },
    })


@router.get("/{project_id}/indicators")
def list_pilot_indicators(
    project_id: int,
    indicator_type: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询中试指标列表"""
    query = db.query(PilotIndicator).filter(PilotIndicator.pilot_project_id == project_id)
    if indicator_type is not None:
        query = query.filter(PilotIndicator.indicator_type == indicator_type)
    total = query.count()
    items = query.order_by(desc(PilotIndicator.record_date)).offset((page - 1) * page_size).limit(page_size).all()
    data = [
        {
            "id": i.id,
            "pilot_batch_id": i.pilot_batch_id,
            "batch_id": i.batch_id,
            "record_date": str(i.record_date),
            "indicator_type": i.indicator_type,
            "indicator_name": i.indicator_name,
            "value": float(i.value),
            "unit": i.unit,
            "sample_size": i.sample_size,
            "test_method": i.test_method,
        }
        for i in items
    ]
    return paginated_response(data, page, page_size, total)
