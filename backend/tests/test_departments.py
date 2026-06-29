"""部门管理模块测试"""
import pytest
import time


class TestDepartmentCRUD:
    """部门增删改查测试"""

    def test_list_departments(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/departments/list", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    def test_tree_departments(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/departments/tree", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    def test_create_department(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        name = f"测试部门_{int(time.time())}"
        response = client.post("/api/v1/departments/create", json={
            "name": name,
            "parent_id": None,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_create_department_with_parent(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        name = f"父部门_{int(time.time())}"
        create_resp = client.post("/api/v1/departments/create", json={
            "name": name,
            "parent_id": None,
        }, headers=headers)
        parent_id = create_resp.json()["data"]["id"]

        response = client.post("/api/v1/departments/create", json={
            "name": f"子部门_{int(time.time())}",
            "parent_id": parent_id,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_create_duplicate_department(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        name = f"重复部门_{int(time.time())}"
        client.post("/api/v1/departments/create", json={
            "name": name,
            "parent_id": None,
        }, headers=headers)

        response = client.post("/api/v1/departments/create", json={
            "name": name,
            "parent_id": None,
        }, headers=headers)
        assert response.status_code == 400

    def test_get_department(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        name = f"查询部门_{int(time.time())}"
        create_resp = client.post("/api/v1/departments/create", json={
            "name": name,
            "parent_id": None,
        }, headers=headers)
        dept_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/departments/{dept_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == dept_id

    def test_update_department(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        name = f"更新部门_{int(time.time())}"
        create_resp = client.post("/api/v1/departments/create", json={
            "name": name,
            "parent_id": None,
        }, headers=headers)
        dept_id = create_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/departments/{dept_id}", json={
            "name": f"更新后的名称_{int(time.time())}",
        }, headers=headers)
        assert response.status_code == 200

        response = client.get(f"/api/v1/departments/{dept_id}", headers=headers)
        assert response.status_code == 200

    def test_delete_department(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        name = f"删除部门_{int(time.time())}"
        create_resp = client.post("/api/v1/departments/create", json={
            "name": name,
            "parent_id": None,
        }, headers=headers)
        dept_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/departments/{dept_id}", headers=headers)
        assert response.status_code == 200

        response = client.get(f"/api/v1/departments/{dept_id}", headers=headers)
        assert response.status_code == 404

    def test_delete_department_with_children(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        name = f"父部门_{int(time.time())}"
        create_resp = client.post("/api/v1/departments/create", json={
            "name": name,
            "parent_id": None,
        }, headers=headers)
        parent_id = create_resp.json()["data"]["id"]

        client.post("/api/v1/departments/create", json={
            "name": f"子部门_{int(time.time())}",
            "parent_id": parent_id,
        }, headers=headers)

        response = client.delete(f"/api/v1/departments/{parent_id}", headers=headers)
        assert response.status_code == 400

    def test_delete_department_with_users(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        name = f"部门用户_{int(time.time())}"
        create_resp = client.post("/api/v1/departments/create", json={
            "name": name,
            "parent_id": None,
        }, headers=headers)
        dept_id = create_resp.json()["data"]["id"]

        username = f"deptuser_{int(time.time())}"
        client.post("/api/v1/users/create", json={
            "username": username,
            "password": "test123456",
            "email": f"{username}@test.com",
            "real_name": "部门用户",
            "role": "member",
            "dept_id": dept_id,
        }, headers=headers)

        response = client.delete(f"/api/v1/departments/{dept_id}", headers=headers)
        assert response.status_code == 400


class TestDepartmentValidation:
    """部门参数校验测试"""

    def test_create_department_validation(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.post("/api/v1/departments/create", json={
            "parent_id": None,
        }, headers=headers)
        assert response.status_code == 422

        response = client.post("/api/v1/departments/create", json={
            "name": "a",
            "parent_id": None,
        }, headers=headers)
        assert response.status_code == 422

        response = client.post("/api/v1/departments/create", json={
            "name": "x" * 101,
            "parent_id": None,
        }, headers=headers)
        assert response.status_code == 422

    def test_get_nonexistent_department(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/departments/9999999", headers=headers)
        assert response.status_code == 404


class TestDepartmentAccessControl:
    """部门访问控制测试"""

    def test_departments_require_auth(self, client):
        response = client.get("/api/v1/departments/list")
        assert response.status_code == 401

    def test_create_department_requires_admin(self, client, member_token):
        headers = {"Authorization": f"Bearer {member_token}"}
        response = client.post("/api/v1/departments/create", json={
            "name": "测试部门",
            "parent_id": None,
        }, headers=headers)
        assert response.status_code == 403