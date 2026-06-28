"""权限迁移脚本 - 为现有数据库补充缺失的权限资源并分配给对应角色

补充资源：material / warehouse / inventory / log（这些在 init_db.py 早期版本中缺失）
对已存在的权限不做任何改动，仅新增缺失项并按角色策略补分配。
"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.role import Role, Permission, role_permission_table


# 与 init_db.py 保持一致的资源/动作
ALL_RESOURCES = [
    "project", "experiment", "bom", "sample", "document",
    "user", "department", "role",
    "material", "warehouse", "inventory", "log",
]
ACTIONS = ["create", "read", "update", "delete", "download"]


def get_or_create_perm(db, resource: str, action: str) -> Permission:
    code = f"{resource}:{action}"
    perm = db.query(Permission).filter(Permission.code == code).first()
    if perm:
        return perm
    perm = Permission(
        code=code, name=code, resource=resource, action=action,
        description=f"{resource} {action}",
    )
    db.add(perm)
    db.flush()
    return perm


def role_has_perm(db, role: Role, perm: Permission) -> bool:
    row = db.execute(
        role_permission_table.select().where(
            (role_permission_table.c.role_id == role.id) &
            (role_permission_table.c.permission_id == perm.id)
        )
    ).first()
    return row is not None


def assign_if_missing(db, role: Role, perm: Permission) -> bool:
    if role_has_perm(db, role, perm):
        return False
    db.execute(role_permission_table.insert().values(role_id=role.id, permission_id=perm.id))
    return True


def migrate():
    db = SessionLocal()
    try:
        # 1. 补全所有权限定义
        all_perms = []
        for resource in ALL_RESOURCES:
            for action in ACTIONS:
                all_perms.append(get_or_create_perm(db, resource, action))
        db.commit()
        print(f"权限定义就绪：共 {len(all_perms)} 项")

        roles = {r.code: r for r in db.query(Role).all()}
        if not roles:
            print("未发现任何角色，请先运行 init_db.py")
            return

        added = 0

        # admin：拥有所有权限
        admin = roles.get("admin")
        if admin:
            for p in all_perms:
                added += 1 if assign_if_missing(db, admin, p) else 0

        # manager：除 role:create/delete、user:delete 外全部
        manager = roles.get("manager")
        if manager:
            for p in all_perms:
                if (p.resource == "role" and p.action in ("create", "delete")) \
                   or (p.resource == "user" and p.action == "delete"):
                    continue
                added += 1 if assign_if_missing(db, manager, p) else 0

        # member：读所有模块 + create + download + project/experiment 的 update
        member = roles.get("member")
        if member:
            for p in all_perms:
                if p.action in ("read", "create", "download") \
                   or (p.resource in ("project", "experiment") and p.action == "update"):
                    added += 1 if assign_if_missing(db, member, p) else 0

        # viewer：只读 + 下载
        viewer = roles.get("viewer")
        if viewer:
            for p in all_perms:
                if p.action in ("read", "download"):
                    added += 1 if assign_if_missing(db, viewer, p) else 0

        db.commit()
        print(f"迁移完成：新增权限分配 {added} 项")
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
