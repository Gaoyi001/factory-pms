# app/__init__.py
import logging
from app.core.database import Base, engine
from app.models import user, project, experiment, bom, sample, document

logger = logging.getLogger(__name__)

__all__ = ["Base", "engine"]


def create_tables():
    """创建所有数据库表（开发环境用，生产环境用 Alembic 迁移）"""
    Base.metadata.create_all(bind=engine)


def init_db():
    """初始化基础数据"""
    from sqlalchemy.orm import sessionmaker
    from app.core.database import engine
    from app.models.user import User, Department
    from app.core.security import get_password_hash

    Session = sessionmaker(bind=engine)
    db = Session()

    try:
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

        # 创建管理员账号
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(
                username="admin",
                email="admin@factory-pms.com",
                password_hash=get_password_hash("admin123"),
                real_name="系统管理员",
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()

        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
    finally:
        db.close()
