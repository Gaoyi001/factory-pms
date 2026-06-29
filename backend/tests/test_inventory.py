"""库存管理模块测试"""
import pytest
import time


class TestWarehouseCRUD:
    """仓库增删改查测试"""

    def test_list_warehouses(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/inventory/warehouses/list", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    def test_create_warehouse(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"测试仓库_{int(time.time())}",
            "code": f"W-{int(time.time())}",
            "location": "测试位置",
            "description": "仓库描述",
            "is_active": True,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_get_warehouse(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"查询仓库_{int(time.time())}",
            "code": f"WG-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/inventory/warehouses/{warehouse_id}", headers=headers)
        assert response.status_code == 405

    def test_update_warehouse(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"更新仓库_{int(time.time())}",
            "code": f"WU-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_id = create_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/inventory/warehouses/{warehouse_id}", json={
            "name": f"更新后的名称_{int(time.time())}",
            "is_active": False,
        }, headers=headers)
        assert response.status_code == 200

    def test_delete_warehouse(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"删除仓库_{int(time.time())}",
            "code": f"WD-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/inventory/warehouses/{warehouse_id}", headers=headers)
        assert response.status_code == 200


class TestInventoryCRUD:
    """库存记录测试"""

    def test_list_inventory(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/inventory/list", params={"page": 1, "page_size": 20}, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_create_inventory(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        warehouse_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"库存仓库_{int(time.time())}",
            "code": f"WI-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_id = warehouse_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"库存物料_{int(time.time())}",
            "code": f"MI-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        response = client.post("/api/v1/inventory/create", json={
            "material_id": material_id,
            "warehouse_id": warehouse_id,
            "quantity": 100,
            "unit": "个",
            "safety_stock": 10,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data


class TestInventoryOperations:
    """库存操作测试"""

    def test_inventory_income(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        warehouse_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"入库仓库_{int(time.time())}",
            "code": f"WIN-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_id = warehouse_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"入库物料_{int(time.time())}",
            "code": f"MIN-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/inventory/create", json={
            "material_id": material_id,
            "warehouse_id": warehouse_id,
            "quantity": 50,
            "unit": "个",
        }, headers=headers)
        inventory_item_id = create_resp.json()["data"]["id"]

        response = client.post("/api/v1/inventory/inbound", json={
            "inventory_item_id": inventory_item_id,
            "quantity": 50,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_inventory_outcome(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        warehouse_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"出库仓库_{int(time.time())}",
            "code": f"WOUT-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_id = warehouse_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"出库物料_{int(time.time())}",
            "code": f"MOUT-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/inventory/create", json={
            "material_id": material_id,
            "warehouse_id": warehouse_id,
            "quantity": 100,
            "unit": "个",
        }, headers=headers)
        inventory_item_id = create_resp.json()["data"]["id"]

        response = client.post("/api/v1/inventory/outbound", json={
            "inventory_item_id": inventory_item_id,
            "quantity": 30,
        }, headers=headers)
        assert response.status_code == 200

    def test_inventory_transfer(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        warehouse_a_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"调拨源仓库_{int(time.time())}",
            "code": f"WAT-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_a_id = warehouse_a_resp.json()["data"]["id"]

        warehouse_b_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"调拨目标仓库_{int(time.time())}",
            "code": f"WBT-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_b_id = warehouse_b_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"调拨物料_{int(time.time())}",
            "code": f"MT-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/inventory/create", json={
            "material_id": material_id,
            "warehouse_id": warehouse_a_id,
            "quantity": 100,
            "unit": "个",
        }, headers=headers)
        inventory_item_id = create_resp.json()["data"]["id"]

        response = client.post("/api/v1/inventory/transfer", json={
            "inventory_item_id": inventory_item_id,
            "source_warehouse_id": warehouse_a_id,
            "target_warehouse_id": warehouse_b_id,
            "quantity": 30,
        }, headers=headers)
        assert response.status_code == 200

    def test_inventory_check(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        warehouse_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"盘点仓库_{int(time.time())}",
            "code": f"WCHK-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_id = warehouse_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"盘点物料_{int(time.time())}",
            "code": f"MCHK-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/inventory/create", json={
            "material_id": material_id,
            "warehouse_id": warehouse_id,
            "quantity": 100,
            "unit": "个",
        }, headers=headers)
        inventory_item_id = create_resp.json()["data"]["id"]

        response = client.post("/api/v1/inventory/check", json={
            "inventory_item_id": inventory_item_id,
            "quantity": 95,
        }, headers=headers)
        assert response.status_code == 200


class TestInventoryApproval:
    """库存审批测试"""

    def test_submit_approval(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        warehouse_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"审批仓库_{int(time.time())}",
            "code": f"WAPR-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_id = warehouse_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"审批物料_{int(time.time())}",
            "code": f"MAPR-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/inventory/create", json={
            "material_id": material_id,
            "warehouse_id": warehouse_id,
            "quantity": 100,
            "unit": "个",
        }, headers=headers)
        inventory_item_id = create_resp.json()["data"]["id"]

        outbound_resp = client.post("/api/v1/inventory/outbound", json={
            "inventory_item_id": inventory_item_id,
            "quantity": 30,
            "approval_required": True,
        }, headers=headers)
        tx_id = outbound_resp.json()["data"]["id"]

        response = client.post(f"/api/v1/inventory/approvals/{tx_id}/submit", json={
            "approval_level": 1,
            "approver_id": 1,
            "approver_name": "审批人",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_approve_request(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        warehouse_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"审批通过仓库_{int(time.time())}",
            "code": f"WAPRV-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_id = warehouse_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"审批通过物料_{int(time.time())}",
            "code": f"MAPRV-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/inventory/create", json={
            "material_id": material_id,
            "warehouse_id": warehouse_id,
            "quantity": 100,
            "unit": "个",
        }, headers=headers)
        inventory_item_id = create_resp.json()["data"]["id"]

        outbound_resp = client.post("/api/v1/inventory/outbound", json={
            "inventory_item_id": inventory_item_id,
            "quantity": 50,
            "approval_required": True,
        }, headers=headers)
        tx_id = outbound_resp.json()["data"]["id"]

        submit_resp = client.post(f"/api/v1/inventory/approvals/{tx_id}/submit", json={
            "approval_level": 1,
            "approver_id": 1,
            "approver_name": "审批人",
        }, headers=headers)
        approval_id = submit_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/inventory/approvals/{approval_id}/action", json={
            "status": "approved",
        }, headers=headers)
        assert response.status_code == 200

    def test_reject_request(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        warehouse_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"审批拒绝仓库_{int(time.time())}",
            "code": f"WREJ-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_id = warehouse_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"审批拒绝物料_{int(time.time())}",
            "code": f"MREJ-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/inventory/create", json={
            "material_id": material_id,
            "warehouse_id": warehouse_id,
            "quantity": 100,
            "unit": "个",
        }, headers=headers)
        inventory_item_id = create_resp.json()["data"]["id"]

        outbound_resp = client.post("/api/v1/inventory/outbound", json={
            "inventory_item_id": inventory_item_id,
            "quantity": 25,
            "approval_required": True,
        }, headers=headers)
        tx_id = outbound_resp.json()["data"]["id"]

        submit_resp = client.post(f"/api/v1/inventory/approvals/{tx_id}/submit", json={
            "approval_level": 1,
            "approver_id": 1,
            "approver_name": "审批人",
        }, headers=headers)
        approval_id = submit_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/inventory/approvals/{approval_id}/action", json={
            "status": "rejected",
            "comment": "库存不足",
        }, headers=headers)
        assert response.status_code == 200


class TestInventoryAlerts:
    """库存预警测试"""

    def test_get_alerts(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/inventory/alerts", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    def test_get_alert_summary(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/inventory/alerts/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "unread" in data
        assert "unresolved" in data


class TestInventoryStats:
    """库存统计测试"""

    def test_get_overview(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/inventory/stats/overview", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_items" in data
        assert "total_quantity" in data


class TestInventoryValidation:
    """库存参数校验测试"""

    def test_invalid_income_quantity(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        warehouse_resp = client.post("/api/v1/inventory/warehouses/create", json={
            "name": f"校验仓库_{int(time.time())}",
            "code": f"WVAL-{int(time.time())}",
            "is_active": True,
        }, headers=headers)
        warehouse_id = warehouse_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"校验物料_{int(time.time())}",
            "code": f"MVAL-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/inventory/create", json={
            "material_id": material_id,
            "warehouse_id": warehouse_id,
            "quantity": 10,
            "unit": "个",
        }, headers=headers)
        inventory_item_id = create_resp.json()["data"]["id"]

        response = client.post("/api/v1/inventory/inbound", json={
            "inventory_item_id": inventory_item_id,
            "quantity": -10,
        }, headers=headers)
        assert response.status_code == 400