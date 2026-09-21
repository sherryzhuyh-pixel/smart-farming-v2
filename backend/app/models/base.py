from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, Date, DateTime,
    Numeric, ForeignKey, JSON, UniqueConstraint, Index
)
from sqlalchemy.sql import func
from app.database import Base


class Breed(Base):
    __tablename__ = "breed"
    id = Column(Integer, primary_key=True, autoincrement=True)
    breed_code = Column(String(32), nullable=False, unique=True)
    breed_name = Column(String(64), nullable=False)
    breed_type = Column(Integer, nullable=False, default=1)
    origin = Column(String(128))
    description = Column(Text)
    avg_weight_male = Column(Numeric(8, 3))
    avg_weight_female = Column(Numeric(8, 3))
    avg_egg_rate = Column(Numeric(5, 2))
    feed_meat_ratio = Column(Numeric(5, 3))
    survival_rate_std = Column(Numeric(5, 2))
    daily_gain_std = Column(Numeric(6, 3))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class House(Base):
    __tablename__ = "house"
    id = Column(Integer, primary_key=True, autoincrement=True)
    house_code = Column(String(32), nullable=False, unique=True)
    house_name = Column(String(64), nullable=False)
    house_type = Column(Integer, nullable=False, default=1)
    area_sqm = Column(Numeric(8, 2))
    capacity = Column(Integer)
    location = Column(String(256))
    env_device_id = Column(String(64))
    camera_ids = Column(JSON)
    status = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Batch(Base):
    __tablename__ = "batch"
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_no = Column(String(32), nullable=False, unique=True)
    batch_name = Column(String(64))
    breed_id = Column(BigInteger, ForeignKey("breed.id"), nullable=False)
    house_id = Column(BigInteger, ForeignKey("house.id"), nullable=False)
    batch_type = Column(Integer, nullable=False, default=1)
    quantity_initial = Column(Integer, nullable=False)
    quantity_current = Column(Integer, nullable=False)
    date_in = Column(Date, nullable=False)
    date_out = Column(Date)
    age_day_in = Column(Integer, nullable=False, default=1)
    source_type = Column(Integer, nullable=False)
    source_batch_id = Column(BigInteger, ForeignKey("batch.id"))
    purchase_order_id = Column(BigInteger, ForeignKey("purchase_order.id"))
    status = Column(Integer, nullable=False, default=1)
    responsible_person = Column(String(32))
    pilot_flag = Column(Integer, nullable=False, default=0)
    pilot_project_id = Column(BigInteger, ForeignKey("pilot_project.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AnimalIndividual(Base):
    __tablename__ = "animal_individual"
    id = Column(Integer, primary_key=True, autoincrement=True)
    animal_no = Column(String(32), nullable=False, unique=True)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    house_id = Column(BigInteger, ForeignKey("house.id"), nullable=False)
    breed_id = Column(BigInteger, ForeignKey("breed.id"), nullable=False)
    gender = Column(Integer, nullable=False)
    date_birth = Column(Date)
    date_in = Column(Date, nullable=False)
    age_day_in = Column(Integer, nullable=False)
    weight_in = Column(Numeric(7, 3))
    weight_out = Column(Numeric(7, 3))
    date_out = Column(Date)
    out_type = Column(Integer)
    status = Column(Integer, nullable=False, default=1)
    dam_id = Column(BigInteger, ForeignKey("animal_individual.id"))
    sire_id = Column(BigInteger, ForeignKey("animal_individual.id"))
    traceability_code = Column(String(64), unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class GrowthRecord(Base):
    __tablename__ = "growth_record"
    id = Column(Integer, primary_key=True, autoincrement=True)
    animal_id = Column(BigInteger, ForeignKey("animal_individual.id"), nullable=False)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    record_date = Column(Date, nullable=False)
    age_days = Column(Integer, nullable=False)
    weight = Column(Numeric(7, 3), nullable=False)
    body_length = Column(Numeric(6, 2))
    chest_girth = Column(Numeric(6, 2))
    shank_length = Column(Numeric(5, 2))
    recorder = Column(String(32))
    remark = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())


class HealthRecord(Base):
    __tablename__ = "health_record"
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_type = Column(Integer, nullable=False)
    animal_id = Column(BigInteger, ForeignKey("animal_individual.id"))
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    record_date = Column(Date, nullable=False)
    event_name = Column(String(128), nullable=False)
    drug_name = Column(String(128))
    drug_dosage = Column(String(64))
    route = Column(String(32))
    symptom = Column(Text)
    diagnosis = Column(String(256))
    treatment_result = Column(Integer)
    veterinarian = Column(String(32))
    cost = Column(Numeric(10, 2))
    mortality_flag = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now())


class PurchaseOrder(Base):
    __tablename__ = "purchase_order"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(32), nullable=False, unique=True)
    order_type = Column(Integer, nullable=False)
    supplier_name = Column(String(128), nullable=False)
    supplier_contact = Column(String(32))
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date)
    total_amount = Column(Numeric(12, 2), nullable=False)
    total_quantity = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False, default=1)
    remark = Column(String(512))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PurchaseItem(Base):
    __tablename__ = "purchase_item"
    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_order_id = Column(BigInteger, ForeignKey("purchase_order.id"), nullable=False)
    item_name = Column(String(128), nullable=False)
    item_spec = Column(String(64))
    unit = Column(String(16), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    batch_no = Column(String(32))
    expiry_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_code = Column(String(32), nullable=False, unique=True)
    item_name = Column(String(128), nullable=False)
    item_category = Column(Integer, nullable=False)
    item_spec = Column(String(64))
    unit = Column(String(16), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False, default=0)
    safety_stock = Column(Numeric(12, 3))
    storage_location = Column(String(64))
    batch_no = Column(String(32))
    expiry_date = Column(Date)
    status = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class InventoryTransaction(Base):
    __tablename__ = "inventory_transaction"
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(BigInteger, ForeignKey("inventory.id"), nullable=False)
    trans_type = Column(Integer, nullable=False)
    trans_date = Column(Date, nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    balance = Column(Numeric(12, 3), nullable=False)
    ref_type = Column(Integer)
    ref_id = Column(BigInteger)
    operator = Column(String(32))
    remark = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())


class HatchingRecord(Base):
    __tablename__ = "hatching_record"
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    hatch_batch_no = Column(String(32), nullable=False, unique=True)
    eggs_total = Column(Integer, nullable=False)
    eggs_fertile = Column(Integer)
    chicks_hatched = Column(Integer)
    chicks_grade_a = Column(Integer)
    chicks_grade_b = Column(Integer)
    chicks_grade_c = Column(Integer)
    hatch_rate = Column(Numeric(5, 2))
    hatch_date_start = Column(Date, nullable=False)
    hatch_date_end = Column(Date)
    incubator_no = Column(String(32))
    operator = Column(String(32))
    remark = Column(String(512))
    created_at = Column(DateTime, server_default=func.now())


class SalesOrder(Base):
    __tablename__ = "sales_order"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(32), nullable=False, unique=True)
    order_type = Column(Integer, nullable=False)
    customer_name = Column(String(128), nullable=False)
    customer_contact = Column(String(32))
    customer_phone = Column(String(16))
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date)
    total_amount = Column(Numeric(12, 2), nullable=False)
    total_quantity = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False, default=1)
    remark = Column(String(512))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SalesItem(Base):
    __tablename__ = "sales_item"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sales_order_id = Column(BigInteger, ForeignKey("sales_order.id"), nullable=False)
    batch_id = Column(BigInteger, ForeignKey("batch.id"))
    item_name = Column(String(128), nullable=False)
    item_spec = Column(String(64))
    unit = Column(String(16), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    traceability_code = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())


class CullingRecord(Base):
    __tablename__ = "culling_record"
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    animal_id = Column(BigInteger, ForeignKey("animal_individual.id"))
    cull_date = Column(Date, nullable=False)
    cull_reason = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    weight_total = Column(Numeric(8, 2))
    disposal_method = Column(Integer)
    revenue = Column(Numeric(10, 2))
    operator = Column(String(32))
    remark = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())


class BreedingOperation(Base):
    __tablename__ = "breeding_operation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    op_type = Column(Integer, nullable=False)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    animal_id = Column(BigInteger, ForeignKey("animal_individual.id"))
    house_id = Column(BigInteger, ForeignKey("house.id"), nullable=False)
    op_date = Column(DateTime, nullable=False)
    feed_type = Column(String(64))
    feed_quantity = Column(Numeric(8, 3))
    drug_name = Column(String(128))
    drug_dosage = Column(String(64))
    from_house_id = Column(BigInteger, ForeignKey("house.id"))
    to_house_id = Column(BigInteger, ForeignKey("house.id"))
    weight = Column(Numeric(7, 3))
    operator = Column(String(32), nullable=False)
    recorder = Column(String(32))
    env_temp = Column(Numeric(4, 1))
    env_humidity = Column(Numeric(4, 1))
    remark = Column(String(512))
    created_at = Column(DateTime, server_default=func.now())


class EnvironmentParam(Base):
    __tablename__ = "environment_param"
    id = Column(Integer, primary_key=True, autoincrement=True)
    house_id = Column(BigInteger, ForeignKey("house.id"), nullable=False)
    batch_id = Column(BigInteger, ForeignKey("batch.id"))
    record_time = Column(DateTime, nullable=False)
    temperature = Column(Numeric(4, 1))
    humidity = Column(Numeric(4, 1))
    ammonia = Column(Numeric(6, 2))
    co2 = Column(Numeric(6, 2))
    light_intensity = Column(Numeric(6, 1))
    ventilation_rate = Column(Numeric(6, 2))
    device_id = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())


class Alert(Base):
    __tablename__ = "alert"
    id = Column(Integer, primary_key=True, autoincrement=True)
    house_id = Column(BigInteger, ForeignKey("house.id"), nullable=False)
    batch_id = Column(BigInteger, ForeignKey("batch.id"))
    alert_type = Column(Integer, nullable=False)
    alert_level = Column(Integer, nullable=False)
    alert_content = Column(String(512), nullable=False)
    threshold_value = Column(String(32))
    actual_value = Column(String(32))
    status = Column(Integer, nullable=False, default=1)
    handler = Column(String(32))
    handle_time = Column(DateTime)
    handle_result = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())


class FeedConsumption(Base):
    __tablename__ = "feed_consumption"
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    house_id = Column(BigInteger, ForeignKey("house.id"), nullable=False)
    record_date = Column(Date, nullable=False)
    feed_type = Column(String(64), nullable=False)
    feed_quantity = Column(Numeric(8, 3), nullable=False)
    actual_consumption = Column(Numeric(8, 3))
    waste_amount = Column(Numeric(6, 3))
    avg_consumption_per_bird = Column(Numeric(6, 3))
    feed_meat_ratio_day = Column(Numeric(5, 3))
    cost = Column(Numeric(10, 2))
    recorder = Column(String(32))
    created_at = Column(DateTime, server_default=func.now())


class BenchmarkStandard(Base):
    __tablename__ = "benchmark_standard"
    id = Column(Integer, primary_key=True, autoincrement=True)
    breed_id = Column(BigInteger, ForeignKey("breed.id"), nullable=False)
    standard_name = Column(String(64), nullable=False)
    age_from = Column(Integer, nullable=False)
    age_to = Column(Integer, nullable=False)
    target_weight = Column(Numeric(7, 3))
    target_daily_gain = Column(Numeric(6, 3))
    target_feed_meat_ratio = Column(Numeric(5, 3))
    target_survival_rate = Column(Numeric(5, 2))
    target_egg_rate = Column(Numeric(5, 2))
    target_feed_consumption = Column(Numeric(6, 3))
    target_temp_low = Column(Numeric(4, 1))
    target_temp_high = Column(Numeric(4, 1))
    target_humidity_low = Column(Numeric(4, 1))
    target_humidity_high = Column(Numeric(4, 1))
    source = Column(String(128))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PerformanceAnalysis(Base):
    __tablename__ = "performance_analysis"
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_type = Column(Integer, nullable=False)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    analysis_date = Column(Date, nullable=False)
    age_days = Column(Integer, nullable=False)
    benchmark_id = Column(BigInteger, ForeignKey("benchmark_standard.id"), nullable=False)
    actual_weight = Column(Numeric(7, 3))
    target_weight = Column(Numeric(7, 3))
    weight_deviation = Column(Numeric(6, 3))
    weight_deviation_pct = Column(Numeric(5, 2))
    actual_daily_gain = Column(Numeric(6, 3))
    target_daily_gain = Column(Numeric(6, 3))
    daily_gain_deviation_pct = Column(Numeric(5, 2))
    actual_feed_meat_ratio = Column(Numeric(5, 3))
    target_feed_meat_ratio = Column(Numeric(5, 3))
    fmr_deviation_pct = Column(Numeric(5, 2))
    actual_survival_rate = Column(Numeric(5, 2))
    target_survival_rate = Column(Numeric(5, 2))
    survival_deviation_pct = Column(Numeric(5, 2))
    actual_egg_rate = Column(Numeric(5, 2))
    target_egg_rate = Column(Numeric(5, 2))
    egg_rate_deviation_pct = Column(Numeric(5, 2))
    created_at = Column(DateTime, server_default=func.now())


class TraceabilityChain(Base):
    __tablename__ = "traceability_chain"
    id = Column(Integer, primary_key=True, autoincrement=True)
    traceability_code = Column(String(64), nullable=False, unique=True)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    animal_id = Column(BigInteger, ForeignKey("animal_individual.id"))
    stage = Column(Integer, nullable=False)
    stage_ref_id = Column(BigInteger)
    parent_trace_id = Column(BigInteger, ForeignKey("traceability_chain.id"))
    event_date = Column(Date, nullable=False)
    event_desc = Column(String(256), nullable=False)
    location = Column(String(128))
    operator = Column(String(32))
    data_hash = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())


class PilotProject(Base):
    __tablename__ = "pilot_project"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_code = Column(String(32), nullable=False, unique=True)
    project_name = Column(String(128), nullable=False)
    project_type = Column(Integer, nullable=False)
    tech_partner = Column(String(128))
    channel_partner = Column(String(128))
    description = Column(Text)
    target_scale = Column(Integer, nullable=False)
    phase = Column(Integer, nullable=False, default=1)
    status = Column(Integer, nullable=False, default=1)
    start_date = Column(Date)
    end_date = Column(Date)
    principal = Column(String(32))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PilotBatch(Base):
    __tablename__ = "pilot_batch"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pilot_project_id = Column(BigInteger, ForeignKey("pilot_project.id"), nullable=False)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    group_type = Column(Integer, nullable=False)
    compare_mode = Column(Integer, nullable=False)
    treatment_desc = Column(String(256))
    dosage = Column(String(64))
    frequency = Column(String(32))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())


class PilotIndicator(Base):
    __tablename__ = "pilot_indicator"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pilot_project_id = Column(BigInteger, ForeignKey("pilot_project.id"), nullable=False)
    pilot_batch_id = Column(BigInteger, ForeignKey("pilot_batch.id"), nullable=False)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    record_date = Column(Date, nullable=False)
    indicator_type = Column(Integer, nullable=False)
    indicator_name = Column(String(64), nullable=False)
    value = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(16))
    sample_size = Column(Integer)
    test_method = Column(String(128))
    lab_report_no = Column(String(32))
    remark = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())


class MarketPrice(Base):
    __tablename__ = "market_price"
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_date = Column(Date, nullable=False)
    region = Column(String(32))
    product_type = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(16), nullable=False)
    price_change = Column(Numeric(6, 2))
    price_change_pct = Column(Numeric(5, 2))
    source = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())


class SysConfig(Base):
    __tablename__ = "sys_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(128), nullable=False)
    config_value = Column(String(512), nullable=False)
    value_type = Column(String(32), nullable=False)
    scope_type = Column(Integer, nullable=False)
    scope_id = Column(BigInteger)
    description = Column(String(256))
    is_editable = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint("config_key", "scope_type", "scope_id", name="uk_sc_key_scope"),
    )


class SysConfigHistory(Base):
    __tablename__ = "sys_config_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(BigInteger, ForeignKey("sys_config.id"), nullable=False)
    old_value = Column(String(512), nullable=False)
    new_value = Column(String(512), nullable=False)
    changed_by = Column(BigInteger)
    changed_at = Column(DateTime, server_default=func.now())


class FinancialTransaction(Base):
    __tablename__ = "financial_transaction"
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(Integer, nullable=False)
    category = Column(String(64), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    batch_id = Column(BigInteger, ForeignKey("batch.id"))
    ref_table = Column(String(64))
    ref_id = Column(BigInteger)
    transaction_date = Column(Date, nullable=False)
    payee_payer = Column(String(128))
    remark = Column(String(256))
    voucher_no = Column(String(64))
    created_by = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())


class CostAllocation(Base):
    __tablename__ = "cost_allocation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    cost_type = Column(Integer, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    quantity = Column(Numeric(10, 2))
    unit_cost = Column(Numeric(10, 4))
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class ProfitAnalysis(Base):
    __tablename__ = "profit_analysis"
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(BigInteger, ForeignKey("batch.id"), nullable=False)
    total_revenue = Column(Numeric(14, 2), nullable=False)
    total_cost = Column(Numeric(14, 2), nullable=False)
    gross_profit = Column(Numeric(14, 2), nullable=False)
    profit_margin = Column(Numeric(5, 2), nullable=False)
    cost_per_bird = Column(Numeric(10, 2))
    revenue_per_bird = Column(Numeric(10, 2))
    analysis_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
