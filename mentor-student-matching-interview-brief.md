# Mentor–Student Matching — Candidate Brief

Build a **matching tool** (not a one-off CSV export) that assigns students to mentors using the provided datasets. Explore the data, infer field meanings, and make your own design choices. Be ready to explain and demo your approach.

## Data

You are given two files in this folder:

- `[mentors_prod_200_enriched.csv](mentors_prod_200_enriched.csv)`
- `[students_prod_2000_enriched.csv](students_prod_2000_enriched.csv)`

Open them, inspect the columns, and parse any JSON fields. Note the scale: many more students than mentors.

## What you must build

A **rule-driven tool** the interviewer can run, tune, and override — for example via config files, a CLI, or a simple UI.

At minimum, the tool should support:

- **Configurable rules and parameters** (weights, limits, thresholds)
- **Manual overrides** — e.g. force a student–mentor pair, block a pair, or skip someone from the pool
- **Re-run on change** — updating config or overrides recomputes results
- **Visible outcomes** — assignments plus a way to judge how good the matching is (your own metrics)

A flat CSV alone is not sufficient.

## Questions (in order)

Work through these in sequence. Each builds on the previous one.

### Q1 — Feasible matching

Assign each student to **one** mentor. **Time** and **gender** are hard requirements — discover how those are represented in the data and enforce them.

Also define how mentor capacity works (a mentor may serve multiple students). Report anyone you cannot assign and why.

### Q2 — Parent expectations

Among valid assignments from Q1, improve matches using **parent/student expectations** (see the student data).

Propose your own **matching method**, **scoring formula**, and **way to measure** how good the result is compared to a simple baseline.

### Q3 — Two-way fit

Extend Q2 so **mentor preferences** and **student context** (e.g. symptoms) matter too, not only what the parent wants.

Explain how you balance both sides and how you detect poor fits.

### Q4 — Rejection and re-matching

After an initial match, simulate students **rejecting** their mentor with roughly **20%** probability. Re-assign rejected students to another mentor.

Describe your re-matching process and how match quality changes after rejection.

## Deliverables

Bring (or demo live):

- Runnable tool and brief README
- Config for tunable parameters
- A way to apply interviewer overrides without editing code
- Assignment output with enough detail to understand *why* each pair was chosen
- Metrics or report showing match quality

## Notes

- Text fields may be mixed Vietnamese and English.
- Session length and schedule structure are in the data — read the files.
- Document assumptions, trade-offs, and algorithm choices.