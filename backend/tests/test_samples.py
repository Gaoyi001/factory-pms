"""样品试产模块测试"""
import pytest
import time


class TestSampleCRUD:
    """样品增删改查测试"""

    def test_list_samples(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/samples/samples", params={"page": 1, "page_size": 20}, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_create_sample(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"样品项目_{int(time.time())}",
            "code": f"SP-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        response = client.post("/api/v1/samples/samples", json={
            "name": f"测试样品_{int(time.time())}",
            "project_id": project_id,
            "sample_type": "development",
            "status": "draft",
            "description": "样品描述",
            "quantity": 10,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_get_sample(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"查询样品项目_{int(time.time())}",
            "code": f"SPG-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/samples/samples", json={
            "name": f"查询样品_{int(time.time())}",
            "project_id": project_id,
            "sample_type": "development",
            "status": "active",
        }, headers=headers)
        sample_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/samples/samples/{sample_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == sample_id

    def test_update_sample(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"更新样品项目_{int(time.time())}",
            "code": f"SPU-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/samples/samples", json={
            "name": f"更新样品_{int(time.time())}",
            "project_id": project_id,
            "sample_type": "development",
            "status": "draft",
        }, headers=headers)
        sample_id = create_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/samples/samples/{sample_id}", json={
            "name": f"更新后的名称_{int(time.time())}",
            "status": "approved",
        }, headers=headers)
        assert response.status_code == 200

    def test_delete_sample(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"删除样品项目_{int(time.time())}",
            "code": f"SPD-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/samples/samples", json={
            "name": f"删除样品_{int(time.time())}",
            "project_id": project_id,
            "sample_type": "development",
            "status": "draft",
        }, headers=headers)
        sample_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/samples/samples/{sample_id}", headers=headers)
        assert response.status_code == 200


class TestSampleInspection:
    """样品检验测试"""

    def test_create_inspection(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"检验样品项目_{int(time.time())}",
            "code": f"SPI-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        sample_resp = client.post("/api/v1/samples/samples", json={
            "name": f"检验样品_{int(time.time())}",
            "project_id": project_id,
            "sample_type": "development",
            "status": "active",
        }, headers=headers)
        sample_id = sample_resp.json()["data"]["id"]

        response = client.post("/api/v1/samples/inspections", json={
            "sample_id": sample_id,
            "inspect_type": "外观检验",
            "result": "合格",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "inspect_no" in data

    def test_list_inspections(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"检验列表样品项目_{int(time.time())}",
            "code": f"SPIL-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        sample_resp = client.post("/api/v1/samples/samples", json={
            "name": f"检验列表样品_{int(time.time())}",
            "project_id": project_id,
            "sample_type": "development",
            "status": "active",
        }, headers=headers)
        sample_id = sample_resp.json()["data"]["id"]

        client.post("/api/v1/samples/inspections", json={
            "sample_id": sample_id,
            "inspect_type": "外观检验",
            "result": "合格",
        }, headers=headers)

        response = client.get(f"/api/v1/samples/samples/{sample_id}/inspections", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)


class TestTrialProduction:
    """试产记录测试"""

    def test_create_trial_production(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"试产样品项目_{int(time.time())}",
            "code": f"SPTP-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        sample_resp = client.post("/api/v1/samples/samples", json={
            "name": f"试产样品_{int(time.time())}",
            "project_id": project_id,
            "sample_type": "development",
            "status": "approved",
        }, headers=headers)
        sample_id = sample_resp.json()["data"]["id"]

        response = client.post("/api/v1/samples/trials", json={
            "project_id": project_id,
            "sample_id": sample_id,
            "name": f"试产记录_{int(time.time())}",
            "status": "completed",
            "plan_qty": 100,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_list_trial_productions(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/samples/trials", params={"page": 1, "page_size": 20}, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_update_trial_production(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"更新试产样品项目_{int(time.time())}",
            "code": f"SPTPU-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        sample_resp = client.post("/api/v1/samples/samples", json={
            "name": f"更新试产样品_{int(time.time())}",
            "project_id": project_id,
            "sample_type": "development",
            "status": "approved",
        }, headers=headers)
        sample_id = sample_resp.json()["data"]["id"]

        tp_resp = client.post("/api/v1/samples/trials", json={
            "project_id": project_id,
            "sample_id": sample_id,
            "name": f"试产记录_{int(time.time())}",
            "status": "completed",
            "plan_qty": 100,
        }, headers=headers)
        tp_id = tp_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/samples/trials/{tp_id}", json={
            "plan_qty": 150,
        }, headers=headers)
        assert response.status_code == 200


class TestSampleValidation:
    """样品参数校验测试"""

    def test_create_sample_validation(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.post("/api/v1/samples/samples", json={
            "sample_type": "development",
        }, headers=headers)
        assert response.status_code == 422
