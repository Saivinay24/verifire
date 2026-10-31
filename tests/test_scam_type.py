"""Which scam type a lookup shows when people report different things about one number."""

from fastapi.testclient import TestClient

from tests.test_api_contract import _report

NUMBER = "+91 98765 43210"


def _look(client: TestClient) -> dict:  # type: ignore[type-arg]
    return client.get("/lookup", params={"type": "phone", "value": NUMBER}).json()  # type: ignore[no-any-return]


def test_a_brigade_cannot_relabel_a_real_scam(client: TestClient) -> None:
    for n in range(1, 6):  # five real victims on five networks: digital arrest
        assert client.post("/reports", json=_report(n * 7)).status_code == 201
    for k in range(12):  # twelve fake accounts on one connection all say "lottery"
        body = _report(
            100 + k, ip_prefix="49.200.12", reporter_id=f"fake_{k}", scam_type="lottery-prize", note=""
        )
        client.post("/reports", json=body)
    body = _look(client)
    assert body["scam_type"] == "digital-arrest"
    types = {t["scam_type"]: t["people"] for t in body["scam_types"]}
    assert (
        types["digital-arrest"] == 5 and types.get("lottery-prize", 0) <= 1
    )  # one connection, one vote at most


def test_every_reported_type_is_listed_most_people_first(client: TestClient) -> None:
    for n, st in zip(
        range(1, 6),
        ["digital-arrest", "digital-arrest", "digital-arrest", "courier-customs", "otp-call"],
        strict=True,
    ):
        client.post("/reports", json=_report(n * 7, scam_type=st))
    body = _look(client)
    assert body["scam_type"] == "digital-arrest"
    assert body["scam_types"][0]["scam_type"] == "digital-arrest"
    assert {t["scam_type"] for t in body["scam_types"]} == {"digital-arrest", "courier-customs", "otp-call"}
