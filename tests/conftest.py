from collections.abc import Iterator

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from app.db import get_engine
from app.main import app
from app.repos.tables import licence_state
from app.services import licence


def reset_licence() -> None:
    """Back to the shipped bootstrap licence, with a fresh clock high-water mark."""
    with get_engine().begin() as conn:
        conn.execute(sa.update(licence_state).values(licence=None, clock_high_water=None))
    licence._state.loaded_at = 0.0
    licence._state.high_water = None


@pytest.fixture
def client() -> Iterator[TestClient]:
    reset_licence()
    with TestClient(app) as c:
        assert c.post("/admin/reset").status_code == 200
        yield c
    reset_licence()
