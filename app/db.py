"""Database engine. One pooled engine per process; repositories borrow connections from it."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        get_settings().sqlalchemy_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # survive the host recycling idle connections
    )
