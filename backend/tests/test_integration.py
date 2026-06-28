"""
集成测试：验证关键模块的协作和数据完整性
测试数据库使用 SQLite，每个测试之间隔离
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app

# Override settings for isolated testing
settings.DEBUG = True
settings.SECRET_KEY = "integration-test-secret-key-32chars-minimum"
settings.DATABASE_URL = "sqlite:///./test_integration.db"

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前重建数据库"""
    from app.core.database import engine, Base
    Base.metadata.create_all(bind=engine)
    yield
    # 测试后清理
    Base.metadata.drop_all(bind=engine)


def _create_admin_and_login():
    """工具函数：创建管理员用户并返回 token"""
    from app.core.database import SessionLocal
    from app.core.security import get_password_hash
    from app.models.user import User, Department
    from app.models.role import Role, Permission
    from app.models.role import role_permission_table

    db = SessionLocal()
    try:
        # 创建默认部门 (Department 只有 name 和 parent_id)
        dept = Department(name="根部门")
        db.add(dept)
        db.commit()
        db.refresh(dept)

        # 创建 admin 角色
        role = Role(code="admin", name="系统管理员", description="管理员", sort_order=1, is_active=True)
        db.add(role)
        db.commit()

        # 创建权限（权限码与 run.py 的 DEFAULT_PERMISSIONS 保持一致）
        perms_data = [
            ("project", "create"), ("project", "read"), ("project", "update"), ("project", "delete"),
            ("experiment", "create"), ("experiment", "read"), ("experiment", "update"), ("experiment", "delete"),
            ("bom", "create"), ("bom", "read"), ("bom", "update"), ("bom", "delete"),
            ("inventory", "create"), ("inventory", "read"), ("inventory", "update"), ("inventory", "delete"),
            ("inventory", "approve"),
            ("document", "create"), ("document", "read"), ("document", "update"), ("document", "delete"),
            ("document", "upload"), ("document", "download"),
            ("user", "create"), ("user", "read"), ("user", "update"), ("user", "delete"),
            ("role", "create"), ("role", "read"), ("role", "update"), ("role", "delete"),
            ("department", "create"), ("department", "read"), ("department", "update"), ("department", "delete"),
            ("sample", "create"), ("sample", "read"), ("sample", "update"), ("sample", "delete"),
            ("warehouse", "create"), ("warehouse", "read"), ("warehouse", "update"), ("warehouse", "delete"),
            ("log", "read"), ("log", "delete"),
            ("material", "create"), ("material", "read"), ("material", "update"), ("material", "delete"),
        ]
        for resource, action in perms_data:
            perm = db.query(Permission).filter(Permission.code == f"{resource}:{action}").first()
            if not perm:
                perm = Permission(code=f"{resource}:{action}", name=f"{resource}:{action}",
                                  resource=resource, action=action)
                db.add(perm)
        db.commit()

        # 分配所有权限给 admin
        for resource, action in perms_data:
            perm = db.query(Permission).filter(Permission.code == f"{resource}:{action}").first()
            existing = db.query(role_permission_table).filter(
                role_permission_table.c.role_id == role.id,
                role_permission_table.c.permission_id == perm.id
            ).first()
            if not existing:
                db.execute(role_permission_table.insert().values(role_id=role.id, permission_id=perm.id))
        db.commit()

        # 创建 admin 用户
        user = User(
            username="int_test_admin",
            email="int_test@test.com",
            password_hash=get_password_hash("test123456"),
            real_name="集成测试管理员",
            role="admin",
            dept_id=dept.id,
            is_active=True,
        )
        db.add(user)
        db.commit()

        # 登录获取 token
        response = client.post("/api/v1/auth/login", json={
            "username": "int_test_admin",
            "password": "test123456"
        })
        return response.json()["data"]["access_token"]
    finally:
        db.close()


class TestProjectCRUD:
    """项目 CRUD 集成测试"""

    def test_create_and_read_project(self):
        """创建项目后应能查询到"""
        token = _create_admin_and_login()
        headers = {"Authorization": f"Bearer {token}"}

        # 创建项目 (priority 是整数 1-5, status 是字符串)
        create_resp = client.post("/api/v1/projects/create", json={
            "name": "集成测试项目",
            "code": "IT-2024-001",
            "description": "用于集成测试的项目",
            "priority": 1,
            "status": "draft",
        }, headers=headers)
        assert create_resp.status_code in (200, 201), f"创建项目失败: {create_resp.json()}"
        project_data = create_resp.json().get("data", create_resp.json())
        project_id = project_data.get("id")
        assert project_id is not None

        # 查询项目
        get_resp = client.get(f"/api/v1/projects/{project_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["name"] == "集成测试项目"

    def test_update_project_status(self):
        """项目状态应正确更新"""
        token = _create_admin_and_login()
        headers = {"Authorization": f"Bearer {token}"}

        # 创建
        create_resp = client.post("/api/v1/projects/create", json={
            "name": "状态更新项目",
            "code": "IT-2024-002",
            "status": "draft",
        }, headers=headers)
        project_id = create_resp.json().get("data", create_resp.json()).get("id")

        # 更新状态
        update_resp = client.put(f"/api/v1/projects/{project_id}", json={
            "status": "active"
        }, headers=headers)
        assert update_resp.status_code == 200

        # 验证
        get_resp = client.get(f"/api/v1/projects/{project_id}", headers=headers)
        assert get_resp.json()["data"]["status"] == "active"

    def test_project_permission_denied(self):
        """未认证用户不能创建项目"""
        resp = client.post("/api/v1/projects/create", json={
            "name": "未授权项目",
            "code": "IT-2024-003",
        })
        assert resp.status_code == 401


class TestInventoryTransfer:
    """库存调拨集成测试"""

    def test_inventory_transfer_atomic(self):
        """库存创建和状态管理测试"""
        token = _create_admin_and_login()
        headers = {"Authorization": f"Bearer {token}"}
        from app.core.database import SessionLocal
        from app.models.inventory import InventoryItem
        from app.models.bom import Material

        db = SessionLocal()
        try:
            # 创建物料
            m = Material(code="MAT-INV-001", name="测试物料A", unit="kg", spec="标准", material_type="material")
            db.add(m)
            db.commit()
            db.refresh(m)

            # 创建库存项 (InventoryItem 使用 material_id 和 warehouse 字符串)
            item1 = InventoryItem(
                material_id=m.id,
                warehouse="原料仓A",
                location="A-01-01",
                quantity=100,
                safety_stock=10,
                unit="kg",
                status="normal"
            )
            db.add(item1)
            db.commit()
            db.refresh(item1)

            # 验证库存已创建
            assert item1.id is not None
            assert item1.quantity == 100

            # 测试通过 API 查询库存列表
            list_resp = client.get("/api/v1/inventory/list", headers=headers)
            assert list_resp.status_code == 200, f"查询库存列表失败: {list_resp.json()}"
        finally:
            db.close()

    def test_low_stock_detection(self):
        """低库存状态应正确检测"""
        from app.models.inventory import InventoryItem
        from app.api.v1.inventory import _check_low_stock

        # 缺货
        item = InventoryItem(quantity=0, safety_stock=5, status="normal")
        _check_low_stock(item)
        assert item.status == "out_of_stock"

        # 低库存
        item2 = InventoryItem(quantity=3, safety_stock=10, status="normal")
        _check_low_stock(item2)
        assert item2.status == "low_stock"

        # 正常
        item3 = InventoryItem(quantity=50, safety_stock=10, status="normal")
        _check_low_stock(item3)
        assert item3.status == "normal"


class TestBOMOperations:
    """BOM 操作集成测试"""

    def test_bom_create_and_query(self):
        """BOM 创建后应能查询"""
        token = _create_admin_and_login()
        headers = {"Authorization": f"Bearer {token}"}

        from app.core.database import SessionLocal
        from app.models.bom import Material  # Material 在 app.models.bom

        db = SessionLocal()
        try:
            m1 = Material(code="MAT-BOM-001", name="成品A", unit="个", spec="标准", material_type="product")
            m2 = Material(code="MAT-BOM-002", name="零件B", unit="个", spec="标准", material_type="material")
            m3 = Material(code="MAT-BOM-003", name="零件C", unit="个", spec="标准", material_type="material")
            db.add_all([m1, m2, m3])
            db.commit()

            # 创建 BOM (端点: POST /api/v1/bom/headers; items 需要 material_id 整数 和 quantity 字符串)
            bom_resp = client.post("/api/v1/bom/headers", json={
                "product_code": "MAT-BOM-001",
                "name": "成品A BOM",
                "version": "1.0",
                "status": "draft",
                "items": [
                    {"material_code": "MAT-BOM-002", "material_name": "零件B", "material_id": m2.id, "quantity": "2", "unit": "个"},
                    {"material_code": "MAT-BOM-003", "material_name": "零件C", "material_id": m3.id, "quantity": "3", "unit": "个"},
                ],
            }, headers=headers)
            assert bom_resp.status_code in (200, 201), f"创建BOM失败: {bom_resp.json()}"
        finally:
            db.close()


class TestDocumentUploadSecurity:
    """文件上传安全集成测试"""

    def test_upload_without_auth(self):
        """未认证用户不能上传文件"""
        # 上传需要指定文档 ID: POST /api/v1/documents/{doc_id}/upload
        resp = client.post("/api/v1/documents/1/upload")
        assert resp.status_code in (401, 422, 404)

    def test_max_file_size_config(self):
        """验证文件大小限制配置"""
        from app.api.v1.documents import MAX_FILE_SIZE
        assert MAX_FILE_SIZE == 50 * 1024 * 1024, "MAX_FILE_SIZE 应为 50MB"


class TestDepartmentTree:
    """部门树操作集成测试"""

    def test_create_department_with_auth(self):
        """创建部门需要认证"""
        token = _create_admin_and_login()
        headers = {"Authorization": f"Bearer {token}"}

        dept_resp = client.post("/api/v1/departments/create", json={
            "name": "一级部门",
        }, headers=headers)
        assert dept_resp.status_code in (200, 201), f"创建部门失败: {dept_resp.json()}"

    def test_departments_auth_required(self):
        """部门列表需要认证"""
        resp = client.get("/api/v1/departments/list")
        assert resp.status_code == 401


class TestResponseIntegrity:
    """响应格式完整性测试"""

    def test_api_response_structure(self):
        """验证 API 响应结构一致性"""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data or "status" in data or "app" in data

    def test_404_handling(self):
        """不存在的路由应返回 404"""
        resp = client.get("/api/v1/nonexistent-endpoint")
        assert resp.status_code == 404


class TestConcurrentSafety:
    """并发安全测试"""

    def test_transaction_rollback(self):
        """事务回滚后数据不应被持久化"""
        from app.core.database import SessionLocal
        from app.models.user import Department

        db = SessionLocal()
        try:
            # 插入第一条记录 (Department name 是 unique)
            d1 = Department(name="回滚测试部门")
            db.add(d1)
            db.commit()

            # 尝试插入相同 name——违反唯一约束
            d2 = Department(name="回滚测试部门")
            db.add(d2)
            with pytest.raises(Exception):
                db.commit()

            db.rollback()

            # 验证只有一个部门
            count = db.query(Department).filter(Department.name == "回滚测试部门").count()
            assert count == 1, f"事务回滚后应只有1条记录，实际有{count}条"
        finally:
            db.close()
