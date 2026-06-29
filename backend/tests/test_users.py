"""用户管理模块测试"""
import pytest
import time


class TestUserCRUD:
    """用户增删改查测试"""

    def test_list_users(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/list", params={"page": 1, "page_size": 20}, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_simple_list(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/simple-list", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)

    def test_create_user(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        username = f"testuser_{int(time.time())}"
        response = client.post("/api/v1/users/create", json={
            "username": username,
            "password": "test123456",
            "email": f"{username}@test.com",
            "real_name": "API测试用户",
            "role": "member",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_create_duplicate_user(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/users/create", json={
            "username": "test_admin",
            "password": "test123456",
            "email": "duplicate@test.com",
            "real_name": "重复用户",
            "role": "member",
        }, headers=headers)
        assert response.status_code == 400

    def test_update_user(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        username = f"updateuser_{int(time.time())}"
        create_resp = client.post("/api/v1/users/create", json={
            "username": username,
            "password": "test123456",
            "email": f"{username}@test.com",
            "real_name": "原始名称",
            "role": "member",
        }, headers=headers)
        user_id = create_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/users/{user_id}", json={
            "real_name": "更新后的名称",
            "role": "viewer",
        }, headers=headers)
        assert response.status_code == 200

    def test_update_user_without_permission(self, client, member_token, db):
        from app.models.user import User
        headers = {"Authorization": f"Bearer {member_token}"}
        user = db.query(User).filter(User.username == "test_member").first()

        response = client.put(f"/api/v1/users/{user.id}", json={
            "real_name": "尝试修改自己",
        }, headers=headers)
        assert response.status_code == 200

    def test_update_other_user_as_member(self, client, member_token, db, admin_token):
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        username = f"targetuser_{int(time.time())}"
        create_resp = client.post("/api/v1/users/create", json={
            "username": username,
            "password": "test123456",
            "email": f"{username}@test.com",
            "real_name": "目标用户",
            "role": "member",
        }, headers=admin_headers)
        target_id = create_resp.json()["data"]["id"]

        member_headers = {"Authorization": f"Bearer {member_token}"}
        response = client.put(f"/api/v1/users/{target_id}", json={
            "real_name": "尝试修改他人",
        }, headers=member_headers)
        assert response.status_code == 403

    def test_delete_user(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        username = f"deleteuser_{int(time.time())}"
        create_resp = client.post("/api/v1/users/create", json={
            "username": username,
            "password": "test123456",
            "email": f"{username}@test.com",
            "real_name": "待删除用户",
            "role": "member",
        }, headers=headers)
        user_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/users/{user_id}", headers=headers)
        assert response.status_code == 200

        response = client.get(f"/api/v1/users/list", params={"keyword": username}, headers=headers)
        data = response.json()["data"]
        found = any(u["username"] == username and u["is_active"] for u in data["items"])
        assert not found


class TestUserPassword:
    """密码修改测试"""

    def test_change_password_by_admin(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        username = f"pwduser_{int(time.time())}"
        create_resp = client.post("/api/v1/users/create", json={
            "username": username,
            "password": "oldpassword",
            "email": f"{username}@test.com",
            "real_name": "密码测试用户",
            "role": "member",
        }, headers=headers)
        user_id = create_resp.json()["data"]["id"]

        response = client.post("/api/v1/users/change-password", json={
            "user_id": user_id,
            "new_password": "newpassword123",
        }, headers=headers)
        assert response.status_code == 200

    def test_change_own_password(self, client, member_token):
        headers = {"Authorization": f"Bearer {member_token}"}
        response = client.post("/api/v1/users/change-password", json={
            "old_password": "test123456",
            "new_password": "newpassword123",
        }, headers=headers)
        assert response.status_code == 200

    def test_change_password_wrong_old(self, client, member_token):
        headers = {"Authorization": f"Bearer {member_token}"}
        response = client.post("/api/v1/users/change-password", json={
            "old_password": "wrongpassword",
            "new_password": "newpassword123",
        }, headers=headers)
        assert response.status_code == 400


class TestUserBatch:
    """批量操作测试"""

    def test_batch_enable(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_ids = []
        for i in range(2):
            username = f"batchuser_{int(time.time())}_{i}"
            create_resp = client.post("/api/v1/users/create", json={
                "username": username,
                "password": "test123456",
                "email": f"{username}@test.com",
                "real_name": f"批量用户{i}",
                "role": "member",
                "is_active": False,
            }, headers=headers)
            user_ids.append(create_resp.json()["data"]["id"])

        response = client.post("/api/v1/users/batch-enable", json=user_ids, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["updated"] == 2

    def test_batch_disable(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_ids = []
        for i in range(2):
            username = f"batchuser_{int(time.time())}_{i}"
            create_resp = client.post("/api/v1/users/create", json={
                "username": username,
                "password": "test123456",
                "email": f"{username}@test.com",
                "real_name": f"批量用户{i}",
                "role": "member",
                "is_active": True,
            }, headers=headers)
            user_ids.append(create_resp.json()["data"]["id"])

        response = client.post("/api/v1/users/batch-disable", json=user_ids, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["updated"] == 2

    def test_batch_disable_self(self, client, admin_token, db):
        headers = {"Authorization": f"Bearer {admin_token}"}
        from app.models.user import User
        admin = db.query(User).filter(User.username == "test_admin").first()

        response = client.post("/api/v1/users/batch-disable", json=[admin.id], headers=headers)
        assert response.status_code == 400


class TestUserValidation:
    """用户参数校验测试"""

    def test_create_user_validation(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.post("/api/v1/users/create", json={
            "password": "test123456",
            "email": "test@x.com",
        }, headers=headers)
        assert response.status_code == 422

        response = client.post("/api/v1/users/create", json={
            "username": "ab",
            "password": "test123456",
            "email": "t@x.com",
        }, headers=headers)
        assert response.status_code == 422

        response = client.post("/api/v1/users/create", json={
            "username": "validuser",
            "password": "12345",
            "email": "t@x.com",
        }, headers=headers)
        assert response.status_code == 422

        response = client.post("/api/v1/users/create", json={
            "username": "validuser",
            "password": "test123456",
            "email": "not-an-email",
        }, headers=headers)
        assert response.status_code == 422