"""角色权限模块测试"""
import pytest
import time


class TestRoleCRUD:
    """角色增删改查测试"""

    def test_list_roles(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/roles/list", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    def test_get_role(self, client, admin_token, db):
        headers = {"Authorization": f"Bearer {admin_token}"}
        from app.models.role import Role
        role = db.query(Role).filter(Role.code == "admin").first()

        response = client.get(f"/api/v1/roles/{role.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["code"] == "admin"

    def test_create_role(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        code = f"test_role_{int(time.time())}"
        response = client.post("/api/v1/roles/create", json={
            "code": code,
            "name": "测试角色",
            "description": "这是一个测试角色",
            "is_active": True,
            "sort_order": 10,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_create_duplicate_role(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/roles/create", json={
            "code": "admin",
            "name": "重复角色",
        }, headers=headers)
        assert response.status_code == 400

    def test_update_role(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        code = f"updaterole_{int(time.time())}"
        create_resp = client.post("/api/v1/roles/create", json={
            "code": code,
            "name": "原始名称",
            "description": "原始描述",
            "is_active": True,
            "sort_order": 10,
        }, headers=headers)
        role_id = create_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/roles/{role_id}", json={
            "name": "更新后的名称",
            "description": "更新后的描述",
        }, headers=headers)
        assert response.status_code == 200

    def test_update_system_role(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.put("/api/v1/roles/1", json={
            "name": "超级管理员",
        }, headers=headers)
        assert response.status_code == 400

    def test_delete_role(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        code = f"deleterole_{int(time.time())}"
        create_resp = client.post("/api/v1/roles/create", json={
            "code": code,
            "name": "待删除角色",
            "is_active": True,
            "sort_order": 10,
        }, headers=headers)
        role_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/roles/{role_id}", headers=headers)
        assert response.status_code == 200

        response = client.get(f"/api/v1/roles/{role_id}", headers=headers)
        assert response.status_code == 404

    def test_delete_system_role(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.delete("/api/v1/roles/1", headers=headers)
        assert response.status_code == 400

    def test_delete_role_with_users(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        code = f"userrole_{int(time.time())}"
        create_resp = client.post("/api/v1/roles/create", json={
            "code": code,
            "name": "有用户角色",
            "is_active": True,
            "sort_order": 10,
        }, headers=headers)
        role_id = create_resp.json()["data"]["id"]

        username = f"roleuser_{int(time.time())}"
        client.post("/api/v1/users/create", json={
            "username": username,
            "password": "test123456",
            "email": f"{username}@test.com",
            "real_name": "角色用户",
            "role": code,
        }, headers=headers)

        response = client.delete(f"/api/v1/roles/{role_id}", headers=headers)
        assert response.status_code == 400


class TestPermissionManagement:
    """权限管理测试"""

    def test_list_permissions(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/roles/permissions/list", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0

    def test_create_permission(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/roles/permissions/create", json={
            "code": "test:custom",
            "name": "自定义权限",
            "resource": "test",
            "action": "custom",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_create_duplicate_permission(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/roles/permissions/create", json={
            "code": "project:create",
            "name": "重复权限",
            "resource": "project",
            "action": "create",
        }, headers=headers)
        assert response.status_code == 400


class TestPermissionAssignment:
    """权限分配测试"""

    def test_assign_permissions(self, client, admin_token, db):
        headers = {"Authorization": f"Bearer {admin_token}"}
        code = f"assignrole_{int(time.time())}"
        create_resp = client.post("/api/v1/roles/create", json={
            "code": code,
            "name": "权限分配测试角色",
            "is_active": True,
            "sort_order": 10,
        }, headers=headers)
        role_id = create_resp.json()["data"]["id"]

        perms_resp = client.get("/api/v1/roles/permissions/list", headers=headers)
        perm_ids = [p["id"] for p in perms_resp.json()["data"][:3]]

        response = client.post(f"/api/v1/roles/{role_id}/permissions", json=perm_ids, headers=headers)
        assert response.status_code == 200

        get_resp = client.get(f"/api/v1/roles/{role_id}", headers=headers)
        data = get_resp.json()["data"]
        assert len(data["permissions"]) == 3

    def test_assign_permissions_to_nonexistent_role(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/roles/99999/permissions", json=[1, 2, 3], headers=headers)
        assert response.status_code == 404


class TestRoleValidation:
    """角色参数校验测试"""

    def test_create_role_validation(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.post("/api/v1/roles/create", json={
            "name": "测试角色",
        }, headers=headers)
        assert response.status_code == 422

        response = client.post("/api/v1/roles/create", json={
            "code": "a",
            "name": "短编码角色",
        }, headers=headers)
        assert response.status_code == 422

        response = client.post("/api/v1/roles/create", json={
            "code": "test_role_code_that_is_way_too_long_exceeds_thirty_two_characters",
            "name": "长编码角色",
        }, headers=headers)
        assert response.status_code == 422


class TestRoleAccessControl:
    """角色访问控制测试"""

    def test_roles_requires_admin(self, client, member_token):
        headers = {"Authorization": f"Bearer {member_token}"}
        response = client.get("/api/v1/roles/list", headers=headers)
        assert response.status_code == 403

    def test_permissions_requires_admin(self, client, member_token):
        headers = {"Authorization": f"Bearer {member_token}"}
        response = client.get("/api/v1/roles/permissions/list", headers=headers)
        assert response.status_code == 403