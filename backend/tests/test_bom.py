"""BOM管理模块测试"""
import pytest
import time


class TestMaterialCRUD:
    """物料管理测试"""

    def test_list_materials(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/bom/materials", params={"page": 1, "page_size": 20}, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_create_material(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/bom/materials", json={
            "name": f"测试物料_{int(time.time())}",
            "code": f"M-{int(time.time())}",
            "spec": "测试规格",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_get_material(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/bom/materials", json={
            "name": f"查询物料_{int(time.time())}",
            "code": f"MG-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/bom/materials/{material_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == material_id

    def test_update_material(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/bom/materials", json={
            "name": f"更新物料_{int(time.time())}",
            "code": f"MU-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = create_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/bom/materials/{material_id}", json={
            "name": f"更新后的名称_{int(time.time())}",
        }, headers=headers)
        assert response.status_code == 200

    def test_delete_material(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/bom/materials", json={
            "name": f"删除物料_{int(time.time())}",
            "code": f"MD-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/bom/materials/{material_id}", headers=headers)
        assert response.status_code == 200


class TestBOMHeaderCRUD:
    """BOM表头增删改查测试"""

    def test_list_bom_headers(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/bom/headers", params={"page": 1, "page_size": 20}, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_create_bom_header(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/bom/headers", json={
            "name": f"BOM产品_{int(time.time())}",
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PRD-{int(time.time())}",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_get_bom_header(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/bom/headers", json={
            "name": f"BOM查询产品_{int(time.time())}",
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PRDG-{int(time.time())}",
        }, headers=headers)
        bom_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/bom/headers/{bom_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == bom_id

    def test_update_bom_header(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/bom/headers", json={
            "name": f"BOM更新产品_{int(time.time())}",
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PRDU-{int(time.time())}",
        }, headers=headers)
        bom_id = create_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/bom/headers/{bom_id}", json={
            "name": f"更新后的名称_{int(time.time())}",
            "status": "released",
        }, headers=headers)
        assert response.status_code == 200

    def test_delete_bom_header(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/bom/headers", json={
            "name": f"BOM删除产品_{int(time.time())}",
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PRDD-{int(time.time())}",
        }, headers=headers)
        bom_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/bom/headers/{bom_id}", headers=headers)
        assert response.status_code == 200


class TestBOMItems:
    """BOM明细测试"""

    def test_add_bom_item(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        bom_resp = client.post("/api/v1/bom/headers", json={
            "name": f"BOM明细产品_{int(time.time())}",
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PRDI-{int(time.time())}",
        }, headers=headers)
        bom_id = bom_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"BOM物料_{int(time.time())}",
            "code": f"BOMM-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        response = client.post(f"/api/v1/bom/headers/{bom_id}/items", json={
            "material_id": material_id,
            "quantity": "10",
            "unit": "个",
            "line_no": 1,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_list_bom_items(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        bom_resp = client.post("/api/v1/bom/headers", json={
            "name": f"BOM列表产品_{int(time.time())}",
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PRDL-{int(time.time())}",
        }, headers=headers)
        bom_id = bom_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"BOM列表物料_{int(time.time())}",
            "code": f"BOMML-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        client.post(f"/api/v1/bom/headers/{bom_id}/items", json={
            "material_id": material_id,
            "quantity": "5",
            "unit": "个",
            "line_no": 1,
        }, headers=headers)

        response = client.get(f"/api/v1/bom/headers/{bom_id}/items", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data

    def test_update_bom_item(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        bom_resp = client.post("/api/v1/bom/headers", json={
            "name": f"BOM更新明细产品_{int(time.time())}",
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PRDUI-{int(time.time())}",
        }, headers=headers)
        bom_id = bom_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"BOM更新物料_{int(time.time())}",
            "code": f"BOMMU-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        item_resp = client.post(f"/api/v1/bom/headers/{bom_id}/items", json={
            "material_id": material_id,
            "quantity": "5",
            "unit": "个",
            "line_no": 1,
        }, headers=headers)
        item_id = item_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/bom/headers/{bom_id}/items/{item_id}", json={
            "quantity": "15",
        }, headers=headers)
        assert response.status_code == 200

    def test_delete_bom_item(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        bom_resp = client.post("/api/v1/bom/headers", json={
            "name": f"BOM删除明细产品_{int(time.time())}",
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PRDDI-{int(time.time())}",
        }, headers=headers)
        bom_id = bom_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"BOM删除物料_{int(time.time())}",
            "code": f"BOMMD-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        item_resp = client.post(f"/api/v1/bom/headers/{bom_id}/items", json={
            "material_id": material_id,
            "quantity": "5",
            "unit": "个",
            "line_no": 1,
        }, headers=headers)
        item_id = item_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/bom/headers/{bom_id}/items/{item_id}", headers=headers)
        assert response.status_code == 200


class TestBOMChangeOrder:
    """BOM变更单测试"""

    def test_create_change_order(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        bom_resp = client.post("/api/v1/bom/headers", json={
            "name": f"BOM变更产品_{int(time.time())}",
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PRDCO-{int(time.time())}",
        }, headers=headers)
        bom_id = bom_resp.json()["data"]["id"]

        response = client.post("/api/v1/bom/changes", json={
            "bom_id": bom_id,
            "change_type": "modify",
            "title": "变更标题",
            "reason": "设计变更",
            "description": "变更描述",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "change_no" in data

    def test_list_change_orders(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/bom/changes", params={"page": 1, "page_size": 20}, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data

    def test_delete_change_order(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        bom_resp = client.post("/api/v1/bom/headers", json={
            "name": f"BOM变更删除产品_{int(time.time())}",
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PRDCD-{int(time.time())}",
        }, headers=headers)
        bom_id = bom_resp.json()["data"]["id"]

        co_resp = client.post("/api/v1/bom/changes", json={
            "bom_id": bom_id,
            "change_type": "modify",
            "title": "待删除变更",
            "reason": "测试",
        }, headers=headers)
        co_data = co_resp.json()["data"]

        change_no = co_data["change_no"]
        change_id = None
        list_resp = client.get("/api/v1/bom/changes", params={"keyword": change_no}, headers=headers)
        if list_resp.json()["data"]["items"]:
            change_id = list_resp.json()["data"]["items"][0]["id"]

        if change_id:
            response = client.delete(f"/api/v1/bom/changes/{change_id}", headers=headers)
            assert response.status_code == 200


class TestBOMValidation:
    """BOM参数校验测试"""

    def test_create_bom_validation(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.post("/api/v1/bom/headers", json={
            "version": "V1.0",
            "status": "draft",
        }, headers=headers)
        assert response.status_code == 422

    def test_invalid_bom_item_quantity(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        bom_resp = client.post("/api/v1/bom/headers", json={
            "name": f"BOM校验产品_{int(time.time())}",
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PRDIV-{int(time.time())}",
        }, headers=headers)
        bom_id = bom_resp.json()["data"]["id"]

        material_resp = client.post("/api/v1/bom/materials", json={
            "name": f"BOM校验物料_{int(time.time())}",
            "code": f"BOMMV-{int(time.time())}",
            "unit": "个",
            "material_type": "原材料",
            "status": "active",
        }, headers=headers)
        material_id = material_resp.json()["data"]["id"]

        response = client.post(f"/api/v1/bom/headers/{bom_id}/items", json={
            "material_id": material_id,
            "quantity": -1,
            "unit": "个",
        }, headers=headers)
        assert response.status_code == 422