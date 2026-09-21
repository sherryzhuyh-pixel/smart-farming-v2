"""AI智慧养殖系统V2.0 - API 测试用例

覆盖8个P0模块的API测试:
1. 个体生长曲线 (growth)
2. 批次全生命周期 (batches)
3. 性能偏差看板 (performance)
4. 中试效果对比 (pilot)
5. 财务收支管理 (finance)
6. 批次利润分析 (profit)
7. 溯源查询 (traceability)
8. 库存管理 (inventory)

通用功能:
- 统一响应格式验证
- 分页、排序、筛选
- 配置型设计 (sys_config)
"""
import pytest
from datetime import date


# =============================================================================
# 基础接口测试
# =============================================================================

class TestHealth:
    def test_health_check(self, client):
        """健康检查接口"""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_root(self, client):
        """根路径"""
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["name"] == "AI智慧养殖系统V2.0"


# =============================================================================
# 1. 批次全生命周期 (batches)
# =============================================================================

class TestBatches:
    def test_list_batches_empty(self, client):
        """空批次列表"""
        resp = client.get("/api/v2/batches")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_list_batches_with_data(self, client, seed_batch):
        """有数据的批次列表"""
        resp = client.get("/api/v2/batches")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]) == 1
        assert data["data"][0]["batch_no"] == "B20240921001"
        assert data["pagination"]["total"] == 1

    def test_list_batches_filter_by_status(self, client, seed_batch):
        """按状态筛选批次"""
        resp = client.get("/api/v2/batches?status=1")
        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] == 1

        resp = client.get("/api/v2/batches?status=99")
        assert resp.json()["pagination"]["total"] == 0

    def test_list_batches_filter_by_keyword(self, client, seed_batch):
        """关键字搜索"""
        resp = client.get("/api/v2/batches?keyword=张三")
        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] == 1

        resp = client.get("/api/v2/batches?keyword=不存在的")
        assert resp.json()["pagination"]["total"] == 0

    def test_list_batches_pagination(self, client, seed_batch):
        """分页测试"""
        resp = client.get("/api/v2/batches?page=1&page_size=5")
        assert resp.status_code == 200
        assert resp.json()["pagination"]["page_size"] == 5

    def test_get_batch_detail(self, client, seed_batch):
        """批次详情"""
        resp = client.get(f"/api/v2/batches/{seed_batch.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["batch_no"] == "B20240921001"
        assert data["data"]["breed"]["breed_name"] == "爱拔益加"

    def test_get_batch_detail_not_found(self, client):
        """不存在的批次"""
        resp = client.get("/api/v2/batches/99999")
        assert resp.status_code == 200
        assert resp.json()["code"] != 0

    def test_get_batch_lifecycle(self, client, seed_batch):
        """批次生命周期聚合"""
        resp = client.get(f"/api/v2/batches/{seed_batch.id}/lifecycle")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["batch_id"] == seed_batch.id
        assert "individual_count" in data["data"]
        assert "mortality" in data["data"]
        assert "recent_operations" in data["data"]

    def test_get_batch_growth_summary(self, client, seed_batch):
        """批次生长汇总"""
        resp = client.get(f"/api/v2/batches/{seed_batch.id}/growth-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["batch_id"] == seed_batch.id
        assert "avg_weight" in data["data"]

    def test_get_batch_performance(self, client, seed_batch):
        """批次性能偏差"""
        resp = client.get(f"/api/v2/batches/{seed_batch.id}/performance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "survival_rate" in data["data"]
        assert "daily_gain" in data["data"]
        assert "feed_meat_ratio" in data["data"]

    def test_get_batch_profit(self, client, seed_batch, seed_financial):
        """批次利润分析"""
        resp = client.get(f"/api/v2/batches/{seed_batch.id}/profit")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["batch_id"] == seed_batch.id
        assert "total_revenue" in data["data"]
        assert "total_cost" in data["data"]


# =============================================================================
# 2. 个体生长曲线 (growth)
# =============================================================================

class TestGrowth:
    def test_growth_curve_not_found(self, client):
        """不存在的个体生长曲线"""
        resp = client.get("/api/v2/individuals/99999/growth-curve")
        assert resp.status_code == 200
        assert resp.json()["code"] != 0

    def test_growth_records_not_found(self, client):
        """不存在的个体生长记录"""
        resp = client.get("/api/v2/individuals/99999/growth-records")
        assert resp.status_code == 200
        assert resp.json()["code"] != 0

    def test_pedigree_not_found(self, client):
        """不存在的个体谱系"""
        resp = client.get("/api/v2/individuals/99999/pedigree")
        assert resp.status_code == 200
        assert resp.json()["code"] != 0


# =============================================================================
# 3. 性能偏差看板 (performance)
# =============================================================================

class TestPerformance:
    def test_performance_dashboard(self, client):
        """性能偏差看板"""
        resp = client.get("/api/v2/performance/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "data" in data

    def test_performance_deviation(self, client):
        """性能偏差列表"""
        resp = client.get("/api/v2/performance/deviation")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "data" in data

    def test_performance_benchmark(self, client):
        """标准数据对比"""
        resp = client.get("/api/v2/performance/benchmark")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "data" in data


# =============================================================================
# 4. 中试效果对比 (pilot)
# =============================================================================

class TestPilot:
    def test_list_pilots_empty(self, client):
        """空中试项目列表"""
        resp = client.get("/api/v2/pilots")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"] == []

    def test_get_pilot_not_found(self, client):
        """不存在的中试项目"""
        resp = client.get("/api/v2/pilots/99999")
        assert resp.status_code == 200
        assert resp.json()["code"] != 0

    def test_pilot_comparison_not_found(self, client):
        """不存在的中试对比"""
        resp = client.get("/api/v2/pilots/99999/comparison")
        assert resp.status_code == 200
        assert resp.json()["code"] != 0


# =============================================================================
# 5. 财务收支管理 (finance)
# =============================================================================

class TestFinance:
    def test_list_transactions_empty(self, client):
        """空收支列表"""
        resp = client.get("/api/v2/financial-transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["list"] == []

    def test_list_transactions_with_data(self, client, seed_financial):
        """有数据的收支列表"""
        resp = client.get("/api/v2/financial-transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]["list"]) == 3
        assert data["data"]["summary"]["total_income"] == 500000.0
        assert data["data"]["summary"]["total_expense"] == 200000.0
        assert data["data"]["summary"]["net_profit"] == 300000.0

    def test_list_transactions_filter_by_type(self, client, seed_financial):
        """按收支类型筛选"""
        resp = client.get("/api/v2/financial-transactions?transaction_type=1")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["list"]) == 1
        assert resp.json()["data"]["list"][0]["transaction_type"] == 1

        resp = client.get("/api/v2/financial-transactions?transaction_type=2")
        assert len(resp.json()["data"]["list"]) == 2

    def test_list_transactions_filter_by_date(self, client, seed_financial):
        """按日期范围筛选"""
        resp = client.get("/api/v2/financial-transactions?start_date=2024-09-01&end_date=2024-09-30")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["list"]) == 3

    def test_create_transaction(self, client, seed_batch):
        """创建收支记录"""
        payload = {
            "transaction_type": 2,
            "category": "人工费",
            "amount": 15000.0,
            "batch_id": seed_batch.id,
            "transaction_date": "2024-09-20",
            "payee_payer": "劳务公司",
            "remark": "临时工费用",
            "created_by": "admin",
        }
        resp = client.post("/api/v2/financial-transactions", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["category"] == "人工费"
        assert data["message"] == "创建成功"

    def test_finance_summary(self, client, seed_financial):
        """收支汇总"""
        resp = client.get("/api/v2/financial-transactions/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["summary"]["total_income"] == 500000.0
        assert data["data"]["summary"]["total_expense"] == 200000.0

    def test_finance_summary_group_by_month(self, client, seed_financial):
        """按月分组汇总"""
        resp = client.get("/api/v2/financial-transactions/summary?group_by=month")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]["grouped_data"]) > 0

    def test_finance_summary_with_date_range(self, client, seed_financial):
        """带日期范围的汇总"""
        resp = client.get("/api/v2/financial-transactions/summary?start_date=2024-09-01&end_date=2024-09-30")
        assert resp.status_code == 200
        assert resp.json()["code"] == 0


# =============================================================================
# 6. 批次利润分析 (profit)
# =============================================================================

class TestProfit:
    def test_profit_ranking(self, client):
        """利润排名"""
        resp = client.get("/api/v2/profit/ranking")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "data" in data

    def test_profit_trend(self, client):
        """利润趋势"""
        resp = client.get("/api/v2/profit/trend")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "data" in data

    def test_batch_profit_detail(self, client, seed_batch):
        """批次利润详情 - 通过batches路由"""
        resp = client.get(f"/api/v2/batches/{seed_batch.id}/profit")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "total_revenue" in data["data"]
        assert "total_cost" in data["data"]
        assert "gross_profit" in data["data"]


# =============================================================================
# 7. 溯源查询 (traceability)
# =============================================================================

class TestTraceability:
    def test_traceability_not_found(self, client):
        """不存在的溯源码"""
        resp = client.get("/api/v2/traceability/INVALID_CODE")
        assert resp.status_code == 200
        assert resp.json()["code"] != 0

    def test_traceability_completeness(self, client):
        """溯源完整度统计"""
        resp = client.get("/api/v2/traceability/completeness")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "data" in data


# =============================================================================
# 8. 库存管理 (inventory)
# =============================================================================

class TestInventory:
    def test_list_inventory_empty(self, client):
        """空库存列表"""
        resp = client.get("/api/v2/inventory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["list"] == []
        assert data["data"]["summary"]["total_items"] == 0

    def test_list_inventory_with_data(self, client, seed_inventory):
        """有数据的库存列表"""
        resp = client.get("/api/v2/inventory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]["list"]) == 2
        assert data["pagination"]["total"] == 2

    def test_list_inventory_filter_by_type(self, client, seed_inventory):
        """按类型筛选库存"""
        resp = client.get("/api/v2/inventory?item_category=1")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["list"]) == 1
        assert resp.json()["data"]["list"][0]["item_name"] == "雏鸡饲料A"

    def test_list_inventory_filter_by_keyword(self, client, seed_inventory):
        """关键字搜索库存"""
        resp = client.get("/api/v2/inventory?keyword=疫苗")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["list"]) == 1
        assert resp.json()["data"]["list"][0]["item_name"] == "疫苗B"

    def test_create_inventory(self, client):
        """创建库存记录"""
        payload = {
            "item_code": "T001",
            "item_name": "测试物资",
            "item_category": 4,
            "item_spec": "标准",
            "quantity": 100.0,
            "unit": "件",
            "safety_stock": 10.0,
            "status": 1,
        }
        resp = client.post("/api/v2/inventory", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["item_code"] == "T001"

    def test_inventory_alerts(self, client, seed_inventory):
        """库存预警查询"""
        resp = client.get("/api/v2/inventory/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "data" in data
        # 疫苗B数量(10)低于安全库存(20)，应出现在预警中
        alert_items = data["data"]
        low_stock = [a for a in alert_items if a.get("alert_type") == "low_stock"]
        assert len(low_stock) >= 1

    def test_inventory_transaction(self, client, seed_inventory):
        """库存出入库"""
        inv_id = seed_inventory[0].id
        payload = {
            "transaction_type": "out",
            "quantity": 10.0,
            "reason": "领用",
            "operator": "李四",
        }
        resp = client.post(f"/api/v2/inventory/{inv_id}/transactions", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["transaction_type"] == "out"
        assert data["data"]["quantity"] == 10.0

    def test_inventory_transactions_list(self, client, seed_inventory):
        """库存流水查询"""
        inv_id = seed_inventory[0].id
        resp = client.get(f"/api/v2/inventory/{inv_id}/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "data" in data


# =============================================================================
# 9. 系统配置 (config) - 三级作用域
# =============================================================================

class TestConfig:
    def test_list_config_empty(self, client):
        """空配置列表"""
        resp = client.get("/api/v2/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"] == []

    def test_create_config_global(self, client):
        """创建全局配置"""
        payload = {
            "config_key": "trace_mode",
            "config_value": "ear_tag",
            "config_desc": "个体追踪模式：ear_tag=耳标扫码, sampling=批次抽样",
            "scope_type": 1,
            "scope_id": 0,
        }
        resp = client.post("/api/v2/config", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["config_key"] == "trace_mode"
        assert data["data"]["scope_type"] == 1

    def test_create_config_house(self, client, seed_house):
        """创建鸡舍级配置"""
        payload = {
            "config_key": "target_temperature",
            "config_value": "26",
            "config_desc": "目标温度",
            "scope_type": 2,
            "scope_id": seed_house.id,
        }
        resp = client.post("/api/v2/config", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["scope_type"] == 2

    def test_list_config_filter_by_scope(self, client):
        """按作用域筛选配置"""
        resp = client.get("/api/v2/config?scope_type=1")
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

    def test_update_config(self, client):
        """更新配置"""
        # 先创建
        payload = {
            "config_key": "auto_finance",
            "config_value": "0",
            "config_desc": "财务自动联动",
            "scope_type": 1,
            "scope_id": 0,
        }
        create_resp = client.post("/api/v2/config", json=payload)
        config_id = create_resp.json()["data"]["id"]

        # 再更新
        update_payload = {
            "config_value": "1",
            "config_desc": "财务自动联动-已启用",
        }
        resp = client.put(f"/api/v2/config/{config_id}", json=update_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["config_value"] == "1"

    def test_config_history(self, client):
        """配置变更历史"""
        # 先创建
        payload = {
            "config_key": "history_test",
            "config_value": "v1",
            "config_desc": "历史测试",
            "scope_type": 1,
            "scope_id": 0,
        }
        create_resp = client.post("/api/v2/config", json=payload)
        config_id = create_resp.json()["data"]["id"]

        # 更新一次
        client.put(f"/api/v2/config/{config_id}", json={"config_value": "v2"})

        resp = client.get(f"/api/v2/config/{config_id}/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]) >= 1


# =============================================================================
# 10. 通用响应格式验证
# =============================================================================

class TestResponseFormat:
    def test_success_response_structure(self, client, seed_batch):
        """成功响应结构验证"""
        resp = client.get(f"/api/v2/batches/{seed_batch.id}")
        data = resp.json()
        assert "code" in data
        assert "message" in data
        assert "data" in data
        assert isinstance(data["code"], int)
        assert isinstance(data["message"], str)

    def test_paginated_response_structure(self, client, seed_batch):
        """分页响应结构验证"""
        resp = client.get("/api/v2/batches")
        data = resp.json()
        assert "code" in data
        assert "message" in data
        assert "data" in data
        assert "pagination" in data
        assert "page" in data["pagination"]
        assert "page_size" in data["pagination"]
        assert "total" in data["pagination"]
        assert "total_pages" in data["pagination"]

    def test_error_response_structure(self, client):
        """错误响应结构验证"""
        resp = client.get("/api/v2/batches/99999")
        data = resp.json()
        assert "code" in data
        assert "message" in data
        assert data["code"] != 0


# =============================================================================
# 11. 边界条件测试
# =============================================================================

class TestEdgeCases:
    def test_invalid_page_number(self, client):
        """无效页码 - FastAPI 会自动校验 ge=1"""
        resp = client.get("/api/v2/batches?page=0")
        # FastAPI validation returns 422
        assert resp.status_code == 422

    def test_invalid_page_size_too_large(self, client):
        """页码过大 - FastAPI 会自动校验 le=100"""
        resp = client.get("/api/v2/batches?page_size=200")
        assert resp.status_code == 422

    def test_empty_post_body(self, client):
        """空POST请求体"""
        resp = client.post("/api/v2/financial-transactions", json={})
        # Should handle gracefully
        assert resp.status_code in [200, 422]

    def test_special_chars_in_keyword(self, client):
        """特殊字符搜索"""
        resp = client.get("/api/v2/batches?keyword=%25%27%3B")
        assert resp.status_code == 200

    def test_date_format_validation(self, client):
        """日期格式校验"""
        resp = client.get("/api/v2/financial-transactions?start_date=invalid")
        assert resp.status_code == 422
