import pytest
import sys
import os

# Make sure app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app

# Override settings for testing
settings.DEBUG = True
settings.SECRET_KEY = "test-secret-key-for-testing-only-do-not-use-in-production"
settings.DATABASE_URL = "sqlite:///./test_factory_pms.db"

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前确保数据库表存在，测试后清理避免数据污染"""
    from app.core.database import engine, Base
    Base.metadata.create_all(bind=engine)
    yield
    # 测试后清理：drop_all 避免数据残留导致后续测试污染
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_token():
    """获取 admin 用户 token（先创建测试用户）"""
    from app.core.database import SessionLocal
    from app.core.security import get_password_hash
    from app.models.user import User
    from app.models.role import Role, Permission

    db = SessionLocal()
    try:
        # Ensure admin user exists
        admin = db.query(User).filter(User.username == "test_admin").first()
        if not admin:
            # Create admin role if needed
            role = db.query(Role).filter(Role.code == "admin").first()
            if not role:
                role = Role(code="admin", name="系统管理员", description="管理员角色", sort_order=1)
                db.add(role)
                db.commit()

            admin = User(
                username="test_admin",
                email="test@test.com",
                password_hash=get_password_hash("test123456"),
                real_name="测试管理员",
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        # Login to get token
        response = client.post("/api/v1/auth/login", json={
            "username": "test_admin",
            "password": "test123456"
        })
        data = response.json()
        return data.get("data", {}).get("access_token", "")
    finally:
        db.close()


class TestConfig:
    """测试配置类"""

    def test_secret_key_required(self):
        """验证 SECRET_KEY 不能为空"""
        assert settings.SECRET_KEY, "SECRET_KEY should not be empty"
        assert len(settings.SECRET_KEY) >= 32, "SECRET_KEY should be at least 32 chars"

    def test_debug_default_false(self):
        """验证 DEBUG 默认值为 False（不依赖 .env 文件）"""
        from app.core.config import Settings
        # 绕过 .env 文件读取，直接验证类定义中的默认值
        s = Settings(_env_file=None)
        assert s.DEBUG == False, f"DEBUG should default to False, got {s.DEBUG}"

    def test_access_token_expire_in_range(self):
        """验证 token 过期时间在合理范围内"""
        assert 5 <= settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 10080


class TestSecurity:
    """测试安全模块"""

    def test_password_hash(self):
        """测试密码哈希"""
        from app.core.security import get_password_hash, verify_password
        pwd = "test123456"
        hashed = get_password_hash(pwd)
        assert hashed != pwd
        assert verify_password(pwd, hashed)

    def test_password_hash_min_length(self):
        """测试密码最小长度限制"""
        from app.core.security import get_password_hash
        import pytest as pt
        with pt.raises(ValueError, match="密码长度至少6字符"):
            get_password_hash("12345")

    def test_create_access_token(self):
        """测试创建 JWT token"""
        from app.core.security import create_access_token
        import jwt as pyjwt
        token = create_access_token({"sub": "1", "role": "admin"})
        assert token
        payload = pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "1"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_token_expired(self):
        """测试过期 token"""
        from app.core.security import create_access_token
        from datetime import timedelta
        import jwt as pyjwt
        import time

        token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(pyjwt.ExpiredSignatureError):
            pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


class TestAuthAPI:
    """测试认证 API"""

    def test_login_no_credentials(self):
        """测试无凭据登录"""
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422  # Validation error

    def test_login_wrong_password(self):
        """测试错误密码"""
        response = client.post("/api/v1/auth/login", json={
            "username": "test_admin",
            "password": "wrongpassword"
        })
        assert response.status_code in (401, 400)

    def test_protected_route_no_token(self):
        """测试无 token 访问受保护路由"""
        response = client.get("/api/v1/projects/list")
        assert response.status_code == 401


class TestDepartmentsAPI:
    """测试部门 API"""

    def test_list_departments_requires_auth(self):
        """部门列表需要认证"""
        response = client.get("/api/v1/departments/list")
        assert response.status_code == 401


class TestInventoryLogic:
    """测试库存逻辑"""

    def test_transaction_number_generation(self):
        """测试交易单号生成"""
        from app.core.database import SessionLocal
        from app.core.config import settings as s

        # Use test database
        db = SessionLocal()
        from app.api.v1.inventory import _generate_tx_no
        tx_no = _generate_tx_no("inbound", db)
        assert tx_no.startswith("IN")
        assert len(tx_no) > 10
        db.close()

    def test_check_low_stock(self):
        """测试库存状态检查"""
        from app.models.inventory import InventoryItem
        from app.api.v1.inventory import _check_low_stock

        item = InventoryItem(quantity=0, safety_stock=10, status="normal")
        _check_low_stock(item)
        assert item.status == "out_of_stock"

        item2 = InventoryItem(quantity=5, safety_stock=10, status="normal")
        _check_low_stock(item2)
        assert item2.status == "low_stock"

        item3 = InventoryItem(quantity=20, safety_stock=10, status="normal")
        _check_low_stock(item3)
        assert item3.status == "normal"


class TestConfigValidation:
    """测试配置校验"""

    def test_cors_origins_not_wildcard_by_default(self):
        """CORS 不应默认允许所有来源（不依赖 .env 文件）"""
        from app.core.config import Settings
        s = Settings(_env_file=None)
        # 默认应为空列表（生产安全）
        assert s.CORS_ORIGINS == [], f"CORS_ORIGINS should be empty by default, got {s.CORS_ORIGINS}"

    def test_jwt_algorithm(self):
        """JWT 算法应为 HS256"""
        assert settings.ALGORITHM == "HS256"


class TestResponseFormat:
    """测试响应格式"""

    def test_login_response_format(self, admin_token):
        """测试登录响应包含 access_token"""
        assert admin_token, "Login should return access_token"

    def test_health_check(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
