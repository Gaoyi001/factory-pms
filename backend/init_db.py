"""数据库初始化脚本 - 创建权限模块相关表"""
import sys
sys.path.insert(0, '.')

from app.core.database import engine, Base, SessionLocal
from app.models import (
    Role, Permission, OperationLog,
    User, Department,
    Project, ProjectType, Task, Requirement,
    Experiment, ExperimentRecord, ExperimentAttachment,
    Material, BomHeader, BomItem, BomChange,
    Sample, SampleInspection, SampleInspectionItem, TrialProduction,
    Document, DocumentVersion, DocumentApproval, DocCategory, KnowledgeArticle,
    Warehouse, InventoryItem, InventoryTransaction, InventoryApproval, InventoryAlert,
)
# 确保所有模型被注册（包括 __init__.py 未显式导出的）
import app.models  # noqa: F401

def init_db():
    """创建所有表"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成!")

def init_default_roles_and_permissions():
    """初始化默认角色和权限"""
    db = SessionLocal()
    try:
        # 检查是否已有角色
        if db.query(Role).count() > 0:
            print("角色已存在，跳过初始化")
            return
        
        # 创建默认角色
        default_roles = [
            {"code": "admin", "name": "管理员", "description": "系统管理员，拥有所有权限", "sort_order": 1},
            {"code": "manager", "name": "经理", "description": "部门经理，可管理项目和数据", "sort_order": 2},
            {"code": "member", "name": "成员", "description": "普通成员，可创建和编辑自己的数据", "sort_order": 3},
            {"code": "viewer", "name": "查看者", "description": "只读用户，只能查看数据", "sort_order": 4},
        ]
        
        roles = {}
        for role_data in default_roles:
            role = Role(**role_data)
            db.add(role)
            roles[role.code] = role
        
        db.commit()
        
        # 创建默认权限
        # 资源：与后端 require_permission 调用保持一致
        # project/experiment/bom/sample/document/user/department/role + material/warehouse/inventory/log
        resources = [
            "project", "experiment", "bom", "sample", "document",
            "user", "department", "role",
            "material", "warehouse", "inventory", "log",
        ]
        actions = ["create", "read", "update", "delete", "download"]

        all_perms = []
        for resource in resources:
            for action in actions:
                perm = Permission(
                    code=f"{resource}:{action}",
                    name=f"{resource}:{action}",
                    resource=resource,
                    action=action,
                    description=f"{resource} {action}",
                )
                db.add(perm)
                all_perms.append(perm)

        db.commit()

        # 给 admin 分配所有权限
        admin_role = roles.get("admin")
        if admin_role:
            admin_role.permissions = all_perms
            db.commit()

        # 给 manager 分配部分权限（排除角色管理的删除/创建、用户的删除）
        manager_role = roles.get("manager")
        if manager_role:
            manager_perms = [p for p in all_perms
                           if not (p.resource == "role" and p.action in ("delete", "create"))
                           and not (p.resource == "user" and p.action == "delete")]
            manager_role.permissions = manager_perms
            db.commit()

        # 给 member 分配基础权限：读所有模块 + 创建/部分更新
        member_role = roles.get("member")
        if member_role:
            member_perms = [p for p in all_perms
                          if p.action in ("read", "create", "download")
                          or (p.resource in ("project", "experiment") and p.action == "update")]
            member_role.permissions = member_perms
            db.commit()

        # 给 viewer 分配只读权限（含下载，下载属于只读延伸）
        viewer_role = roles.get("viewer")
        if viewer_role:
            viewer_perms = [p for p in all_perms if p.action in ("read", "download")]
            viewer_role.permissions = viewer_perms
            db.commit()
        
        print("默认角色和权限初始化完成")
        
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    init_default_roles_and_permissions()
    print("数据库初始化完成!")
