"""认证模块测试"""
import pytest


class TestAuthLogin:
    """登录功能测试"""

    def test_login_success(self, client, admin_user):
        response = client.post("/api/v1/auth/login", json={
            "username": "test_admin",
            "password": "test123456"
        })
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "access_token" in data["data"]
        assert data["data"]["access_token"]

    def test_login_wrong_password(self, client):
        response = client.post("/api/v1/auth/login", json={
            "username": "test_admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent_user_xyz",
            "password": "anypass"
        })
        assert response.status_code == 401

    def test_login_empty_body(self, client):
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422

    def test_login_missing_username(self, client):
        response = client.post("/api/v1/auth/login", json={"password": "test123456"})
        assert response.status_code == 422

    def test_login_missing_password(self, client):
        response = client.post("/api/v1/auth/login", json={"username": "test_admin"})
        assert response.status_code == 422

    def test_login_disabled_user(self, client, db):
        from app.models.user import User
        from app.core.security import get_password_hash
        user = User(
            username="disabled_user",
            email="disabled@test.com",
            password_hash=get_password_hash("test123456"),
            real_name="已禁用用户",
            role="member",
            is_active=False,
        )
        db.add(user)
        db.commit()

        response = client.post("/api/v1/auth/login", json={
            "username": "disabled_user",
            "password": "test123456"
        })
        assert response.status_code == 403


class TestAuthMe:
    """获取当前用户信息测试"""

    def test_get_me_with_token(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["username"] == "test_admin"
        assert data["data"]["role"] == "admin"

    def test_get_me_without_token(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestAuthLogout:
    """登出功能测试"""

    def test_logout_clears_cookie(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200
        assert response.cookies.get("access_token") is None


class TestAuthRegister:
    """注册功能测试"""

    def test_register_as_admin(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/auth/register", json={
            "username": "new_user",
            "password": "test123456",
            "email": "new@test.com",
            "real_name": "新用户",
            "role": "member",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "user_id" in data["data"]

    def test_register_duplicate_username(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/auth/register", json={
            "username": "test_admin",
            "password": "test123456",
            "email": "another@test.com",
            "real_name": "重复用户",
            "role": "member",
        }, headers=headers)
        assert response.status_code == 400

    def test_register_without_admin(self, client, member_token):
        headers = {"Authorization": f"Bearer {member_token}"}
        response = client.post("/api/v1/auth/register", json={
            "username": "unauth_user",
            "password": "test123456",
            "email": "unauth@test.com",
            "real_name": "无权限用户",
            "role": "member",
        }, headers=headers)
        assert response.status_code == 403


class TestAuthPermissions:
    """权限获取测试"""

    def test_get_permissions_admin(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/auth/me/permissions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_admin"] is True
        assert len(data["data"]["permissions"]) > 0

    def test_get_permissions_member(self, client, member_token):
        headers = {"Authorization": f"Bearer {member_token}"}
        response = client.get("/api/v1/auth/me/permissions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_admin"] is False


class TestAuthRateLimit:
    """登录限流测试"""

    def test_login_rate_limit(self, client):
        for _ in range(10):
            response = client.post("/api/v1/auth/login", json={
                "username": "test_admin",
                "password": "wrongpassword"
            })
        response = client.post("/api/v1/auth/login", json={
            "username": "test_admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 429