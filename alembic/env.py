import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Loyiha papkasini sys.path ga qo'shamiz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.models import Base

# Alembic Config obyekti
config = context.config

# Logging sozlamalari
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata - barcha jadvallarni tanib olish uchun
target_metadata = Base.metadata

# Database URL ni settings dan olamiz (environment orqali)
db_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Offline rejimda migratsiyalarni ishga tushirish."""
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
    """Online rejimda migratsiyalarni ishga tushirish."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
