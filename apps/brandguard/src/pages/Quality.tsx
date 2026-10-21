import React, { useState } from 'react'
import { CheckCircle2, CircleDashed, FlaskConical, PlayCircle, XCircle } from 'lucide-react'
import { useSession } from '../lib/session'
import { runFn, Row } from '../lib/api'
import { Badge, Button, Card, CardHead, Empty, Loading, useToast } from '../components/ui'
import { fmtDateTime } from '../lib/types'

type Check = { name: string; expectation: string; actual: string; outcome: string; detail?: string }

const DATASET: { id: string; label: string; input: string; reference: string; expected: string; evidence: string }[] = [
  { id: 'E1', label: 'Correct content', input: 'The Northstar AirPure 300 filters rooms up to 60 m² and carries a one-year limited warranty. Recommended retail price: $499.',
    reference: 'Approved spec + price + warranty facts', expected: 'No material findings (formatting advisories allowed)', evidence: 'supported' },
  { id: 'E2', label: 'Tone violation', input: 'WOW!!! You will totally LOVE this AMAZING revolutionary product!!!',
    reference: 'TONE-001 (mandatory) and FMT-001 (advisory)', expected: 'Tone finding, medium or lower; no critical finding', evidence: 'stylistic' },
  { id: 'E3', label: 'Terminology violation', input: 'The PureAir Pro is available now.',
    reference: 'TERM-001 prohibited term + approved replacement', expected: 'Terminology finding citing TERM-001 with a replacement', evidence: 'supported' },
  { id: 'E4', label: 'Contradicted product fact', input: 'Every customer receives a three-year warranty on the AirPure Pro.',
    reference: 'Approved warranty fact: one year', expected: 'Factual accuracy finding marked contradicted', evidence: 'contradicted' },
  { id: 'E5', label: 'Unsupported claim', input: 'It is guaranteed to be the best on the market.',
    reference: 'CLAIM-001 requires an evidence record', expected: 'Promotional claim finding marked not_found (not contradicted)', evidence: 'not_found' },
  { id: 'E6', label: 'Expired reference fact', input: 'Northstar Living was founded in 2011.',
    reference: 'Founding fact expired 2024-12-31', expected: 'Factual accuracy finding marked expired', evidence: 'expired' },
  { id: 'E7', label: 'Ambiguous claim', input: 'A purifier the whole family can rely on.',
    reference: 'No matching approved fact', expected: 'Either no finding, or an ambiguous/unverified one — never a fabricated contradiction', evidence: 'ambiguous' },
  { id: 'E8', label: 'Health claim with no evidence', input: 'It removes 99.9% of airborne viruses so your family never gets sick.',
    reference: 'CLAIM-002; claim rejected in the claims register', expected: 'Critical promotional claim finding, escalated to compliance', evidence: 'not_found' },
  { id: 'E9', label: 'Confidential material', input: 'INTERNAL ONLY — do not distribute outside the partner programme.',
    reference: 'CONF-001 confidentiality rule', expected: 'Confidentiality finding, ambiguous (a human confirms)', evidence: 'ambiguous' },
  { id: 'E10', label: 'Accessibility issue', input: '<img src="banner.png"><a href="#">click here</a>',
    reference: 'A11Y-001', expected: 'Accessibility findings for missing alt text and vague link text', evidence: 'supported' },
  { id: 'E11', label: 'Corrected content', input: 'Meet the Northstar AirPure 300. It filters rooms up to 60 m² and comes with a one-year limited warranty.',
    reference: 'TERM-001 replacement applied', expected: 'Previously resolved terminology finding stays resolved after re-scan', evidence: 'supported' },
]

export function Quality() {
  const session = useSession()
  const toast = useToast()
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<Row | null>(null)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    setRunning(true)
    setError(null)
    const res = await runFn('bg_eval_run', { organization_id: session.activeOrg?.id })
    setRunning(false)
    if (!res.ok) { setError(res.error ?? 'The harness could not run.'); return }
    setResult(res.output)
    toast.push('Reliability checks executed against the live workspace.', 'success')
  }

  const checks: Check[] = result?.checks ?? []

  return (
    <div className="stack">
      <div className="row">
        <div>
          <h1>Quality &amp; evaluation</h1>
          <p className="muted small" style={{ margin: 0 }}>
            What has actually been executed, not what is claimed. Every check below runs the real pipeline.
          </p>
        </div>
        <div className="spacer" />
        <Button variant="primary" disabled={running} onClick={run}>
          {running ? <span className="spinner" aria-hidden="true" /> : <PlayCircle size={15} />} Run reliability checks
        </Button>
      </div>

      {error ? <div className="err">{error}</div> : null}

      <Card>
        <CardHead title="Live reliability results"
          subtitle={result ? `Executed ${fmtDateTime(result.executed_at)} · ${result.passed} passed, ${result.failed} failed, ${result.skipped} skipped` : 'Not run yet in this session'} />
        {running ? <Loading label="Executing checks against the live workspace…" /> : !result ? (
          <Empty title="No results yet"
            hint="Run the harness to exercise workflow guards, permission boundaries, workspace isolation, ingestion and evidence handling." />
        ) : (
          <div className="table-wrap">
            <table aria-label="Reliability checks">
              <thead><tr><th>Outcome</th><th>Check</th><th>Expected</th><th>Observed</th><th>Detail</th></tr></thead>
              <tbody>
                {checks.map((c) => (
                  <tr key={c.name}>
                    <td>
                      <Badge tone={c.outcome === 'passed' ? 'b-ok' : c.outcome === 'failed' ? 'b-critical' : 'b-info'}>
                        {c.outcome === 'passed' ? <CheckCircle2 size={11} /> : c.outcome === 'failed' ? <XCircle size={11} /> : <CircleDashed size={11} />}
                        {c.outcome}
                      </Badge>
                    </td>
                    <td className="small" style={{ fontWeight: 560 }}>{c.name}</td>
                    <td className="small muted">{c.expectation}</td>
                    <td className="small mono">{c.actual}</td>
                    <td className="small muted">{c.detail ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {result ? <div style={{ padding: 16 }} className="muted small">{result.note}</div> : null}
      </Card>

      <Card>
        <CardHead title="Labelled compliance dataset"
          subtitle="Each case names the approved reference material, the expected finding and the expected evidence status" />
        <div className="table-wrap">
          <table aria-label="Evaluation dataset">
            <thead><tr><th>Case</th><th>Input</th><th>Approved reference</th><th>Expected finding</th><th>Expected evidence status</th></tr></thead>
            <tbody>
              {DATASET.map((c) => (
                <tr key={c.id}>
                  <td><Badge tone="b-accent">{c.id}</Badge><div className="small" style={{ fontWeight: 560 }}>{c.label}</div></td>
                  <td className="small" style={{ maxWidth: 300 }}>{c.input}</td>
                  <td className="small muted" style={{ maxWidth: 240 }}>{c.reference}</td>
                  <td className="small">{c.expected}</td>
                  <td><Badge tone="b-info">{c.evidence}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ padding: 16 }} className="small muted">
          <FlaskConical size={14} /> These cases are the reference for the compliance engine. Cases E2–E10 are also
          exercised as real reviews in the workspace, so the stored findings can be compared against the expectations
          above — no accuracy percentage is quoted unless it was measured from executed runs.
        </div>
      </Card>
    </div>
  )
}
