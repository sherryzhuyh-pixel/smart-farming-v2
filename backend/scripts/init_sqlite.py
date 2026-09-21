#!/usr/bin/env python3
"""AI智慧养殖系统V2.0 - SQLite数据库初始化脚本

功能：
1. 创建SQLite数据库文件
2. 执行DDL创建所有表
3. 初始化基础数据（品种、鸡舍、批次、库存等）
4. 初始化管理员账号

用法：
    python scripts/init_sqlite.py [--drop]

环境变量（或.env文件）：
    DATABASE_URL=sqlite:///./smart_farming.db
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
from datetime import date, datetime

from app.config import get_settings
from app.database import Base, engine
from app.models import (
    Breed, House, Batch, AnimalIndividual, GrowthRecord, HealthRecord,
    Inventory, InventoryTransaction,
    BreedingOperation, EnvironmentParam,
    PilotProject, PilotBatch, PilotIndicator,
    SysConfig, FinancialTransaction, ProfitAnalysis, TraceabilityChain,
)
from sqlalchemy.orm import sessionmaker


def drop_all_tables():
    """删除所有表"""
    Base.metadata.drop_all(bind=engine)
    print("[OK] 所有表已删除")


def create_all_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("[OK] 所有表已创建")


def init_breed_data(session):
    """初始化品种数据"""
    breeds = [
        Breed(
            breed_code="AA+",
            breed_name="AA+白羽肉鸡父母代",
            breed_type=1,
            survival_rate_std=95.0,
            daily_gain_std=45.5,
            feed_meat_ratio=1.85,
            description="世界著名白羽肉鸡品种",
        ),
        Breed(
            breed_code="ROSS308",
            breed_name="ROSS308白羽肉鸡",
            breed_type=1,
            survival_rate_std=94.5,
            daily_gain_std=48.2,
            feed_meat_ratio=1.78,
            description="安伟捷公司优质肉鸡品种",
        ),
        Breed(
            breed_code="COBB",
            breed_name="科宝",
            breed_type=1,
            survival_rate_std=95.5,
            daily_gain_std=67.0,
            feed_meat_ratio=1.72,
            description="科宝公司经典肉鸡品种",
        ),
        Breed(
            breed_code="HY-LINE",
            breed_name="海兰褐",
            breed_type=2,
            survival_rate_std=92.0,
            daily_gain_std=15.0,
            feed_meat_ratio=2.10,
            description="著名褐壳蛋鸡品种",
        ),
    ]
    session.add_all(breeds)
    session.commit()
    print(f"[OK] 初始化 {len(breeds)} 条品种数据")
    return breeds


def init_house_data(session):
    """初始化鸡舍数据"""
    houses = [
        House(
            house_code="A-01",
            house_name="A区育雏舍1号",
            house_type=1,
            capacity=12000,
            area_sqm=1200.0,
            status=1,
        ),
        House(
            house_code="A-02",
            house_name="A区育雏舍2号",
            house_type=1,
            capacity=10000,
            area_sqm=1000.0,
            status=1,
        ),
        House(
            house_code="B-01",
            house_name="B区中试舍1号",
            house_type=2,
            capacity=6000,
            area_sqm=800.0,
            status=1,
        ),
        House(
            house_code="A-03",
            house_name="A区育成舍1号",
            house_type=2,
            capacity=15000,
            area_sqm=1500.0,
            status=1,
        ),
    ]
    session.add_all(houses)
    session.commit()
    print(f"[OK] 初始化 {len(houses)} 条鸡舍数据")
    return houses


def init_batch_data(session, breeds, houses):
    """初始化批次数据"""
    batches = [
        Batch(
            batch_no="BT-20260315-AA-001",
            batch_name="A区育雏批次-001",
            breed_id=breeds[0].id,
            house_id=houses[0].id,
            quantity_initial=10000,
            quantity_current=9850,
            date_in=date(2026, 3, 15),
            date_out=date(2026, 9, 15),
            age_day_in=1,
            source_type=1,
            status=1,
            responsible_person="张技术员",
            pilot_flag=0,
        ),
        Batch(
            batch_no="BT-20260320-AA-002",
            batch_name="A区育雏批次-002",
            breed_id=breeds[0].id,
            house_id=houses[1].id,
            quantity_initial=8000,
            quantity_current=7800,
            date_in=date(2026, 3, 20),
            date_out=date(2026, 9, 20),
            age_day_in=1,
            source_type=1,
            status=1,
            responsible_person="李技术员",
            pilot_flag=0,
        ),
        Batch(
            batch_no="BT-20260401-ROSS-001",
            batch_name="B区中试批次-001",
            breed_id=breeds[1].id,
            house_id=houses[2].id,
            quantity_initial=5000,
            quantity_current=4900,
            date_in=date(2026, 4, 1),
            date_out=date(2026, 10, 1),
            age_day_in=1,
            source_type=1,
            status=1,
            responsible_person="王技术员",
            pilot_flag=1,
        ),
        Batch(
            batch_no="BT-20260110-AA-003",
            batch_name="A区已出栏批次-001",
            breed_id=breeds[0].id,
            house_id=houses[0].id,
            quantity_initial=12000,
            quantity_current=0,
            date_in=date(2026, 1, 10),
            date_out=date(2026, 7, 10),
            age_day_in=1,
            source_type=1,
            status=2,
            responsible_person="张技术员",
            pilot_flag=0,
        ),
    ]
    session.add_all(batches)
    session.commit()
    print(f"[OK] 初始化 {len(batches)} 条批次数据")
    return batches


def init_inventory_data(session):
    """初始化库存数据"""
    items = [
        Inventory(
            item_code="FEED-001",
            item_name="玉米-东北二等",
            item_category=1,
            item_spec="水分<=14%，蛋白>=8%",
            unit="kg",
            quantity=50000,
            safety_stock=10000,
            storage_location="A仓库-3号货架-2层",
            expiry_date=date(2026, 9, 1),
            status=1,
        ),
        Inventory(
            item_code="FEED-002",
            item_name="豆粕-43%蛋白",
            item_category=1,
            item_spec="蛋白>=43%",
            unit="kg",
            quantity=8000,
            safety_stock=5000,
            storage_location="A仓库-2号货架-1层",
            expiry_date=date(2026, 8, 15),
            status=1,
        ),
        Inventory(
            item_code="VAC-001",
            item_name="新城疫活疫苗(IV系)",
            item_category=3,
            item_spec="1000羽份/瓶",
            unit="瓶",
            quantity=50,
            safety_stock=200,
            storage_location="B冷库-1号柜",
            expiry_date=date(2026, 12, 1),
            status=1,
        ),
        Inventory(
            item_code="DRUG-001",
            item_name="恩诺沙星可溶性粉",
            item_category=2,
            item_spec="10%",
            unit="袋",
            quantity=100,
            safety_stock=50,
            storage_location="C药库-2号柜",
            expiry_date=date(2026, 4, 15),
            status=2,
        ),
        Inventory(
            item_code="VAC-002",
            item_name="禽流感疫苗(H5+H7)",
            item_category=3,
            item_spec="500羽份/瓶",
            unit="瓶",
            quantity=20,
            safety_stock=30,
            storage_location="B冷库-2号柜",
            expiry_date=date(2026, 3, 1),
            status=3,
        ),
        Inventory(
            item_code="FEED-003",
            item_name="微藻功能饲料",
            item_category=1,
            item_spec="含硒0.5mg/kg",
            unit="kg",
            quantity=3000,
            safety_stock=1000,
            storage_location="A仓库-5号货架",
            expiry_date=date(2026, 10, 1),
            status=1,
        ),
    ]
    session.add_all(items)
    session.commit()
    print(f"[OK] 初始化 {len(items)} 条库存数据")


def init_health_records(session, batch_id):
    """初始化健康记录"""
    records = [
        HealthRecord(
            record_type=1,
            batch_id=batch_id,
            record_date=date(2026, 3, 22),
            event_name="新城疫疫苗首免",
            drug_name="新城疫活疫苗(IV系)",
            veterinarian="王兽医",
            cost=2000,
            mortality_flag=0,
        ),
        HealthRecord(
            record_type=1,
            batch_id=batch_id,
            record_date=date(2026, 4, 5),
            event_name="禽流感疫苗免疫",
            drug_name="禽流感H5+H7疫苗",
            veterinarian="王兽医",
            cost=3000,
            mortality_flag=0,
        ),
        HealthRecord(
            record_type=2,
            batch_id=batch_id,
            record_date=date(2026, 4, 12),
            event_name="呼吸道症状诊治",
            drug_name="泰乐菌素",
            drug_dosage="1g/L饮水",
            symptom="咳嗽、打喷嚏",
            diagnosis="慢性呼吸道病",
            treatment_result=2,
            veterinarian="王兽医",
            cost=500,
            mortality_flag=0,
        ),
    ]
    session.add_all(records)
    session.commit()
    print(f"[OK] 初始化 {len(records)} 条健康记录")


def init_pilot_project(session, breeds, houses, batches):
    """初始化中试项目"""
    pilot = PilotProject(
        project_code="PILOT-202604-001",
        project_name="微藻功能饲料中试",
        project_type=1,
        description="评估微藻功能饲料对肉鸡生长性能的影响",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 10, 1),
        status=1,
        principal="刘中试负责人",
        target_scale=5000,
        phase=1,
    )
    session.add(pilot)
    session.commit()
    session.refresh(pilot)

    # 关联中试批次
    pb = PilotBatch(
        pilot_project_id=pilot.id,
        batch_id=batches[2].id,
        group_type=1,
        compare_mode=1,
        start_date=date(2026, 4, 1),
    )
    session.add(pb)
    session.commit()

    # 中试指标
    indicators = [
        PilotIndicator(
            pilot_project_id=pilot.id,
            pilot_batch_id=pb.id,
            batch_id=batches[2].id,
            record_date=date(2026, 4, 1),
            indicator_type=1,
            indicator_name="成活率",
            value=98.0,
            unit="%",
        ),
        PilotIndicator(
            pilot_project_id=pilot.id,
            pilot_batch_id=pb.id,
            batch_id=batches[2].id,
            record_date=date(2026, 4, 1),
            indicator_type=1,
            indicator_name="日增重",
            value=52.3,
            unit="g",
        ),
        PilotIndicator(
            pilot_project_id=pilot.id,
            pilot_batch_id=pb.id,
            batch_id=batches[2].id,
            record_date=date(2026, 4, 1),
            indicator_type=1,
            indicator_name="料肉比",
            value=1.72,
            unit="",
        ),
    ]
    session.add_all(indicators)
    session.commit()
    print(f"[OK] 初始化中试项目: {pilot.project_name}")


def init_sys_config(session):
    """初始化系统配置"""
    configs = [
        SysConfig(
            config_key="trace_mode",
            config_value="ear_tag",
            value_type="string",
            scope_type=1,
            scope_id=0,
            description="个体追踪模式：ear_tag=耳标扫码, sampling=批次抽样",
        ),
        SysConfig(
            config_key="auto_finance_link",
            config_value="0",
            value_type="int",
            scope_type=1,
            scope_id=0,
            description="财务自动联动：0=手动, 1=自动",
        ),
        SysConfig(
            config_key="sampling_rate",
            config_value="10",
            value_type="int",
            scope_type=1,
            scope_id=0,
            description="批次抽样比例（%）",
        ),
        SysConfig(
            config_key="alert_low_stock",
            config_value="1",
            value_type="int",
            scope_type=1,
            scope_id=0,
            description="库存低量预警开关",
        ),
        SysConfig(
            config_key="expiry_warning_days",
            config_value="30",
            value_type="int",
            scope_type=1,
            scope_id=0,
            description="临期预警天数",
        ),
    ]
    session.add_all(configs)
    session.commit()
    print(f"[OK] 初始化 {len(configs)} 条系统配置")


def main():
    parser = argparse.ArgumentParser(description="AI智慧养殖系统V2.0 - SQLite数据库初始化")
    parser.add_argument("--drop", action="store_true", help="先删除所有表再重新创建")
    args = parser.parse_args()

    print("=" * 60)
    print("AI智慧养殖系统V2.0 - SQLite数据库初始化")
    print("=" * 60)

    settings = get_settings()
    print(f"数据库: {settings.DATABASE_URL_EFFECTIVE}")

    # 1. 删除表（如果指定了--drop）
    if args.drop:
        drop_all_tables()

    # 2. 创建表
    create_all_tables()

    # 3. 初始化种子数据
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        print("\n--- 初始化种子数据 ---")
        breeds = init_breed_data(session)
        houses = init_house_data(session)
        batches = init_batch_data(session, breeds, houses)
        init_inventory_data(session)
        init_health_records(session, batches[0].id)
        init_pilot_project(session, breeds, houses, batches)
        init_sys_config(session)
        print("\n[OK] 所有种子数据初始化完成")
    except Exception as e:
        session.rollback()
        print(f"[ERROR] 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("数据库初始化完成！")
    print("=" * 60)
    print("\n后续操作:")
    print("  1. 启动服务: uvicorn app.main:app --reload")
    print("  2. API文档: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
