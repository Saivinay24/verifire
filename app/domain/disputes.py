"""Dispute policy: how long a review lasts and what ends it. Not trust-engine parameters.

The trust engine's 72 constants live in constants.py and are untouched by disputes. These five
numbers only bound the brief's rule that a disputed number is never KNOWN_SCAM while under review,
so a dispute protects a wrongly reported owner without becoming a scammer's shield.
"""

from datetime import timedelta

DISPUTE_REVIEW_WINDOW = timedelta(days=7)  # Every dispute ends: decided, overruled, or lapsed by then.
# Overruled by new victims: people and networks not seen before the dispute, reporting after it,
# who on their own clear the full KNOWN_SCAM bar, spread over at least 6 hours, so a burst fired
# right after a dispute (the harassment pattern) can never break it; an active scam keeps
# producing victims over hours and days.
DISPUTE_OVERRULE_SPREAD = timedelta(hours=6)
DISPUTE_LOCK = timedelta(days=90)  # After rejected, overruled or lapsed: no new dispute on that number.
DISPUTE_NETWORK_WINDOW = timedelta(hours=24)
DISPUTE_PER_NETWORK_DAY = 20  # New disputes from one network (/24) per 24 h before 429.
