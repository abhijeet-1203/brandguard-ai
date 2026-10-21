# Test report

All tests run against the **live pod** through the same functions the app calls. The suite
creates an isolated `quality-assurance` workspace with three approved rules, three approved
facts (including one expired) and seven fixture submissions that are analysed by the real
engine. No mocks, no in-memory substitutes.

Run it with:

```bash
cd brandguard/tests && python -m pytest -v
```

## Executed results

| Run | Command | Result |
| --- | --- | --- |
| Suite run 1 | `pytest brandguard/tests -v` | 25 passed, 3 failed (348 s) |
| Suite run 2 (after the first fixes) | `pytest brandguard/tests -v` | 26 passed, 2 failed (307 s) |
| Fixed tests re-run | `pytest brandguard/tests -v -k "rescan or audit"` | 2 passed (367 s) |
| **Final full suite** | `pytest brandguard/tests -v` | **28 passed, 0 failed (396 s)** |

The failures were not test noise — two of them exposed real defects, which were fixed and
re-verified:

1. **A finding that was corrected and re-scanned stayed "accepted" instead of "resolved".**
   The reconciliation step only closed findings whose prior status was exactly `open`.
   Fixed: `open`, `accepted` and `escalated` are all treated as unresolved, so an applied
   correction is closed only when the re-scan confirms it is gone.
2. **A required disclaimer was demanded on content with no discount at all.** The
   deterministic check applied `required_disclaimer` rules unconditionally. Fixed: rules
   carry an `applies_when` condition and are only enforced when the content matches it
   (verified by `test_required_disclaimer_applies_only_when_relevant`).
3. The third failure was a test-fixture artefact: the QA workspace's rules had been created
   by direct record writes, so no `guideline.created` audit entry existed. The test now
   creates and attempts to approve a rule through the real workflow — which also proves the
   separation-of-duties guard on guideline approval.

## What is covered

**Engine (`test_engine.py`)**
- prohibited terminology is detected with the approved replacement
- correct content produces no contradiction and no high-severity false positive
- a wrong warranty duration is flagged as `contradicted` with the approved fact cited and a
  usable suggested correction
- facts whose unit cannot be read unambiguously are not compared numerically
- a required disclaimer fires only when it applies
- an expired approved fact is surfaced as `expired`, not as current truth
- an unsupported claim is `not_found`, never `contradicted`
- confidentiality markers are flagged as ambiguous, for a human to confirm
- findings are never duplicated inside a review
- every finding carries a title, explanation, allowed severity, allowed evidence status and
  a detection method
- correction cycle: accept → apply (new version, analysis invalidated) → re-scan →
  finding resolved, with the original submission preserved as a version

**Workflow, permissions, isolation (`test_workflow.py`)**
- invalid state transitions are refused
- approval is blocked before a successful analysis
- separation of duties blocks self-approval
- a decision without a reason is refused
- unresolved mandatory findings block approval for a second reviewer
- an override without a documented reason is refused
- cross-workspace access is refused
- a submission with no content is refused
- an unsupported file type is reported as failed, with a note
- approval is refused when the analysed version is older than the current version
- guideline authoring is audited, and a rule author cannot approve their own rule

**Analytics consistency (`test_analytics.py`)**
- findings-by-category equals the stored rows it is drawn from
- open high-risk counts are traceable to stored findings
- evidence statuses stay inside the allowed set
- the seeded workspace is internally consistent (active rules have approvers, reviews have
  creators)

## Live reliability harness (in-app)

`bg_eval_run`, exposed on **Quality & evaluation**, executes eleven checks against the live
workspace on demand. Last executed result on the seeded workspace: **11 passed, 0 failed,
0 skipped** — workflow transition guard, approval-before-analysis block, self-approval
refusal, cross-workspace refusal, unsupported-file honesty, empty-submission refusal,
expired-fact surfacing, missing-evidence vs contradiction separation, no duplicate
findings, re-analysis requirement after revision, and failed runs recorded as failures.

## Labelled evaluation dataset

`src/pages/Quality.tsx` carries eleven labelled cases (correct content, tone, terminology,
contradicted fact, unsupported claim, expired reference, ambiguous claim, health claim,
confidential material, accessibility, corrected content) with the approved reference, the
expected finding and the expected evidence status. Cases E2–E10 are exercised as real
reviews in the workspace, and the engine tests above assert the same expectations.

**No precision/recall percentage is reported.** The labelled set is small and was not built
to be a statistically meaningful benchmark, so quoting an accuracy figure from it would
overstate what has been measured. What has been measured is stated above.

## Not covered

- OCR and text-in-image analysis (not implemented — see `LIMITATIONS.md`)
- Visual similarity beyond perceptual-hash comparison
- Load/performance testing
- Multi-browser end-to-end automation (the deployed app was exercised manually in the
  agent browser: every screen loaded, and the review, correction, approval, analytics and
  audit flows were driven end to end)
