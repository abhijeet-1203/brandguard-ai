# BrandGuard AI — architecture

## 1. Where the product runs

BrandGuard AI is a **pod app**: a static React bundle served by the platform, with the pod
itself as the backend. There is no separate application server, no in-memory state, and no
second database. That is deliberate — it means authorisation, audit and data residency are
handled by the same runtime for the UI and the automation.

```
┌──────────────────────────────┐        ┌──────────────────────────────────────────┐
│ Browser: React + TS SPA      │        │ Pod runtime                              │
│  • reads: datastore SQL,     │  auth  │  • 22 tables (workspace-scoped rows)      │
│    records API               │ ─────► │  • 18 functions (all mutations + analysis)│
│  • writes: pod functions     │        │  • 3 agents (LLM, schema-constrained)     │
│  • live: change WebSocket    │        │  • pod files: /brandguard/...             │
└──────────────────────────────┘        └──────────────────────────────────────────┘
```

The client never holds credentials or model keys. Every privileged action is a function
call, and each function re-derives the caller's membership and role before doing anything.

## 2. Backend functions

| Function | Type | Responsibility |
| --- | --- | --- |
| `bg_bootstrap` | API | Idempotent session bootstrap: membership, default policy, provider disclosure records |
| `bg_workspace_action` | API | Create/update/archive a workspace and its brand profile (admin only) |
| `bg_team_action` | API | Invite, re-role, suspend, remove members; guards the last administrator (admin only) |
| `bg_policy_update` | API | Approval, AI-flow and retention policy (admin only) |
| `bg_guideline_action` | API | Create/edit/approve/archive rules with version snapshots |
| `bg_guideline_extract` | JOB | Propose draft rules from an uploaded brand document |
| `bg_fact_action` | API | Approved facts, verification states and evidence records |
| `bg_asset_action` | API | Register, approve, replace, archive assets with hashes and colours |
| `bg_document_ingest` | API | Register a pod file and extract its text (converted markdown) |
| `bg_review_create` | API | Validate, extract attachments, store version 1 and its segments |
| `bg_review_analyse` | JOB | The compliance engine (see §3) |
| `bg_correction_action` | JOB | Accept/reject/edit/regenerate/apply/restore corrections |
| `bg_review_workflow` | API | State machine, approvals, overrides, escalation, audit |
| `bg_comment_action` | API | Comments, replies, mentions, thread resolution |
| `bg_insights_generate` | API | Governance memory: recurring problems and guideline gaps |
| `bg_eval_run` | JOB | Live reliability harness used by the Quality page |

## 3. The compliance engine (`bg_review_analyse`)

**Stage 1 — ingestion.** The review's current text, its segments and any attached document
text (page-marked by the platform's converter) are loaded. An empty submission is refused
before anything else happens.

**Stage 2 — reference retrieval.** Only this workspace's *active* guidelines, *approved*
facts (with their expiration dates) and registered assets are retrieved. Nothing from
another workspace is ever queried.

**Stage 3 — deterministic checks.**
- prohibited / deprecated / required terminology (exact, word-boundary matching)
- mandatory disclaimers, gated by an `applies_when` condition so a disclaimer is only
  demanded when it is relevant
- numeric comparison against approved facts, **unit-aware**: only units the engine can read
  unambiguously (months, currency, percent, m², year, kg, cm, mm, hours, days, litres) are
  compared; anything else is reported as *not machine-comparable* instead of guessed at.
  When the sentence does not name the fact's subject, the finding is `ambiguous`, not
  `contradicted`
- expired approved facts → `expired` (never treated as current truth)
- promotional claims (guarantees, superlatives, quantified benefits, comparative, health,
  environmental, certification, financial) checked against approved evidence; absent
  evidence is `not_found`, never a contradiction
- confidentiality patterns (internal-only, embargo, unreleased, cost/margin, identifiers)
- formatting (capital runs, exclamation stacking)
- HTML accessibility (missing/empty alt text, vague link text, skipped heading levels)
- visual checks: perceptual-hash comparison against approved/archived assets and dominant
  colour distance against the workspace palette

**Stage 4 — AI analysis.** The agent receives the content (delimited and labelled
untrusted), the applicable rules with their codes and enforcement levels, the approved
facts with ids and scopes, the asset list, and the limitations already recorded by the
deterministic stage. It must return the schema-declared JSON.

**Stage 5 — validation.** Every returned finding is checked: allowed category, allowed
severity, allowed evidence status, confidence clamped to 0–1, cited rule code present in
the supplied set, cited fact id present in the supplied set, and the quoted span actually
present in the content. Anything that fails is dropped or repaired and the reason is
recorded as a run limitation. A malformed reply is retried once, then reported honestly as
"no AI findings were used" — the run is never presented as a clean result.

**Stage 6 — reconciliation.** Deterministic and AI findings are merged on a fingerprint
(category + normalised quoted text + rule code); the higher severity wins and a correction
from either source is preserved. On re-analysis, findings that are no longer detected are
marked **resolved with the version that confirmed it**, still-open ones are updated in
place, and re-detected ones are reopened.

**Stage 7 — routing.** Risk level is derived from the worst open severity. Critical
claims route to the compliance reviewer when policy requires it; an eligible reviewer who
is not the creator is assigned and notified.

**Stage 8 — persistence.** Findings, the run record (model, analysis version, statistics,
sources used, limitations) and an audit entry are written. A failure writes
`analysis_failed` with the error — never a completed review.

## 4. Authorisation model

Two ledgers apply to every call: the platform's grants on the function, and the caller's
own workspace role.

1. The **app** renders according to the caller's role (UX only).
2. Every **mutation** goes through a function that resolves `bg_memberships` for
   `(workspace, caller email)` and refuses the action unless the role allows it.
3. **Ownership** is re-checked on the record itself: a review, guideline, fact or asset
   whose `organization_id` differs from the requested workspace is refused.
4. **Policy guards** are evaluated at decision time, not at render time: separation of
   duties, mandatory-finding blocking (with documented override), compliance-reviewer
   requirement for critical findings, second-reviewer rule, and the rule that the analysed
   version must match the current version.

Role capabilities:

| Capability | admin | brand manager | compliance reviewer | reviewer | creator |
| --- | :-: | :-: | :-: | :-: | :-: |
| Author / approve guidelines | ✓ | ✓ | | | |
| Maintain approved facts | ✓ | ✓ | ✓ | | |
| Approve assets | ✓ | ✓ | | | |
| Submit content | ✓ | ✓ | ✓ | ✓ | ✓ |
| Decide reviews | ✓ | ✓ | ✓ | ✓ | |
| Approve critical findings | ✓ | | ✓ | | |
| Manage team / policy / workspace | ✓ | | | | |

## 5. Frontend structure

```
src/
  App.tsx              route table, AuthGuard, error boundary
  components/Shell.tsx sidebar, topbar, workspace switcher, notifications
  components/ui.tsx    design-system primitives (card, badge, table, modal, toast…)
  lib/api.ts           SDK wrappers: SQL, records, function runs, uploads, image hashing
  lib/session.tsx      one bootstrap per page load, memberships, active workspace, role
  lib/hooks.ts         SQL/row hooks with explicit refresh, bounded analysis watcher
  pages/               13 screens (dashboard, reviews, review detail, new review, guidelines,
                       facts, assets, approvals, analytics, insights, audit, team, settings,
                       quality)
```

Data discipline: reads happen once per dependency change through the hooks; the review
queue also subscribes to the datastore change stream so it stays fresh without polling. The
only polling is a bounded watcher (3 s interval, 4 min ceiling) on a *single* review while
its analysis is running — a deliberate exception to the no-polling rule, documented here.

## 6. Files

- `/brandguard/<workspace>/reviews|guidelines|assets` — uploads, converted to text by the
  platform when they are documents.
- `/brandguard/assets/*.png` — the seeded approved assets, generated deterministically by
  `bg_seed_workspace` with their perceptual hashes computed from the same pixels.
- `/brandguard/<workspace>/reports` — exported analytics reports.

Uploaded files are workspace-prefixed, validated by extension and size, and paths are
rejected if they are relative or contain traversal segments.
