"""Alembic environment: migrations run against the same DATABASE_URL the app uses."""

from alembic import context
from sqlalchemy import create_engine

from app.config import get_settings


def run_migrations_online() -> None:
    engine = create_engine(get_settings().sqlalchemy_url)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
