#!/usr/bin/env python3
"""AI智慧养殖系统V2.0 - 数据库初始化脚本

功能：
1. 创建数据库（如果不存在）
2. 执行DDL创建30张表
3. 初始化基础配置数据（品种、鸡舍、标准参数等）
4. 初始化系统配置（sys_config三级作用域默认值）

用法：
    python scripts/init_db.py [--drop]

环境变量（或.env文件）：
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import date

from app.config import get_settings
from app.database import Base, engine as app_engine
from app.models import (
    Breed, House, Batch, AnimalIndividual, GrowthRecord, HealthRecord,
    PurchaseOrder, PurchaseItem, Inventory, InventoryTransaction,
    HatchingRecord, SalesOrder, SalesItem, CullingRecord,
    BreedingOperation, EnvironmentParam, Alert, FeedConsumption,
    BenchmarkStandard, PerformanceAnalysis, TraceabilityChain,
    PilotProject, PilotBatch, PilotIndicator, MarketPrice,
    SysConfig, SysConfigHistory, FinancialTransaction,
    CostAllocation, ProfitAnalysis,
)


def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    settings = get_settings()
    # Connect to mysql without database
    url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/?charset={settings.DB_CHARSET}"
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        print(f"[OK] 数据库 '{settings.DB_NAME}' 已就绪")


def drop_all_tables():
    """删除所有表"""
    Base.metadata.drop_all(bind=app_engine)
    print("[OK] 所有表已删除")


def create_all_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=app_engine)
    print("[OK] 所有表已创建")


def init_breed_data(session):
    """初始化品种数据"""
    breeds = [
        Breed(
            breed_code="AA",
            breed_name="爱拔益加",
            breed_type="肉鸡",
            survival_rate_std=95.0,
            daily_gain_std=65.0,
            feed_meat_ratio=1.75,
            description="世界著名白羽肉鸡品种",
        ),
        Breed(
            breed_code="ROSS",
            breed_name="罗斯308",
            breed_type="肉鸡",
            survival_rate_std=94.5,
            daily_gain_std=63.0,
            feed_meat_ratio=1.80,
            description="安伟捷公司优质肉鸡品种",
        ),
        Breed(
            breed_code="COBB",
            breed_name="科宝",
            breed_type="肉鸡",
            survival_rate_std=95.5,
            daily_gain_std=67.0,
            feed_meat_ratio=1.72,
            description="科宝公司经典肉鸡品种",
        ),
        Breed(
            breed_code="HY-LINE",
            breed_name="海兰褐",
            breed_type="蛋鸡",
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
            house_code="H001",
            house_name="1号鸡舍",
            house_type="封闭式",
            capacity=20000,
            area_sqm=1200.0,
            status=1,
        ),
        House(
            house_code="H002",
            house_name="2号鸡舍",
            house_type="封闭式",
            capacity=20000,
            area_sqm=1200.0,
            status=1,
        ),
        House(
            house_code="H003",
            house_name="3号鸡舍",
            house_type="半开放式",
            capacity=15000,
            area_sqm=1000.0,
            status=1,
        ),
        House(
            house_code="H004",
            house_name="4号鸡舍",
            house_type="封闭式",
            capacity=20000,
            area_sqm=1200.0,
            status=0,
        ),
    ]
    session.add_all(houses)
    session.commit()
    print(f"[OK] 初始化 {len(houses)} 条鸡舍数据")
    return houses


def init_inventory_data(session):
    """初始化库存数据"""
    items = [
        Inventory(
            item_code="F001",
            item_name="雏鸡前期料",
            item_type="饲料",
            spec="20kg/袋",
            quantity=500.0,
            unit="袋",
            unit_price=120.0,
            warehouse="主仓库",
            safety_stock=50.0,
            expiry_date=date(2025, 6, 1),
            status=1,
        ),
        Inventory(
            item_code="F002",
            item_name="雏鸡中期料",
            item_type="饲料",
            spec="20kg/袋",
            quantity=300.0,
            unit="袋",
            unit_price=115.0,
            warehouse="主仓库",
            safety_stock=40.0,
            expiry_date=date(2025, 6, 1),
            status=1,
        ),
        Inventory(
            item_code="M001",
            item_name="新城疫疫苗",
            item_type="药品",
            spec="1000羽份/瓶",
            quantity=50.0,
            unit="瓶",
            unit_price=80.0,
            warehouse="药品库",
            safety_stock=10.0,
            expiry_date=date(2025, 3, 15),
            status=1,
        ),
        Inventory(
            item_code="M002",
            item_name="禽流感疫苗",
            item_type="药品",
            spec="1000羽份/瓶",
            quantity=30.0,
            unit="瓶",
            unit_price=120.0,
            warehouse="药品库",
            safety_stock=8.0,
            expiry_date=date(2025, 2, 28),
            status=1,
        ),
        Inventory(
            item_code="E001",
            item_name="饮水器",
            item_type="设备",
            spec="标准型",
            quantity=200.0,
            unit="个",
            unit_price=35.0,
            warehouse="工具库",
            safety_stock=20.0,
            status=1,
        ),
    ]
    session.add_all(items)
    session.commit()
    print(f"[OK] 初始化 {len(items)} 条库存数据")


def init_benchmark_data(session, breeds):
    """初始化标准数据"""
    benchmarks = []
    for breed in breeds:
        if breed.breed_type == "肉鸡":
            for week in range(1, 7):
                benchmarks.append(BenchmarkStandard(
                    breed_id=breed.id,
                    week_no=week,
                    target_weight=week * 500 + 200,
                    target_survival_rate=99.0 - week * 0.8,
                    target_daily_gain=breed.daily_gain_std,
                    target_feed_meat_ratio=breed.feed_meat_ratio,
                ))
    session.add_all(benchmarks)
    session.commit()
    print(f"[OK] 初始化 {len(benchmarks)} 条标准数据")


def init_sys_config(session):
    """初始化系统配置（三级作用域）"""
    configs = [
        # 全局配置 (scope_type=1)
        SysConfig(
            config_key="trace_mode",
            config_value="ear_tag",
            config_desc="个体追踪模式：ear_tag=耳标扫码, sampling=批次抽样",
            scope_type=1,
            scope_id=0,
        ),
        SysConfig(
            config_key="auto_finance_link",
            config_value="0",
            config_desc="财务自动联动：0=手动, 1=自动",
            scope_type=1,
            scope_id=0,
        ),
        SysConfig(
            config_key="traceability_print",
            config_value="0",
            config_desc="溯源码打印：0=仅系统内, 1=支持物理打印",
            scope_type=1,
            scope_id=0,
        ),
        SysConfig(
            config_key="pilot_stat_method",
            config_value="mean_compare",
            config_desc="中试统计方法：mean_compare=均值对比, t_test=t检验",
            scope_type=1,
            scope_id=0,
        ),
        SysConfig(
            config_key="sampling_rate",
            config_value="10",
            config_desc="批次抽样比例（%）",
            scope_type=1,
            scope_id=0,
        ),
        SysConfig(
            config_key="alert_low_stock",
            config_value="1",
            config_desc="库存低量预警开关",
            scope_type=1,
            scope_id=0,
        ),
        SysConfig(
            config_key="alert_expiry",
            config_value="1",
            config_desc="临期预警开关",
            scope_type=1,
            scope_id=0,
        ),
        SysConfig(
            config_key="expiry_warning_days",
            config_value="30",
            config_desc="临期预警天数",
            scope_type=1,
            scope_id=0,
        ),
    ]
    session.add_all(configs)
    session.commit()
    print(f"[OK] 初始化 {len(configs)} 条系统配置")


def init_demo_batch(session, breeds, houses):
    """初始化演示批次数据"""
    breed = breeds[0]  # AA
    house = houses[0]  # H001

    batch = Batch(
        batch_no="B20240921001",
        batch_name="20240921-AA-001",
        breed_id=breed.id,
        house_id=house.id,
        quantity_initial=10000,
        quantity_current=9500,
        date_in=date(2024, 9, 1),
        age_day_in=1,
        source_type=1,
        status=1,
        responsible_person="张三",
        pilot_flag=0,
    )
    session.add(batch)
    session.commit()
    session.refresh(batch)
    print(f"[OK] 初始化演示批次: {batch.batch_no}")

    # 初始化一些个体
    individuals = []
    for i in range(1, 51):
        individuals.append(AnimalIndividual(
            batch_id=batch.id,
            ear_tag_no=f"ET{batch.id:04d}{i:04d}",
            status=1,
            current_house_id=house.id,
        ))
    session.add_all(individuals)
    session.commit()
    print(f"[OK] 初始化 {len(individuals)} 条个体数据")

    # 初始化生长记录（模拟批次抽样模式 - 10%）
    import random
    random.seed(42)
    growth_records = []
    for day in range(1, 22, 7):  # 每周称重
        record_date = date(2024, 9, 1 + day)
        base_weight = 40 + day * 55  # 近似生长曲线
        for ind in individuals[:10]:  # 抽样10%
            weight = base_weight + random.uniform(-20, 20)
            growth_records.append(GrowthRecord(
                batch_id=batch.id,
                animal_id=ind.id,
                record_date=record_date,
                weight=round(weight, 2),
                age_days=day,
                recorder="李四",
            ))
    session.add_all(growth_records)
    session.commit()
    print(f"[OK] 初始化 {len(growth_records)} 条生长记录")

    # 初始化饲料消耗
    feed_records = []
    for day in range(1, 22):
        feed_records.append(FeedConsumption(
            batch_id=batch.id,
            feed_date=date(2024, 9, day),
            feed_quantity=round(1200 + day * 50 + random.uniform(-50, 50), 2),
            feed_type="雏鸡前期料",
            recorder="王五",
        ))
    session.add_all(feed_records)
    session.commit()
    print(f"[OK] 初始化 {len(feed_records)} 条饲料消耗记录")

    # 初始化财务记录
    financials = [
        FinancialTransaction(
            transaction_type=2,
            category="雏鸡苗",
            amount=80000.0,
            batch_id=batch.id,
            transaction_date=date(2024, 9, 1),
            payee_payer="种鸡场A",
            remark="进苗费用",
        ),
        FinancialTransaction(
            transaction_type=2,
            category="饲料费",
            amount=60000.0,
            batch_id=batch.id,
            transaction_date=date(2024, 9, 10),
            payee_payer="饲料供应商B",
            remark="饲料采购",
        ),
        FinancialTransaction(
            transaction_type=2,
            category="药品费",
            amount=8000.0,
            batch_id=batch.id,
            transaction_date=date(2024, 9, 5),
            payee_payer="兽药公司C",
            remark="疫苗采购",
        ),
        FinancialTransaction(
            transaction_type=2,
            category="人工费",
            amount=15000.0,
            batch_id=batch.id,
            transaction_date=date(2024, 9, 15),
            payee_payer="劳务公司D",
            remark="养殖人工",
        ),
    ]
    session.add_all(financials)
    session.commit()
    print(f"[OK] 初始化 {len(financials)} 条财务记录")

    # 初始化利润分析
    total_cost = sum(f.amount for f in financials)
    profit = ProfitAnalysis(
        batch_id=batch.id,
        total_revenue=0.0,
        total_cost=total_cost,
        gross_profit=-total_cost,
        profit_margin=0.0,
        cost_per_bird=round(total_cost / batch.quantity_initial, 2),
        revenue_per_bird=0.0,
        analysis_date=date(2024, 9, 21),
    )
    session.add(profit)
    session.commit()
    print(f"[OK] 初始化利润分析数据")

    # 初始化溯源链
    trace = TraceabilityChain(
        trace_code=f"TC{batch.id:08d}",
        batch_id=batch.id,
        animal_id=None,
        stage="养殖中",
        event_date=date(2024, 9, 21),
        event_type="current",
        description="批次正在养殖中",
        operator="系统",
    )
    session.add(trace)
    session.commit()
    print(f"[OK] 初始化溯源数据: {trace.trace_code}")

    return batch


def init_pilot_project(session, breeds, houses):
    """初始化中试项目"""
    breed = breeds[0]
    house_exp = houses[1]  # H002
    house_ctrl = houses[2]  # H003

    pilot = PilotProject(
        project_name="新型饲料配方中试",
        project_code="PILOT-202409-001",
        description="测试新型低蛋白饲料配方对肉鸡生长性能的影响",
        start_date=date(2024, 9, 1),
        status=1,
        responsible_person="赵六",
    )
    session.add(pilot)
    session.commit()
    session.refresh(pilot)

    # 实验组批次
    batch_exp = Batch(
        batch_no="B20240921002",
        batch_name="20240921-AA-EXP",
        breed_id=breed.id,
        house_id=house_exp.id,
        quantity_initial=5000,
        quantity_current=4800,
        date_in=date(2024, 9, 1),
        age_day_in=1,
        source_type=1,
        status=1,
        responsible_person="赵六",
        pilot_flag=1,
    )
    # 对照组批次
    batch_ctrl = Batch(
        batch_no="B20240921003",
        batch_name="20240921-AA-CTRL",
        breed_id=breed.id,
        house_id=house_ctrl.id,
        quantity_initial=5000,
        quantity_current=4750,
        date_in=date(2024, 9, 1),
        age_day_in=1,
        source_type=1,
        status=1,
        responsible_person="赵六",
        pilot_flag=1,
    )
    session.add_all([batch_exp, batch_ctrl])
    session.commit()
    session.refresh(batch_exp)
    session.refresh(batch_ctrl)

    # 中试批次关联
    pb_exp = PilotBatch(
        pilot_id=pilot.id,
        batch_id=batch_exp.id,
        group_type="experiment",
        description="实验组 - 新饲料配方",
    )
    pb_ctrl = PilotBatch(
        pilot_id=pilot.id,
        batch_id=batch_ctrl.id,
        group_type="control",
        description="对照组 - 常规饲料",
    )
    session.add_all([pb_exp, pb_ctrl])
    session.commit()

    # 中试指标
    indicators = [
        PilotIndicator(pilot_id=pilot.id, indicator_name="成活率", unit="%", target_value=95.0),
        PilotIndicator(pilot_id=pilot.id, indicator_name="日增重", unit="g", target_value=65.0),
        PilotIndicator(pilot_id=pilot.id, indicator_name="料肉比", unit="", target_value=1.75),
        PilotIndicator(pilot_id=pilot.id, indicator_name="出栏体重", unit="g", target_value=2500.0),
    ]
    session.add_all(indicators)
    session.commit()
    print(f"[OK] 初始化中试项目: {pilot.project_name}")


def main():
    parser = argparse.ArgumentParser(description="AI智慧养殖系统V2.0 数据库初始化")
    parser.add_argument("--drop", action="store_true", help="先删除所有表再重新创建")
    parser.add_argument("--skip-seed", action="store_true", help="跳过种子数据初始化")
    args = parser.parse_args()

    print("=" * 60)
    print("AI智慧养殖系统V2.0 - 数据库初始化")
    print("=" * 60)

    # 1. 创建数据库
    create_database_if_not_exists()

    # 2. 删除表（如果指定了--drop）
    if args.drop:
        drop_all_tables()

    # 3. 创建表
    create_all_tables()

    # 4. 初始化种子数据
    if not args.skip_seed:
        SessionLocal = sessionmaker(bind=app_engine)
        session = SessionLocal()
        try:
            print("\n--- 初始化种子数据 ---")
            breeds = init_breed_data(session)
            houses = init_house_data(session)
            init_inventory_data(session)
            init_benchmark_data(session, breeds)
            init_sys_config(session)
            init_demo_batch(session, breeds, houses)
            init_pilot_project(session, breeds, houses)
            print("\n[OK] 所有种子数据初始化完成")
        except Exception as e:
            session.rollback()
            print(f"[ERROR] 初始化失败: {e}")
            raise
        finally:
            session.close()
    else:
        print("[INFO] 跳过种子数据初始化")

    print("\n" + "=" * 60)
    print("数据库初始化完成！")
    print("=" * 60)
    print("\n后续操作:")
    print("  1. 启动服务: uvicorn app.main:app --reload")
    print("  2. API文档: http://localhost:8000/docs")
    print("  3. 运行测试: pytest tests/ -v")


if __name__ == "__main__":
    main()
