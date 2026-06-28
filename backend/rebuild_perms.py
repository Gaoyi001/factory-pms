"""重建权限相关表 - 用于修复表结构问题"""
import sys
sys.path.insert(0, '.')

from app.core.database import engine, Base, SessionLocal
from sqlalchemy import text

def rebuild_permission_tables():
    """删除旧的权限相关表，重新创建"""
    print("正在重建权限相关表...")
    
    with engine.connect() as conn:
        # 删除旧表（按依赖顺序）
        conn.execute(text("DROP TABLE IF EXISTS role_permissions"))
        conn.execute(text("DROP TABLE IF EXISTS permissions"))
        conn.execute(text("DROP TABLE IF EXISTS roles"))
        conn.execute(text("DROP TABLE IF EXISTS operation_logs"))
        conn.commit()
    
    print("旧表已删除")
    
    # 重新创建所有表
    Base.metadata.create_all(bind=engine)
    print("新表已创建")

if __name__ == "__main__":
    rebuild_permission_tables()
    print("权限表重建完成!")
