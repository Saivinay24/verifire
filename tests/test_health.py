from fastapi.testclient import TestClient

from app.domain.areas import AREAS, AREAS_BY_PINCODE
from app.main import app

client = TestClient(app)


def test_health_matches_contract() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_appendix_b_has_25_unique_areas() -> None:
    assert len(AREAS) == 25
    assert len(AREAS_BY_PINCODE) == 25
