"""实验管理模块测试"""
import pytest
import time


class TestExperimentCRUD:
    """实验增删改查测试"""

    def test_list_experiments(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/experiments/list", params={"page": 1, "page_size": 20}, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_create_experiment(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"实验项目_{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        response = client.post("/api/v1/experiments/create", json={
            "name": f"测试实验_{int(time.time())}",
            "project_id": project_id,
            "exp_type": "material",
            "status": "draft",
            "description": "实验描述",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_get_experiment(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"实验查询项目_{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/experiments/create", json={
            "name": f"查询实验_{int(time.time())}",
            "project_id": project_id,
            "exp_type": "material",
            "status": "draft",
        }, headers=headers)
        exp_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/experiments/{exp_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == exp_id

    def test_update_experiment(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"实验更新项目_{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/experiments/create", json={
            "name": f"更新实验_{int(time.time())}",
            "project_id": project_id,
            "exp_type": "material",
            "status": "draft",
        }, headers=headers)
        exp_id = create_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/experiments/{exp_id}", json={
            "name": f"更新后的名称_{int(time.time())}",
        }, headers=headers)
        assert response.status_code == 200

    def test_delete_experiment(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"实验删除项目_{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        create_resp = client.post("/api/v1/experiments/create", json={
            "name": f"删除实验_{int(time.time())}",
            "project_id": project_id,
            "exp_type": "material",
            "status": "draft",
        }, headers=headers)
        exp_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/experiments/{exp_id}", headers=headers)
        assert response.status_code == 200


class TestExperimentRecords:
    """实验记录测试"""

    def test_add_experiment_record(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"记录实验项目_{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        exp_resp = client.post("/api/v1/experiments/create", json={
            "name": f"记录实验_{int(time.time())}",
            "project_id": project_id,
            "exp_type": "material",
            "status": "in_progress",
        }, headers=headers)
        exp_id = exp_resp.json()["data"]["id"]

        response = client.post("/api/v1/experiments/records", json={
            "experiment_id": exp_id,
            "batch_no": f"BATCH-{int(time.time())}",
            "sample_code": "SMP001",
            "result_summary": "测试结果",
            "conclusion": "pass",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_list_experiment_records(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"记录列表实验项目_{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        exp_resp = client.post("/api/v1/experiments/create", json={
            "name": f"记录列表实验_{int(time.time())}",
            "project_id": project_id,
            "exp_type": "material",
            "status": "in_progress",
        }, headers=headers)
        exp_id = exp_resp.json()["data"]["id"]

        client.post("/api/v1/experiments/records", json={
            "experiment_id": exp_id,
            "batch_no": f"BATCH-LIST-{int(time.time())}",
            "result_summary": "记录内容",
            "conclusion": "pass",
        }, headers=headers)

        response = client.get(f"/api/v1/experiments/{exp_id}/records", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data

    def test_update_experiment_record(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"更新记录实验项目_{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        exp_resp = client.post("/api/v1/experiments/create", json={
            "name": f"更新记录实验_{int(time.time())}",
            "project_id": project_id,
            "exp_type": "material",
            "status": "in_progress",
        }, headers=headers)
        exp_id = exp_resp.json()["data"]["id"]

        record_resp = client.post("/api/v1/experiments/records", json={
            "experiment_id": exp_id,
            "batch_no": f"BATCH-UPDATE-{int(time.time())}",
            "result_summary": "待更新内容",
            "conclusion": "pass",
        }, headers=headers)
        record_id = record_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/experiments/records/{record_id}", json={
            "result_summary": "已更新内容",
            "conclusion": "fail",
        }, headers=headers)
        assert response.status_code == 200

    def test_delete_experiment_record(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"删除记录实验项目_{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        exp_resp = client.post("/api/v1/experiments/create", json={
            "name": f"删除记录实验_{int(time.time())}",
            "project_id": project_id,
            "exp_type": "material",
            "status": "in_progress",
        }, headers=headers)
        exp_id = exp_resp.json()["data"]["id"]

        record_resp = client.post("/api/v1/experiments/records", json={
            "experiment_id": exp_id,
            "batch_no": f"BATCH-DEL-{int(time.time())}",
            "result_summary": "待删除内容",
            "conclusion": "pass",
        }, headers=headers)
        record_id = record_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/experiments/records/{record_id}", headers=headers)
        assert response.status_code == 200


class TestExperimentStatus:
    """实验状态流转测试"""

    def test_change_experiment_status(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        project_resp = client.post("/api/v1/projects/create", json={
            "name": f"状态实验项目_{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = project_resp.json()["data"]["id"]

        exp_resp = client.post("/api/v1/experiments/create", json={
            "name": f"状态实验_{int(time.time())}",
            "project_id": project_id,
            "exp_type": "material",
            "status": "draft",
        }, headers=headers)
        exp_id = exp_resp.json()["data"]["id"]

        response = client.post(f"/api/v1/experiments/{exp_id}/status", json={"action": "start"}, headers=headers)
        assert response.status_code == 200


class TestExperimentValidation:
    """实验参数校验测试"""

    def test_create_experiment_validation(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.post("/api/v1/experiments/create", json={
            "name": "测试实验",
            "exp_type": "material",
        }, headers=headers)
        assert response.status_code == 422