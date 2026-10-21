# Known limitations

Honest status of what is and is not implemented. Nothing below is presented as working.

## Analysis

1. **No OCR.** The runtime has no OCR engine, so text embedded inside images is *not*
   read. The engine reports "no text extraction (this runtime has no OCR)" and the
   accessibility stage says text-in-image was not checked. Uploading a text-based document
   or pasting the text is the supported alternative.
2. **Visual comparison is a heuristic.** Logo/asset matching uses an 8×8 perceptual hash
   computed in the browser at upload time and stored on the asset; the engine compares
   hashes and dominant colours. A similarity score is evidence for review, not proof of
   brand compliance, and images whose hash cannot be compared are reported as *unverified*
   rather than non-compliant. Distortion, recolouring and typography checks that need pixel
   analysis are not implemented.
3. **Accessibility checks cover HTML markup only** (alt text presence, link text, heading
   order). Contrast, font size, reading order and full WCAG conformance are not evaluated,
   and the UI says so.
4. **Numeric comparison is unit-aware but literal.** Only values whose unit the engine can
   read unambiguously are compared; other facts are reported as not machine-comparable.
   Ranges ("3–5 days"), fractions ("half the price") and implicit comparisons are not
   evaluated numerically.
5. **Confidentiality detection is pattern-based.** It flags markers and identifiers; it
   cannot promise to find every piece of confidential material, and it says so in the
   finding.
6. **Confidence is an estimate.** Values come from the model and from rule strength; they
   are not calibrated probabilities. The UI labels them "estimate".
7. **The AI pass depends on the platform model.** If it is unavailable the run records the
   limitation, keeps the deterministic findings, and does not fabricate a clean result.

## Product

8. **No publishing integration.** BrandGuard AI records approvals; it never publishes.
   `auto_publish_enabled` exists in policy but is documented as not wired to any publisher,
   and no code path publishes content.
9. **Single-pod tenancy.** Workspaces are rows in one pod. Isolation is enforced on every
   function (ownership + membership) and verified by test, but a pod member who queries the
   datastore directly (outside the app) can see all rows, because the platform's row-level
   security granularity is per user, not per workspace. The app never exposes cross-workspace
   data.
10. **Team membership is by email.** A member is granted access by adding their email; the
    platform's own pod membership is the outer boundary. Suspending a membership blocks the
    app's checks but does not remove pod access.
11. **Comments are review-level.** Text-range anchoring stores offsets and is displayed as a
    range reference, but the UI does not render inline text-range threads.
12. **Retention is declarative.** The retention period is configurable and recorded, but no
    automated purge job runs; resetting a workspace (administrator) is the implemented
    deletion path.
13. **Notifications are in-app** (plus the platform's own inbox). No email or Slack
    delivery is configured.
14. **Guideline extraction quality varies with the document.** Extracted rules are drafts
    with their source quote and always require human approval; a poorly structured PDF may
    produce few or imprecise proposals, which the UI reports rather than hides.

## Test coverage

15. The suite covers the engine, workflow guards, permissions, isolation and analytics
    consistency against live fixtures. It does **not** measure general model accuracy: no
    precision/recall figure is quoted for the AI pass, because no labelled ground truth of
    sufficient size has been executed. The deterministic rules are exercised against known
    inputs and expected outcomes.
