"""项目管理模块测试"""
import pytest
import time


class TestProjectCRUD:
    """项目增删改查测试"""

    def test_list_projects(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/projects/list", params={"page": 1, "page_size": 20}, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_get_project_types(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/projects/types", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    def test_create_project(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/projects/create", json={
            "name": f"测试项目_{int(time.time())}",
            "code": f"P-{int(time.time())}",
            "description": "项目描述",
            "priority": 3,
            "status": "draft",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_create_project_with_owner(self, client, admin_token, member_user, db):
        headers = {"Authorization": f"Bearer {admin_token}"}
        from app.models.user import User
        member = db.query(User).filter(User.username == "test_member").first()

        response = client.post("/api/v1/projects/create", json={
            "name": f"测试项目_owner_{int(time.time())}",
            "code": f"PO-{int(time.time())}",
            "owner_id": member.id,
            "status": "active",
        }, headers=headers)
        assert response.status_code == 200

    def test_get_project(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"查询项目_{int(time.time())}",
            "code": f"PG-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/projects/{project_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == project_id

    def test_update_project(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"更新项目_{int(time.time())}",
            "code": f"PU-{int(time.time())}",
            "status": "draft",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/projects/{project_id}", json={
            "name": f"更新后的名称_{int(time.time())}",
            "status": "active",
        }, headers=headers)
        assert response.status_code == 200

    def test_delete_project(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"删除项目_{int(time.time())}",
            "code": f"PD-{int(time.time())}",
            "status": "draft",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
        assert response.status_code == 200

        response = client.get(f"/api/v1/projects/{project_id}", headers=headers)
        assert response.status_code == 404


class TestProjectTasks:
    """项目任务测试"""

    def test_create_task(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"任务项目_{int(time.time())}",
            "code": f"PT-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        response = client.post(f"/api/v1/projects/{project_id}/tasks", json={
            "title": f"测试任务_{int(time.time())}",
            "description": "任务描述",
            "status": "pending",
            "priority": 3,
            "project_id": project_id,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_list_tasks(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"任务列表项目_{int(time.time())}",
            "code": f"PTL-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        client.post(f"/api/v1/projects/{project_id}/tasks", json={
            "title": f"任务1_{int(time.time())}",
            "status": "pending",
            "project_id": project_id,
        }, headers=headers)

        response = client.get(f"/api/v1/projects/{project_id}/tasks", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    def test_update_task(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"任务更新项目_{int(time.time())}",
            "code": f"PTU-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        task_resp = client.post(f"/api/v1/projects/{project_id}/tasks", json={
            "title": "待更新任务",
            "status": "pending",
            "project_id": project_id,
        }, headers=headers)
        task_id = task_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/projects/tasks/{task_id}", json={
            "title": "已更新任务",
            "status": "completed",
        }, headers=headers)
        assert response.status_code == 200

    def test_delete_task(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"任务删除项目_{int(time.time())}",
            "code": f"PTD-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        task_resp = client.post(f"/api/v1/projects/{project_id}/tasks", json={
            "title": "待删除任务",
            "status": "pending",
            "project_id": project_id,
        }, headers=headers)
        task_id = task_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/projects/tasks/{task_id}", headers=headers)
        assert response.status_code == 200


class TestProjectRequirements:
    """项目需求测试"""

    def test_create_requirement(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"需求项目_{int(time.time())}",
            "code": f"PR-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        response = client.post(f"/api/v1/projects/{project_id}/requirements", json={
            "title": f"测试需求_{int(time.time())}",
            "description": "需求描述",
            "priority": "should",
            "status": "pending",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_list_requirements(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"需求列表项目_{int(time.time())}",
            "code": f"PRL-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        client.post(f"/api/v1/projects/{project_id}/requirements", json={
            "title": f"需求1_{int(time.time())}",
            "status": "pending",
        }, headers=headers)

        response = client.get(f"/api/v1/projects/{project_id}/requirements", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    def test_update_requirement(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"需求更新项目_{int(time.time())}",
            "code": f"PRU-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        req_resp = client.post(f"/api/v1/projects/{project_id}/requirements", json={
            "title": "待更新需求",
            "status": "pending",
        }, headers=headers)
        req_id = req_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/projects/requirements/{req_id}", json={
            "title": "已更新需求",
            "status": "completed",
        }, headers=headers)
        assert response.status_code == 200

    def test_delete_requirement(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"需求删除项目_{int(time.time())}",
            "code": f"PRD-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        req_resp = client.post(f"/api/v1/projects/{project_id}/requirements", json={
            "title": "待删除需求",
            "status": "pending",
        }, headers=headers)
        req_id = req_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/projects/requirements/{req_id}", headers=headers)
        assert response.status_code == 200


class TestProjectDataIsolation:
    """项目数据隔离测试"""

    def test_member_can_see_own_project(self, client, member_token, admin_token, db):
        headers = {"Authorization": f"Bearer {member_token}"}
        from app.models.user import User
        member = db.query(User).filter(User.username == "test_member").first()

        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"成员项目_{int(time.time())}",
            "code": f"PM-{int(time.time())}",
            "status": "active",
            "owner_id": member.id,
        }, headers=admin_headers)
        project_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/projects/{project_id}", headers=headers)
        assert response.status_code == 200

    def test_member_cannot_see_other_project(self, client, member_token, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/projects/create", json={
            "name": f"管理员项目_{int(time.time())}",
            "code": f"PADM-{int(time.time())}",
            "status": "active",
        }, headers=headers)
        project_id = create_resp.json()["data"]["id"]

        member_headers = {"Authorization": f"Bearer {member_token}"}
        response = client.get(f"/api/v1/projects/{project_id}", headers=member_headers)
        assert response.status_code == 403


class TestProjectValidation:
    """项目参数校验测试"""

    def test_create_project_validation(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.post("/api/v1/projects/create", json={
            "priority": 3,
            "status": "draft",
        }, headers=headers)
        assert response.status_code == 422

        response = client.post("/api/v1/projects/create", json={
            "name": "测试项目",
            "status": "draft",
            "priority": 6,
        }, headers=headers)
        assert response.status_code == 422

        response = client.post("/api/v1/projects/create", json={
            "name": "测试项目",
            "status": "draft",
            "priority": 0,
        }, headers=headers)
        assert response.status_code == 422