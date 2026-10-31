"""Mint a signed licence on the vendor's laptop. The private key never enters the repository.

    uv run python -m scripts.mint_licence --licensee "Demo Bank" --minutes 5 --out licences/demo-5min.json
    uv run python -m scripts.mint_licence --licensee "Demo Bank" --days 365 --out licences/demo-long.json

Key: base64 Ed25519 seed at ~/.scammap-keys/licence_ed25519.key (or --key / $SCAMMAP_LICENCE_KEY).
"""

import argparse
import base64
import json
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from nacl.signing import SigningKey

from app.domain.licence import PUBLIC_KEY_B64, canonical_payload, verify
from app.domain.timefmt import IST

DEFAULT_KEY = Path(os.environ.get("SCAMMAP_LICENCE_KEY", "~/.scammap-keys/licence_ed25519.key")).expanduser()


def mint(licensee: str, lifetime: timedelta, key_path: Path) -> dict[str, str]:
    key = SigningKey(base64.b64decode(key_path.read_text().strip()))
    if base64.b64encode(bytes(key.verify_key)).decode() != PUBLIC_KEY_B64:
        raise SystemExit("this private key does not match the public key built into the server")
    now = datetime.now(IST).replace(microsecond=0)
    fields = {
        "licence_id": "lic_" + secrets.token_hex(6),
        "licensee": licensee,
        "issued_at": now.isoformat(),
        "expires_at": (now + lifetime).isoformat(),
    }
    signature = key.sign(canonical_payload(fields)).signature
    document = {**fields, "signature": base64.b64encode(signature).decode()}
    verify(document)  # never hand out a licence the server would refuse
    return document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--licensee", required=True)
    parser.add_argument("--minutes", type=float, default=0)
    parser.add_argument("--days", type=float, default=0)
    parser.add_argument("--key", type=Path, default=DEFAULT_KEY)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    lifetime = timedelta(minutes=args.minutes, days=args.days)
    if lifetime <= timedelta(0):
        raise SystemExit("give --minutes or --days")
    document = mint(args.licensee, lifetime, args.key)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(document, indent=2) + "\n")
    print(f"{args.out}: {document['licensee']} until {document['expires_at']}")


if __name__ == "__main__":
    main()
