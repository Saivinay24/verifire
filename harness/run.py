"""Run the trust suite against a server and print a scoreboard.

    uv run python -m harness.run --base-url https://<live-host> --seeds 5 --out evidence/

Resets the server first (POST /admin/reset). Exit code 1 if any hard expectation fails.
"""

import argparse
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import httpx

from harness.scenarios import JUNK, trust_suite


class Client(Protocol):
    def post(self, url: str, *, json: Any = None) -> Any: ...
    def get(self, url: str, *, params: Any = None) -> Any: ...


def run_suite(client: Client, seeds: list[int], log: list[str]) -> dict[str, Any]:
    failures: list[str] = []
    soft_failures: list[str] = []
    tally: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # name -> [passed, total]
    statuses: dict[int, int] = defaultdict(int)

    resp = client.post("/admin/reset")
    assert resp.status_code == 200, f"reset failed: {resp.status_code}"

    for id_type, value in JUNK:
        r = client.get("/lookup", params={"type": id_type, "value": value})
        ok = r.status_code == 400
        tally["junk-lookup-400"][0] += ok
        tally["junk-lookup-400"][1] += 1
        if not ok:
            failures.append(f"junk lookup {id_type}={value!r} -> {r.status_code}")

    for seed in seeds:
        now = datetime.now(UTC)
        suite = trust_suite(seed, now)
        for sc in suite:
            for rep in sc.reports:
                statuses[client.post("/reports", json=rep).status_code] += 1
            # Junk reports must be refused at the door.
            junk = dict(sc.reports[0], report_id=f"junk_{seed}_{sc.name}", identifier_value="12345",
                        identifier_type="phone")  # fmt: skip
            jr = client.post("/reports", json=junk)
            tally["junk-report-400"][0] += jr.status_code == 400
            tally["junk-report-400"][1] += 1
        for sc in suite:
            body = client.get(
                "/lookup", params={"type": sc.identifier_type, "value": sc.identifier_value}
            ).json()
            msg = sc.expect(body)
            key = sc.name if not sc.name.startswith("bomb-verified") else "bomb-verified-entries"
            tally[key][1] += 1
            line = (
                f"seed={seed} {sc.name:<32} reports={len(sc.reports):>3} verdict={body.get('verdict'):<17} "
                f"distinct={body.get('distinct_reporters'):>3} score={body.get('trust_score')} "
                f"shown={body.get('display_value')}"
            )
            if msg is None:
                tally[key][0] += 1
                log.append("PASS " + line)
            else:
                log.append(("SOFT " if sc.soft else "FAIL ") + line + f"  <- {msg}")
                (soft_failures if sc.soft else failures).append(f"seed={seed} {sc.name}: {msg}")
    return {"tally": dict(tally), "failures": failures, "soft": soft_failures, "statuses": dict(statuses)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--first-seed", type=int, default=1)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    log: list[str] = [
        f"harness run {datetime.now(UTC).isoformat(timespec='seconds')} against {args.base_url}"
    ]
    started = time.perf_counter()
    with httpx.Client(base_url=args.base_url, timeout=30) as client:
        result = run_suite(client, list(range(args.first_seed, args.first_seed + args.seeds)), log)
    log.append("")
    log.append(f"report responses by status: {result['statuses']}")
    for name, (passed, total) in sorted(result["tally"].items()):
        log.append(f"{name:<34} {passed}/{total}")
    log.append(f"hard failures: {len(result['failures'])}   soft (disclosed limits): {len(result['soft'])}")
    log.append(f"elapsed {time.perf_counter() - started:.1f}s")
    text = "\n".join(log)
    print(text)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M")
        (args.out / f"T1_trust_harness_{stamp}.txt").write_text(text + "\n")
    return 1 if result["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
