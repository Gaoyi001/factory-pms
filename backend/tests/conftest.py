import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import get_password_hash
from app.core.rate_limit import login_rate_limiter

settings.DEBUG = True
settings.SECRET_KEY = "test-secret-key-32-chars-minimum-for-jwt"
settings.DATABASE_URL = "sqlite:///./test_fixture.db"

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.core.database import Base
from app.models.user import User, Department
from app.models.role import Role, Permission, role_permission_table
from app.models.bom import Material
from app.models.inventory import Warehouse
from app.main import app
from app.core.database import get_db


@pytest.fixture(scope="session")
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(setup_database):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db):
    login_rate_limiter._store.clear()
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db):
    dept = db.query(Department).filter(Department.name == "测试部门").first()
    if not dept:
        dept = Department(name="测试部门")
        db.add(dept)
        db.commit()
        db.refresh(dept)

    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if not admin_role:
        admin_role = Role(code="admin", name="系统管理员", description="管理员", sort_order=1, is_active=True)
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)

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

    for resource, action in perms_data:
        perm = db.query(Permission).filter(Permission.code == f"{resource}:{action}").first()
        if perm:
            existing = db.query(role_permission_table).filter(
                role_permission_table.c.role_id == admin_role.id,
                role_permission_table.c.permission_id == perm.id
            ).first()
            if not existing:
                db.execute(role_permission_table.insert().values(role_id=admin_role.id, permission_id=perm.id))
    db.commit()

    user = db.query(User).filter(User.username == "test_admin").first()
    if not user:
        user = User(
            username="test_admin",
            email="admin@test.com",
            password_hash=get_password_hash("test123456"),
            real_name="测试管理员",
            role="admin",
            dept_id=dept.id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_token(client, admin_user):
    response = client.post("/api/v1/auth/login", json={
        "username": "test_admin",
        "password": "test123456"
    })
    data = response.json()
    return data.get("data", {}).get("access_token", "")


@pytest.fixture(scope="function")
def member_user(db):
    dept = db.query(Department).filter(Department.name == "测试部门").first()
    if not dept:
        dept = Department(name="测试部门")
        db.add(dept)
        db.commit()
        db.refresh(dept)

    member_role = db.query(Role).filter(Role.code == "member").first()
    if not member_role:
        member_role = Role(code="member", name="普通成员", description="普通成员", sort_order=2, is_active=True)
        db.add(member_role)
        db.commit()
        db.refresh(member_role)

    user = db.query(User).filter(User.username == "test_member").first()
    if not user:
        user = User(
            username="test_member",
            email="member@test.com",
            password_hash=get_password_hash("test123456"),
            real_name="测试成员",
            role="member",
            dept_id=dept.id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="function")
def member_token(client, member_user):
    response = client.post("/api/v1/auth/login", json={
        "username": "test_member",
        "password": "test123456"
    })
    data = response.json()
    return data.get("data", {}).get("access_token", "")


@pytest.fixture(scope="function")
def test_warehouse(db):
    wh = db.query(Warehouse).filter(Warehouse.code == "TEST-WH").first()
    if not wh:
        wh = Warehouse(code="TEST-WH", name="测试仓库", location="A区", description="测试用仓库", is_active=True)
        db.add(wh)
        db.commit()
        db.refresh(wh)
    return wh


@pytest.fixture(scope="function")
def test_material(db):
    mat = db.query(Material).filter(Material.code == "TEST-MAT").first()
    if not mat:
        mat = Material(code="TEST-MAT", name="测试物料", spec="标准规格", unit="pcs", material_type="原材料", status="active")
        db.add(mat)
        db.commit()
        db.refresh(mat)
    return mat
