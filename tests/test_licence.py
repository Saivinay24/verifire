"""The four-step licence demo from the brief, plus tampering and clock rollback.

Uses a throwaway test key so the real private key is never needed in CI.
"""

import base64
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from nacl.signing import SigningKey

from app.domain import licence as L
from app.services import licence as svc
from tests.conftest import reset_licence

TEST_KEY = SigningKey(bytes(range(32)))


def make(minutes: float, licensee: str = "Demo Bank", issued: datetime | None = None) -> dict[str, str]:
    now = (issued or datetime.now(UTC)).replace(microsecond=0)
    fields = {
        "licence_id": f"lic_test_{minutes}",
        "licensee": licensee,
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=minutes)).isoformat(),
    }
    sig = TEST_KEY.sign(L.canonical_payload(fields)).signature
    return {**fields, "signature": base64.b64encode(sig).decode()}


@pytest.fixture
def test_key(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(L, "PUBLIC_KEY_B64", base64.b64encode(bytes(TEST_KEY.verify_key)).decode())
    reset_licence()
    yield
    reset_licence()


def test_tampered_licence_rejected() -> None:
    doc = make(5)
    test_pub = base64.b64encode(bytes(TEST_KEY.verify_key)).decode()
    assert L.verify(doc, test_pub).licensee == "Demo Bank"
    for field, value in (("expires_at", "2099-01-01T00:00:00+05:30"), ("licensee", "Other Bank")):
        with pytest.raises(L.InvalidLicence):
            L.verify({**doc, field: value}, test_pub)
    with pytest.raises(L.InvalidLicence):
        L.verify({**doc, "signature": "not-base64!"}, test_pub)
    with pytest.raises(L.InvalidLicence):
        L.verify(doc)  # signed by a key the server does not trust


def test_status_rules() -> None:
    now = datetime.now(UTC)
    lic = L.verify(make(5, issued=now), base64.b64encode(bytes(TEST_KEY.verify_key)).decode())
    assert L.status(lic, now, None) is L.Status.VALID
    assert L.status(lic, now + timedelta(minutes=6), None) is L.Status.EXPIRED
    assert L.status(lic, now - timedelta(days=365), None) is L.Status.CLOCK_ROLLBACK
    assert L.status(lic, now, now + timedelta(days=1)) is L.Status.CLOCK_ROLLBACK
    assert L.status(None, now, None) is L.Status.MISSING


def test_four_step_demo(client: TestClient, test_key: None, monkeypatch: pytest.MonkeyPatch) -> None:
    start = datetime.now(UTC)
    clock = {"now": start}
    monkeypatch.setattr(svc, "_now", lambda: clock["now"])

    # Step 1: works, and GET /license says who and until when.
    assert client.post("/license", json=make(60, issued=start)).status_code == 200
    client.post("/reports", json=_report())
    info = client.get("/license").json()
    assert info["licensee"] == "Demo Bank" and info["status"] == "valid" and info["expires_at"]

    # Step 2: upload a 5-minute licence.
    assert 299 <= client.post("/license", json=make(5, issued=start)).json()["seconds_remaining"] <= 300
    assert client.get("/lookup", params={"type": "phone", "value": "9876543210"}).status_code == 200

    # Step 3: after 5 minutes every request except /health and /license is 403 LICENSE_EXPIRED.
    clock["now"] = start + timedelta(minutes=5, seconds=1)
    svc._state.loaded_at = 0.0
    for method, path in (
        ("get", "/lookup?type=phone&value=9876543210"),
        ("get", "/map?pincode=560102"),
        ("get", "/alerts?pincode=560102"),
        ("post", "/admin/reset"),
        ("post", "/reports"),
    ):
        r = getattr(client, method)(path) if method == "get" else client.post(path, json={})
        assert r.status_code == 403, path
        assert r.json()["error"] == "LICENSE_EXPIRED"
    assert client.get("/health").json() == {"ok": True}
    assert client.get("/license").json()["status"] == "expired"

    # Step 4: a new licence works at once, no restart, and the old data is still there.
    assert client.post("/license", json=make(60, issued=clock["now"])).status_code == 200
    body = client.get("/lookup", params={"type": "phone", "value": "9876543210"}).json()
    assert body["report_count"] == 1


def test_clock_rollback_refused(client: TestClient, test_key: None, monkeypatch: pytest.MonkeyPatch) -> None:
    start = datetime.now(UTC)
    clock = {"now": start}
    monkeypatch.setattr(svc, "_now", lambda: clock["now"])
    client.post("/license", json=make(60, issued=start - timedelta(minutes=1)))
    assert client.get("/map", params={"pincode": "560102"}).status_code == 200  # high-water mark set
    clock["now"] = start - timedelta(days=365)
    svc._state.loaded_at = 0.0
    r = client.get("/map", params={"pincode": "560102"})
    assert r.status_code == 403 and r.json()["reason"] == "clock_rollback"


def test_expired_or_bad_upload_rejected(client: TestClient, test_key: None) -> None:
    old = make(5, issued=datetime.now(UTC) - timedelta(hours=1))
    assert client.post("/license", json=old).status_code == 400
    assert client.post("/license", json={"licensee": "x"}).status_code == 400


def _report() -> dict[str, object]:
    t = datetime.now(UTC) - timedelta(hours=1)
    return {
        "report_id": "rep_lic_1",
        "occurred_at": t.isoformat(),
        "reported_at": t.isoformat(),
        "reporter_id": "r_lic",
        "ip_prefix": "10.1.2",
        "channel": "Phone call",
        "scam_type": "otp-call",
        "identifier_type": "phone",
        "identifier_value": "+91 98765 43210",
        "pincode": "560102",
        "note": "asked for my OTP pretending to be the bank",
        "has_screenshot": False,
        "amount_lost_inr": 0,
    }
