"""应用配置"""
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field, field_validator
import secrets


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "Factory R&D PMS"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # 数据库 - 默认使用 SQLite（本地开发）
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "factory_pms"
    DATABASE_URL: Optional[str] = "sqlite:///./factory_pms.db"

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return "sqlite:///./factory_pms.db"

    # Redis - 可选组件，本地开发可不启用
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None

    def get_redis_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # JWT
    SECRET_KEY: str = ""  # 必须通过环境变量设置，不可使用默认值
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24, ge=5, le=10080)  # 5分钟~7天

    # 已知的弱占位符密钥黑名单（生产环境必须拒绝）
    _WEAK_SECRET_PLACEHOLDERS = {
        "change-this-in-production-use-random-key",
        "dev-secret-key-change-in-production",
        "secret",
        "changeme",
    }

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        # 留空：开发环境持久化生成，生产环境报错
        if not v:
            if cls.model_config.get("env_file") == ".env":
                # 开发环境：尝试从 .env 已持久化的值读取，避免每次重启 JWT 失效
                persisted = cls._read_persisted_dev_secret()
                if persisted and len(persisted) >= 32:
                    return persisted
                new_key = secrets.token_urlsafe(32)
                cls._persist_dev_secret(new_key)
                return new_key
            raise ValueError("SECRET_KEY 必须通过环境变量设置，不可使用默认值")

        # 拒绝已知弱占位符
        if v in cls._WEAK_SECRET_PLACEHOLDERS:
            raise ValueError(
                f"SECRET_KEY 不能使用占位符 '{v}'，请生成随机密钥："
                "python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )

        # 弱密钥告警：包含 change/dev/secret/example 等关键词
        v_lower = v.lower()
        if any(kw in v_lower for kw in ("change", "dev-secret", "example", "placeholder", "changeme")):
            if cls.model_config.get("env_file") != ".env":
                raise ValueError(
                    f"SECRET_KEY 包含弱密钥关键词，生产环境必须使用随机密钥：{v}"
                )

        if len(v) < 32:
            raise ValueError("SECRET_KEY 长度至少32字符")
        return v

    @staticmethod
    def _read_persisted_dev_secret() -> Optional[str]:
        """读取开发环境持久化的 SECRET_KEY（避免每次重启 JWT 失效）"""
        try:
            import os
            secret_file = os.path.join(os.getcwd(), ".dev_secret_key")
            if os.path.exists(secret_file):
                with open(secret_file, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception:
            pass
        return None

    @staticmethod
    def _persist_dev_secret(key: str) -> None:
        """持久化开发环境 SECRET_KEY（仅本地 .env 场景）"""
        try:
            import os
            secret_file = os.path.join(os.getcwd(), ".dev_secret_key")
            with open(secret_file, "w", encoding="utf-8") as f:
                f.write(key)
            # 设置仅当前用户可读写
            os.chmod(secret_file, 0o600)
        except Exception:
            pass

    # MinIO - 可选组件，本地开发使用本地文件存储
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "factory-pms"
    MINIO_SECURE: bool = False

    # CORS - 生产环境指定具体域名，开发环境可用 ["*"]
    CORS_ORIGINS: list[str] = []

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
