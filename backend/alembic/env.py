from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.infra.models import Base  # garante import dos models (e metadata com tables)
from app.infra.settings import database_url  # monta URL via env vars do docker-compose

# Alembic Config object (alembic.ini)
config = context.config

# Setup logging from alembic.ini (optional, but standard)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata used by autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Offline mode uses just a URL (no Engine). The SQL is emitted to the script output.
    """
    url = database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # ajuda a detectar mudanças de tipo
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Online mode creates an Engine and uses a DB connection.
    """
    # injeta a URL dinamicamente no config (evita hardcode no alembic.ini)
    config.set_main_option("sqlalchemy.url", database_url())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # idem offline
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
