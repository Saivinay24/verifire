"""Turn a free-text note into privacy-safe features, then forget the text.

We keep three things: the note's length, a MinHash signature of its character 4-grams (enough
to spot copy-paste brigades, not enough to read the note back), and whether it mentions a
known scam method. The raw note is never stored or logged (privacy rules 1 and 5).
"""

import hashlib
import re
import unicodedata
from typing import NamedTuple

SIG_SIZE = 64  # MinHash permutations; Jaccard estimate error ~ 1/sqrt(64) = 0.125
LSH_BANDS = 16  # 16 bands x 4 rows: pairs with Jaccard >= ~0.6 almost always share a band
_SHINGLE = 4
_PRIME = (1 << 61) - 1
_MAX_HASH = (1 << 32) - 1


def _permutations() -> list[tuple[int, int]]:
    """Fixed (a, b) pairs for h(x) = (a*x + b) mod p, derived deterministically so signatures are stable."""
    out = []
    for i in range(SIG_SIZE):
        digest = hashlib.blake2b(f"scammap-minhash-{i}".encode(), digest_size=16).digest()
        a = int.from_bytes(digest[:8], "big") % (_PRIME - 1) + 1
        b = int.from_bytes(digest[8:], "big") % _PRIME
        out.append((a, b))
    return out


_PERMS = _permutations()

# Words victims use when describing a real scam method, in English, Hinglish and Hindi.
# A mention earns a small evidence bonus; its absence never counts against a report.
_LEXICON = re.compile(
    r"police|cbi|customs|arrest|parcel|courier|fedex|kyc|pan card|aadhaar|otp|upi|qr|refund|"
    r"cashback|lottery|prize|loan|electricity|bijli|power cut|disconnect|task|deposit|invest|"
    r"profit|trading|video call|skype|fir|warrant|account block|band ho|paise kat|"
    r"पुलिस|गिरफ्तार|पार्सल|कस्टम|केवाईसी|ओटीपी|बिजली|लोन|लॉटरी|इनाम|पैसे|खाता|धोखा|ठगी|वीडियो कॉल",
    re.IGNORECASE,
)


# Plain words for "this was a scam", for notes that say so without naming the method ("fraud call").
_SCAM_WORDS = re.compile(
    r"scam|fraud|fake|cheat|dhokha|dhoka|thag|nakli|farzi|ठग|धोखा|फर्जी|नकली|स्कैम|फ्रॉड",
    re.IGNORECASE,
)

# Words about a shop, its goods or its service: a review, not a scam report. Generic consumer
# vocabulary, so a pile-on of reviews (the brief's "40 friends reporting a real bakery") shows up.
_REVIEW = re.compile(
    r"shop|store|bakery|restaurant|hotel|dukaan|dukan|cake|bread|pastr|sweet|mithai|food|taste|stale|"
    r"expired|hygien|dirty|cockroach|rude|arrogant|misbehav|staff|owner|shopkeeper|overpriced|"
    r"quality|star|kharab|basi|bekar|dont buy|don't buy|never order|"
    r"दुकान|मिठाई|बासी|खराब|घटिया",
    re.IGNORECASE,
)


class NoteFeatures(NamedTuple):
    length: int
    signature: list[int]  # empty when the note is too short to fingerprint
    mentions_method: bool
    names_scam: bool = False  # names a scam method or calls it a scam in plain words
    is_review: bool = False  # complains about a shop or product and names no scam method


def _canonical(note: str) -> str:
    text = unicodedata.normalize("NFKC", note).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"(.)\1{2,}", r"\1", text)  # "pleaseeeee" -> "please"
    return re.sub(r"\s+", " ", text).strip()


def extract(note: str | None) -> NoteFeatures:
    text = _canonical(note or "")
    method = bool(text) and bool(_LEXICON.search(text))
    names_scam = method or bool(_SCAM_WORDS.search(text))
    review = not method and bool(_REVIEW.search(text))
    if len(text) < _SHINGLE:
        return NoteFeatures(len(text), [], method, names_scam, review)
    shingles = {
        int.from_bytes(hashlib.blake2b(text[i : i + _SHINGLE].encode(), digest_size=8).digest(), "big")
        for i in range(len(text) - _SHINGLE + 1)
    }
    signature = [min((a * x + b) % _PRIME for x in shingles) & _MAX_HASH for a, b in _PERMS]
    return NoteFeatures(len(text), signature, method, names_scam, review)


def similarity(a: list[int], b: list[int]) -> float:
    """Estimated Jaccard similarity of two notes' 4-gram sets; 0 when either note is too short."""
    if not a or not b:
        return 0.0
    return sum(x == y for x, y in zip(a, b, strict=True)) / SIG_SIZE


def lsh_bands(signature: list[int]) -> list[tuple[int, tuple[int, ...]]]:
    """Band keys for locality-sensitive hashing, so near-duplicate search is not all-pairs."""
    if not signature:
        return []
    rows = SIG_SIZE // LSH_BANDS
    return [(i, tuple(signature[i * rows : (i + 1) * rows])) for i in range(LSH_BANDS)]
