# Observed shortcomings: first run of review-repo-code-quality

2026-10-20 · companion to [the code quality review](2026-10-20-code-quality-review.md)

## Context

The skill ran for the first time on 2026-10-20, against the two exercise problem files of a workshop repository. It produced 11 findings (9 rated High for safety, 2 Medium) and 5 needs-verification items.

| Item | Value |
| --- | --- |
| Skills | `review-repo-code-quality` v0.1.0, `code-quality-report-conventions` v0.1.0, `analyze-duplicates` (unversioned), all at con/skills@17e4471 |
| Reviewed | CodyCBakerPhD/fixer-upper-examples@d0ec2d5: `02/ex2.py` and `03/ex3.py`. The solution files were used for comparison only, and `01/` was out of scope |
| Report | `docs/code-reviews/2026-10-20-code-quality-review.md`, in [PR #1](https://github.com/CodyCBakerPhD/fixer-upper-examples/pull/1) |
| Applied changes | [PR #2](https://github.com/CodyCBakerPhD/fixer-upper-examples/pull/2), stacked on PR #1 |
| Tools | ruff 0.16.9, vulture 2.16, mypy 2.4.0 and jscpd 5.4.2, on Python 3.13.16 |

At the requester's direction, these shortcomings are recorded here and not in the report.

## Run time

The first report took 18 min 11 s from the request to PR #1.

| Phase | From (UTC) | To (UTC) | Duration |
| --- | --- | --- | --- |
| Setup: fetch the skills, read the files, check tools, ask for consent | 21:22:57, request | 21:25:02, consent given | 2 min 5 s |
| Review, write the report and open PR #1 | 21:25:02 | 21:41:08, PR #1 opened | 16 min 6 s |
| **Total to the first report** | 21:22:57 | 21:41:08 | **18 min 11 s** |
| Apply all proposals | 21:43:17, request | 21:47:08, PR #2 opened | 3 min 51 s |

- **What the times measure:** wall-clock time from the session's event log and git history. They include model, tool and network time.
- **Waiting on the requester:** under 30 s in total, for the consent question (asked after 21:24:34, answered at 21:25:02).

## Raised by the requester

The requester caught two design problems the report never raised.

### 1. The mode names live in several lists, not one registry

- The report praised the `Literal` mode types as well built. It never counted the edits needed to add a mode, although exercise 2's task asks for exactly that.
- `03/ex3.py` lists the names in four places: `T_legacy_1d_modes`, `T_1d_stats`, the `STATS` keys and `map_legacy_stat_name`. A plain statistic takes 2 edits; one with a sample variant takes 4.
- mypy misses a gap between them. A name in the `Literal` but missing from `STATS` type-checks, then raises `KeyError` at runtime (checked on 2026-10-20).
- A registry of dataclass entries keeps every mode in one place. The cost is that `mode` becomes a plain `str`.
- CL-1, applied in b3c403c, made `02/ex2.py` worse: it added a `Mode` `Literal` alongside one `if` branch per mode.

### 2. The `mode` selector shares its name with the "mode" statistic

- After PR #2, `02/ex2.py` reads `if mode == "mode": return _mode(x)`, and the `Mode` type lists `"mode"` as one of its own values.
- `03/ex3.py` calls the same concept "mode" on the legacy path and "stat" elsewhere. Line 82 (line 84 after PR #2) shows both: `stat = map_legacy_stat_name(mode, is_sample)`.
- The skill's checklist names "inconsistent naming for the same concept", yet the run missed it. CL-1 is what introduced `Mode`.
- Renaming the internals to `stat` is safe. Renaming the public `mode` parameter breaks callers that pass it by keyword.

## Noticed during the run

Four more shortcomings came out of the run itself. The first is how both of the requester's items got into the applied code.

- **Nothing checks the design of applied changes.** Verification means a behavior snapshot plus linters. Both passed on CL-1 while it introduced items 1 and 2. Step 5 never re-reviews the applied result against the checklist.
- **A conceded better design never became a finding.** The comparison section said the solution's `STATS` table is more compact and avoids ruff's PLR0911 warning. Even so, the report's Appendix A kept the `if` chain.
- **Effort went to what tools can measure.** The report runs 726 lines for 175 lines of code. Much of it is about exception types and last-digit float behavior, while two design problems went unmentioned.
- **Tooling:**
  - `analyze-duplicates/generate-report.py` crashes on jscpd 5.x JSON (`AttributeError` at line 71, because `sources` is now a count, not a map).
  - The first ruff run wrote `.ruff_cache/` into the reviewed repository. It was removed, and later runs used `--no-cache`. The skill warns about jscpd writing into the repository, but not about linters.

## Common causes

Most of the misses trace back to one gap: the procedure finds what tools flag, and it has no step for design questions.

- **Findings start from tools.** Step 2 is a mechanical sweep, and Step 3 traces only the candidates it turns up. No linter flags parallel lists of names or a selector named after one of its own values, so neither ever became a candidate.
- **No extensibility check.** Both files state their own change requests: exercise 2 asks to add `"stdev"`, and exercise 3 asks for a multi-statistic API. Nothing in the procedure asks how many edits each request takes.
- **"Safe" is not "better".** Confidence ratings and verification measure only whether behavior is preserved. A change can be rated High confidence and still make the design worse, as CL-1 did.

## Possible changes to the skill

Six additions to the con/skills procedure would have caught every shortcoming above. The first three target the design gap.

| Change | Where in the skill | Would have caught |
| --- | --- | --- |
| Extensibility check: for each change the code asks for itself (task or TODO comments, open issues), count the edits it takes, and check whether a type checker catches a missed one | New Step 2 bullet | Item 1 |
| Parallel-list sweep: search for string literals that recur across a `Literal`, dict keys and `if` comparisons | Step 2, "Duplication" | Item 1 |
| Naming checks: a parameter or type named after one of its own values, or one concept under two names | Step 2, "Idiom drift" | Item 2 |
| When the comparison or reference code does something better, raise it as a finding, or say why not | Step 4 | Appendix A's `if` chain |
| Re-review applied changes against the full checklist, not just the behavior snapshot | Step 5 | CL-1's regressions |
| Update `generate-report.py` for jscpd 5.x, and tell linters not to write caches into the repository (`--no-cache`, `--cache-dir`) | `analyze-duplicates`; Step 2 | The tooling issues |
