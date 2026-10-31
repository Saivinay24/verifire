"""Every tunable number in the trust rules, with the reason it has that value.

Tuned only on the randomised harness (rich AND plain genuine campaigns vs every attack, all
seeds). No constant refers to a specific identifier.
"""

from datetime import timedelta

# --- Verdict -------------------------------------------------------------------------------
KNOWN_MIN_GROUPS = 3  # Same "3 different people" bar the brief uses for unmasking.
KNOWN_MIN_DESCRIBED = 2  # ...and at least 2 of them said what happened or showed proof of harm.
# Smallest real case clears it: three independent people who each show proof of harm, even with
# blank notes (3 x 0.575). Three blank clicks with no proof (1.5) never do.
KNOWN_MIN_SCORE = 1.7
UNMASK_MIN_SCORE = 1.7  # Unmask only when the weighted evidence agrees with the 3-people bar.

# --- Step 1: grouping edges ----------------------------------------------------------------
NOTE_DUP_SIMILARITY = 0.7  # MinHash Jaccard of 4-grams; copy-paste with small edits scores > 0.8.
NOTE_DUP_MIN_CHARS = 15  # Short notes ("scam", "fraud call") collide by chance; never link them.
BURST_WINDOW = timedelta(minutes=60)
BURST_MIN_REPORTS = 8  # A burst smaller than this is too small to call coordinated.
BURST_MIN_DIVERSITY = 0.5  # < half the notes distinct (blank counts as one) = lockstep brigade.
# Coordinated burst: a burst with no proof of harm AND a behavioural tell is one actor.
# Each tell alone is weak; real victims essentially never show one at scale with zero evidence.
COORD_MAX_EVIDENCE_SHARE = 0.15  # Under 15% of the burst has a screenshot or a stated loss...
COORD_INSTANT_LAG = timedelta(minutes=2)  # ...and >= 80% filed within 2 min of the "incident"
COORD_INSTANT_SHARE = 0.8  # (victims of a 3-hour call do not report 30 s later), or
COORD_UNIFORM_CV = 0.05  # note lengths as even as generated text, or
COORD_SCATTER_SHARE = 0.5  # no scam type covers half the burst (one number runs one script).

# --- Step 2: per-reporter weight -----------------------------------------------------------
NOTE_SHORT_CHARS = 10
NOTE_FULL_CHARS = 25
NOTE_WEIGHT_EMPTY = 0.5  # No description at all: the brief says a personal one counts more.
NOTE_WEIGHT_SHORT = 0.8
NOTE_NOVELTY_PENALTY = 0.85  # novelty = 1 - 0.85 * excess similarity to earlier notes (Gemini 4.3).
NOTE_NOVELTY_FREE = 0.4  # Real victims of one script share phrases; similarity below this is free.
NOTE_NOVELTY_FLOOR = 0.3
EVIDENCE_SCREENSHOT = 0.15
EVIDENCE_LOSS = 0.15
EVIDENCE_LEXICON = 0.10
EVIDENCE_CAP = 1.3
REPEAT_DAMPING = 0.30  # 1 / (1 + 0.3 (c - 1)) for c repeats by the same reporter.
VELOCITY_FREE_PER_HOUR = 3  # Reports per hour (any identifier) before a reporter is damped.
VELOCITY_DAMPING = 0.25
VERIFIED_REPORTER_FACTOR = 0.5  # Reporter has also reported a verified number: less reliable.
UNIT_WEIGHT_MIN = 0.05

# --- Step 3: per-/24 sub-linear cap ----------------------------------------------------------
IP_CAP_SLOPE = 0.15  # Two people on one Wi-Fi: 1.10. Twenty-two accounts: 1.25.
IP_CAP_MAX = 1.25
GROUP_CAP = 1.3  # A group is one voice: at most one person with full evidence.

# --- Step 4: campaign factor (bounded nudges; only with >= 4 groups) -----------------------
CAMPAIGN_MIN_GROUPS = 4
CAMPAIGN_FLOOR = 0.2
CAMPAIGN_CEIL = 1.1
BURST_RATE_FREE = 0.5  # Reports per minute that a real viral wave can plausibly reach.
BURST_RATE_DAMPING = 0.6  # 2 reports/min (40 in 20 min) -> 0.53.
AREA_MIN_UNITS = 8
AREA_CONCENTRATION = 0.8  # >= 80% of reporters in <= 2 pincodes...
AREA_MAX_PINCODES = 2
AREA_FACTOR = 0.7  # ...AND arriving fast: local brigade, not a local scam told over days.
EVIDENCE_FACTOR_BASE = 0.85  # Floor so a plain genuine campaign (no screenshots) is never crushed.
EVIDENCE_FACTOR_SLOPE = 0.25
SYNC_REPORTED_IQR = timedelta(minutes=20)
SYNC_RATIO = 4.0  # occurred_at spread > 4x reported_at spread: back-dated brigade.
SYNC_FACTOR = 0.7
STYLE_MIN_NOTES = 8  # Length spread over fewer notes is noise.
STYLE_MAX_CV = 0.06  # Below every genuine sample in the harness (p5 0.07); batch text sits ~0.03.
STYLE_FACTOR = 0.8
COORDINATION_MIN_UNITS = 8
COORDINATION_MAX_SHARE = 0.5  # Fast wave where most reporters collapsed into shared groups...
COORDINATION_FACTOR = 0.5  # ...means the leftovers are likely the same brigade.
BLANK_MIN_UNITS = 8
BLANK_MAX_SHARE = 0.5  # Most reporters wrote nothing: real victims describe what happened.
BLANK_FACTOR = 0.4

# --- Alerts --------------------------------------------------------------------------------
# Pile-on gate. A real campaign's victims describe it and agree on what it was; a pile-on (the
# brief's "40 friends reporting a real bakery") does not. Only judged with enough people to tell.
PILE_ON_MIN_UNITS = 8
SAME_CONNECTION_PAIR_WINDOW = timedelta(minutes=15)  # Two accounts, one connection, minutes apart.
SAME_CONNECTION_MIN_ACCOUNTS = 3  # Two accounts on one /24 may be neighbours on a carrier; 3+ is a farm.
PILE_ON_BLANK_SHARE = 0.75  # Real victims leave ~25% blank (measured); 3x that is a pile-on writing nothing.
PILE_ON_MIN_NOTES = 6
PILE_ON_REVIEW_SHARE = 0.3  # Real victims almost never write a shop review; a pile-on of friends does.
PILE_ON_TYPE_SHARE = 0.5  # Victims of one identifier mostly pick the same scam type (~85%).
ALERT_MAX_GROUP_REPORTS = 2  # A victim may report twice to add detail; a third report on one number is spam.
ALERT_MIN_CAMPAIGN = 0.5  # Reports on identifiers damped below this never feed alerts.
SPIKE_MIN_COUNT = 5
SPIKE_RATIO = 2.0

# --- Rate limits (payload time, brief rule 1 and 4) ----------------------------------------
RATE_WINDOW = timedelta(hours=1)
RATE_SAME_IDENTIFIER = 3  # Repeats of one identifier per reporter per hour before 429.
RATE_PER_REPORTER = 20  # Reports per reporter per hour, any identifier, before 429.

# --- Disputes (the owner of a number asks for a review) --------------------------------------
# Brief: while under review a number is never KNOWN_SCAM. These bound how long and how often that
# can hold, so a dispute protects a wrongly reported owner without becoming a scammer's shield.
DISPUTE_REVIEW_WINDOW = timedelta(days=7)  # Every dispute ends: decided, overruled, or lapsed by then.
# Overruled by new victims: people and networks not seen before the dispute, reporting after it,
# who on their own clear the full KNOWN_SCAM bar above...
DISPUTE_OVERRULE_SPREAD = timedelta(hours=6)  # ...spread over at least 6 hours, so a burst fired
# right after a dispute (the harassment pattern) can never break it; an active scam keeps
# producing victims over hours and days.
DISPUTE_LOCK = timedelta(days=90)  # After rejected, overruled or lapsed: no new dispute on that number.
DISPUTE_NETWORK_WINDOW = timedelta(hours=24)
DISPUTE_PER_NETWORK_DAY = 20  # New disputes from one network (/24) per 24 h before 429.
