# DECISIONS — open research decisions

Questions that need an owner's call but should not block the task that raised them
(convention in root `CLAUDE.md`). Each entry keeps the current working value until it is
decided. When one is decided, move it to **Closed** with the date and the choice. If the
decision changes a screening bar or anything else under preregistration, it also needs a
dated entry in the `notes/PREREGISTRATION.md` amendment log.

## Open

### D1 — Raise the market-orthogonality low bar above 0.05?

- **Raised:** 2026-09-28, by Claude (while recording the screening bars)
- **Question:** The low bar kills a candidate when |r| with the market is **below 0.05**.
  `BEHAVIOURAL_RESULTS.md` §4 puts the failed behavioural rule at **+0.05** with the
  market, and §5.2 introduced this screen because of that rule's failure. As worded, the
  bar passes the rule the screen was built to catch.
- **Options:**
  1. Keep "< 0.05" (current, provisional).
  2. Make it inclusive: kill at |r| ≤ 0.05.
  3. Raise it to a higher value (e.g. 0.10) that clears the behavioural rule with a margin.
- **Context:** `modelling/CLAUDE.md` §3 "Screening bars"; `notes/BEHAVIOURAL_RESULTS.md`
  §4, §5; `.claude/skills/new-candidate/SKILL.md` step c.

### D2 — Is 0.80 too loose as a redundancy bound?

- **Raised:** 2026-09-28, by Claude
- **Question:** The high bar kills a candidate as redundant when |r| with the market is
  **above 0.80**. The one "priced" feature in the notes (rolling last-5 shot share) was
  killed by a partial test after controlling for closing odds (partial p = 0.73), not by
  a raw correlation. Its raw |r| with the market was never published. A feature can be
  priced at a raw |r| well below 0.80, so this bound may not catch it.
- **Options:**
  1. Keep 0.80 (current, provisional).
  2. Lower it to a stated value.
  3. Replace the raw-|r| test with an incremental one: the candidate's partial
     association after controlling for the market, as in LEAGUE_STUDY F10.
- **Context:** `modelling/CLAUDE.md` §3 "Screening bars"; `notes/LEAGUE_STUDY.md` F10
  (shot share, "priced"), F11 (venue "already priced"); `notes/STATE.md` ledger row
  "Rolling last-5 shot share".

### D3 — Step c for candidates that are themselves market prices

- **Raised:** 2026-09-28, by Claude (an interpretation adopted in `/new-candidate`)
- **Question:** Retry claims #9 (nowgoal's O/U line) and #10 (the AH line) *are* market
  lines. Their |r| with the market is about 1, so the redundancy bar would kill them
  mechanically. Currently the skill marks step c "not applicable" for a market-price
  candidate.
- **Options:**
  1. Keep "not applicable" (current, provisional).
  2. Apply the bar anyway, which kills #9 and #10 at step c.
  3. For a market candidate, correlate only against the *other* market columns (e.g. AH
     against O/U), which fits #10's "adds over O/U" framing.
- **Context:** `.claude/skills/new-candidate/SKILL.md` step c;
  `notes/RETRY_CANDIDATES_2026-09-23.md` §5 (#9, #10).

### D4 — What "the market price" means for the screen

- **Raised:** 2026-09-28, by Claude (an interpretation adopted in `/new-candidate`)
- **Question:** `BEHAVIOURAL_RESULTS.md` §4–5 says "the market price" without naming a
  column. Currently the bar applies to the **largest |r| across the pre-kickoff market
  columns** (`implied_init_*`, `implied_live_*`, and the O/U line where present). Taking
  the largest |r| makes the low bar easier to pass and the high bar easier to trip.
- **Options:**
  1. Keep max |r| across the pre-kickoff market columns (current, provisional).
  2. Name one column (e.g. the favourite's `implied_live_*` probability, or the O/U line,
     which MARKET_LINE found to be the one live ranker).
  3. Use one composite market score (e.g. the multiple correlation R of the candidate on
     all market columns).
- **Context:** `.claude/skills/new-candidate/SKILL.md` step c;
  `notes/BEHAVIOURAL_RESULTS.md` §4, §5; `notes/MARKET_LINE_FINDINGS.md` §2–3.

## Closed

(none yet)
