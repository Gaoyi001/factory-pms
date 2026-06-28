"""Alembic migration environment config"""

from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.database import Base
from app.core.config import settings

import app.models.user       # noqa: F401
import app.models.role       # noqa: F401
import app.models.project    # noqa: F401
import app.models.experiment # noqa: F401
import app.models.bom        # noqa: F401
import app.models.sample     # noqa: F401
import app.models.document   # noqa: F401
import app.models.operation_log  # noqa: F401
import app.models.inventory  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DATABASE_URL = settings.get_database_url()
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=DATABASE_URL,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
