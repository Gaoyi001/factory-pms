"""后端启动/初始化脚本

数据库初始化流程:
  1. python run.py              # 自动建表（开发环境）+ 种子数据
  2. python run.py init         # 仅建表 + 种子数据
  3. python run.py reset        # 删除所有表 + 重新建表 + 种子数据
  4. python run.py seed         # 仅插入种子数据（表已存在）
  5. python run.py migrate      # 运行 Alembic 迁移（生产环境推荐）

生产环境部署:
  DB_AUTO_CREATE=false
  alembic upgrade head          # 先执行迁移
  python run.py seed            # 再插入种子数据
"""

import sys
import os
import secrets

# 将 app 目录加入路径
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine, Base, SessionLocal
from app.models import User, Department
from app.models.role import Role, Permission
from app.core.security import get_password_hash
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# 确保所有模型都被注册到 Base.metadata
import app.models  # noqa: F401

# 管理员默认密码 — 首次启动通过环境变量 ADMIN_PASSWORD 设置，否则生成随机密码
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")


# 预定义的角色和权限
DEFAULT_PERMISSIONS = [
    {"code": "project:create", "name": "创建项目", "resource": "project", "action": "create"},
    {"code": "project:read", "name": "查看项目", "resource": "project", "action": "read"},
    {"code": "project:update", "name": "更新项目", "resource": "project", "action": "update"},
    {"code": "project:delete", "name": "删除项目", "resource": "project", "action": "delete"},
    {"code": "material:create", "name": "创建物料", "resource": "material", "action": "create"},
    {"code": "material:read", "name": "查看物料", "resource": "material", "action": "read"},
    {"code": "material:update", "name": "更新物料", "resource": "material", "action": "update"},
    {"code": "material:delete", "name": "删除物料", "resource": "material", "action": "delete"},
    {"code": "bom:create", "name": "创建BOM", "resource": "bom", "action": "create"},
    {"code": "bom:read", "name": "查看BOM", "resource": "bom", "action": "read"},
    {"code": "bom:update", "name": "更新BOM", "resource": "bom", "action": "update"},
    {"code": "bom:delete", "name": "删除BOM", "resource": "bom", "action": "delete"},
    {"code": "sample:create", "name": "创建样品", "resource": "sample", "action": "create"},
    {"code": "sample:read", "name": "查看样品", "resource": "sample", "action": "read"},
    {"code": "sample:update", "name": "更新样品", "resource": "sample", "action": "update"},
    {"code": "sample:delete", "name": "删除样品", "resource": "sample", "action": "delete"},
    {"code": "document:create", "name": "创建文档", "resource": "document", "action": "create"},
    {"code": "document:read", "name": "查看文档", "resource": "document", "action": "read"},
    {"code": "document:update", "name": "更新文档", "resource": "document", "action": "update"},
    {"code": "document:delete", "name": "删除文档", "resource": "document", "action": "delete"},
    {"code": "document:upload", "name": "上传文件", "resource": "document", "action": "upload"},
    {"code": "document:download", "name": "下载文件", "resource": "document", "action": "download"},
    {"code": "experiment:create", "name": "创建实验", "resource": "experiment", "action": "create"},
    {"code": "experiment:read", "name": "查看实验", "resource": "experiment", "action": "read"},
    {"code": "experiment:update", "name": "更新实验", "resource": "experiment", "action": "update"},
    {"code": "experiment:delete", "name": "删除实验", "resource": "experiment", "action": "delete"},
    {"code": "user:create", "name": "创建用户", "resource": "user", "action": "create"},
    {"code": "user:read", "name": "查看用户", "resource": "user", "action": "read"},
    {"code": "user:update", "name": "更新用户", "resource": "user", "action": "update"},
    {"code": "user:delete", "name": "删除用户", "resource": "user", "action": "delete"},
    {"code": "log:read", "name": "查看日志", "resource": "log", "action": "read"},
    {"code": "log:delete", "name": "删除日志", "resource": "log", "action": "delete"},
    {"code": "inventory:create", "name": "入库", "resource": "inventory", "action": "create"},
    {"code": "inventory:read", "name": "查看库存", "resource": "inventory", "action": "read"},
    {"code": "inventory:update", "name": "出库/调拨/盘点", "resource": "inventory", "action": "update"},
    {"code": "inventory:delete", "name": "删除库存", "resource": "inventory", "action": "delete"},
    {"code": "inventory:approve", "name": "审批", "resource": "inventory", "action": "approve"},
    {"code": "warehouse:create", "name": "创建仓库", "resource": "warehouse", "action": "create"},
    {"code": "warehouse:read", "name": "查看仓库", "resource": "warehouse", "action": "read"},
    {"code": "warehouse:update", "name": "更新仓库", "resource": "warehouse", "action": "update"},
    {"code": "warehouse:delete", "name": "删除仓库", "resource": "warehouse", "action": "delete"},
]

# 角色权限分配
ROLE_PERMISSIONS_MAP = {
    "admin": ["*"],  # 所有权限
    "manager": [
        "project:read", "project:create", "project:update",
        "material:read", "material:create", "material:update",
        "bom:read", "bom:create", "bom:update", "bom:delete",
        "sample:read", "sample:create", "sample:update", "sample:delete",
        "document:read", "document:create", "document:update", "document:delete",
        "document:upload", "document:download",
        "experiment:read", "experiment:create", "experiment:update", "experiment:delete",
        "inventory:create", "inventory:read", "inventory:update", "inventory:delete", "inventory:approve",
        "warehouse:create", "warehouse:read", "warehouse:update", "warehouse:delete",
        "user:read",
        "log:read",
    ],
    "member": [
        "project:read",
        "material:read",
        "bom:read", "bom:create",
        "sample:read", "sample:create",
        "document:read", "document:create", "document:upload", "document:download",
        "experiment:read", "experiment:create",
        "inventory:read", "inventory:create",
        "warehouse:read", "warehouse:create",
        "user:read",
        "log:read",
    ],
    "viewer": [
        "project:read",
        "material:read",
        "bom:read",
        "sample:read",
        "document:read", "document:download",
        "experiment:read",
        "inventory:read",
        "warehouse:read",
        "user:read",
        "log:read",
    ],
}


def seed_roles_and_permissions(db):
    """初始化角色和权限"""
    # 创建权限
    if not db.query(Permission).first():
        for perm in DEFAULT_PERMISSIONS:
            db.add(Permission(**perm))
        db.commit()
        print("  Permissions seeded")

    # 创建角色
    roles_cache = {}
    existing_roles = db.query(Role).all()
    role_names = {
        "admin": "系统管理员",
        "manager": "主管",
        "member": "普通成员",
        "viewer": "只读用户",
    }

    for code, name in role_names.items():
        role = db.query(Role).filter(Role.code == code).first()
        if not role:
            role = Role(code=code, name=name, description=f"{name}角色", sort_order=list(role_names.keys()).index(code) + 1)
            db.add(role)
            db.flush()
        roles_cache[code] = role

    db.commit()

    # 分配权限（仅当角色没有任何权限时才分配默认权限，避免覆盖用户在前端的修改）
    for role_code, perm_codes in ROLE_PERMISSIONS_MAP.items():
        role = roles_cache[role_code]

        # 如果角色已经有权限，跳过（用户可能已经在前端修改过权限分配）
        if role.permissions:
            continue

        all_perms = {p.code: p for p in db.query(Permission).all()}

        for perm_code in perm_codes:
            if perm_code == "*":
                for p in all_perms.values():
                    role.permissions.append(p)
            else:
                p = all_perms.get(perm_code)
                if p:
                    role.permissions.append(p)

    db.commit()
    print("  Roles & Permissions seeded")


def init_db():
    """创建表 + 初始化基础数据"""
    print("[init] Creating database tables...")
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 迁移：为 documents 表添加 source_module 字段（兼容旧数据库）
        # 注意：新项目建议使用 alembic upgrade head 代替此临时迁移
        try:
            db.execute(text("ALTER TABLE documents ADD COLUMN source_module VARCHAR(32) DEFAULT 'document'"))
            db.commit()
            print("[MIGRATE] Added source_module column to documents")
        except Exception:
            db.rollback()

        # 迁移：为 inventory_items 表添加 version 字段（乐观锁）
        try:
            db.execute(text("ALTER TABLE inventory_items ADD COLUMN version INTEGER DEFAULT 0 NOT NULL"))
            db.commit()
            print("[MIGRATE] Added version column to inventory_items")
        except Exception:
            db.rollback()

        _seed_core_data(db)

        print("\n[OK] Initialization complete!")
        print("   Start:  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("   API docs:  http://localhost:8000/api/v1/docs")

    except Exception as e:
        print(f"[ERROR] Init failed: {e}")
        db.rollback()
    finally:
        db.close()


def seed_data():
    """仅插入种子数据（表已存在）"""
    print("[seed] Inserting seed data...")
    db = SessionLocal()

    try:
        _seed_core_data(db)
        print("[OK] Seed data insert complete!")
    except Exception as e:
        print(f"[ERROR] Seed failed: {e}")
        db.rollback()
    finally:
        db.close()


def _seed_core_data(db):
    """核心种子数据：部门、角色、权限、管理员账号"""
    # 创建默认部门
    if not db.query(Department).first():
        depts = [
            Department(name="管理层"),
            Department(name="研发部"),
            Department(name="工艺部"),
            Department(name="质量部"),
            Department(name="生产部"),
        ]
        db.add_all(depts)
        db.commit()
        print("[OK] Default departments created")

    # 初始化角色和权限
    seed_roles_and_permissions(db)

    # 创建管理员账号
    if not db.query(User).filter(User.username == "admin").first():
        admin_pwd = DEFAULT_ADMIN_PASSWORD or secrets.token_urlsafe(12)
        admin = User(
            username="admin",
            email="admin@factory-pms.com",
            password_hash=get_password_hash(admin_pwd),
            real_name="系统管理员",
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        if DEFAULT_ADMIN_PASSWORD:
            print(f"[OK] Admin account created (admin / {admin_pwd})")
        else:
            print(f"[OK] Admin account created. Generated password: {admin_pwd}")
            print(f"[WARN] 请立即修改默认密码！首次登录后可在个人设置中修改。")
    else:
        print("[INFO] Admin account already exists")


def drop_all():
    """危险：删除所有表"""
    confirm = input("确认删除所有数据表？(yes/no): ")
    if confirm == "yes":
        Base.metadata.drop_all(bind=engine)
        print("[OK] All tables dropped")
    else:
        print("Cancelled")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "reset":
            drop_all()
            init_db()
        elif action == "init":
            init_db()
        elif action == "seed":
            seed_data()
        elif action == "migrate":
            print("Running Alembic migrations...")
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=os.path.dirname(__file__),
            )
            if result.returncode == 0:
                print("Migration completed. Run 'python run.py seed' to insert seed data.")
            else:
                print(f"Migration failed with exit code {result.returncode}")
        else:
            print(f"Unknown action: {action}")
            print("Available actions: init, reset, seed, migrate")
    else:
        init_db()
