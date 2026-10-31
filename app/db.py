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
        # No pre-ping: it costs a database round trip on every request. Recycling connections before
        # the host's idle timeout keeps them alive instead.
        pool_recycle=240,
    )
