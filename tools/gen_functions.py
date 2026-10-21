"""Generate function manifests (functions/<name>/<name>.json) with explicit grants."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1] / "functions"


def t(name, write=False):
    perms = ["datastore.table.read", "datastore.record.read"]
    if write:
        perms.append("datastore.record.write")
    return {"resource_type": "datastore_table", "resource_name": name, "permission_ids": perms}


def folder(path, write=False):
    return {"resource_type": "folder", "resource_name": path,
            "permission_ids": ["folder.read", "folder.write"] if write else ["folder.read"]}


def agent(name):
    return {"resource_type": "agent", "resource_name": name, "permission_ids": ["agent.execute"]}


def fn(name):
    return {"resource_type": "function", "resource_name": name, "permission_ids": ["function.execute"]}


BG_TABLES = ["bg_organizations", "bg_memberships", "bg_policies", "bg_ai_providers", "bg_guidelines",
             "bg_guideline_versions", "bg_facts", "bg_fact_evidence", "bg_assets", "bg_asset_versions",
             "bg_reviews", "bg_review_versions", "bg_segments", "bg_analysis_runs", "bg_findings",
             "bg_corrections", "bg_comments", "bg_approvals", "bg_audit_logs", "bg_notifications",
             "bg_insights", "bg_documents"]

SPECS = {
    "bg_bootstrap": {
        "description": "Ensure the invoking user has a workspace membership, default governance policy and AI-provider disclosure records. Idempotent.",
        "type": "API", "grants": [t("bg_organizations", True), t("bg_memberships", True), t("bg_policies", True), t("bg_ai_providers", True)],
    },
    "bg_policy_update": {
        "description": "Update the workspace governance policy (approval requirements, AI data flow, retention). Administrator only.",
        "type": "API", "grants": [t("bg_policies", True), t("bg_organizations"), t("bg_memberships"), t("bg_audit_logs", True)],
    },
    "bg_guideline_action": {
        "description": "Create, edit, approve, archive and version brand guideline rules with server-side role checks.",
        "type": "API", "grants": [t("bg_guidelines", True), t("bg_guideline_versions", True), t("bg_memberships"), t("bg_audit_logs", True), t("bg_policies"), t("bg_documents")],
    },
    "bg_fact_action": {
        "description": "Maintain the approved facts and claims library, including evidence records and verification decisions.",
        "type": "API", "grants": [t("bg_facts", True), t("bg_fact_evidence", True), t("bg_memberships"), t("bg_audit_logs", True), t("bg_documents")],
    },
    "bg_asset_action": {
        "description": "Register approved assets (logo variants, images, templates), analyse them, approve, replace with a new version or archive.",
        "type": "API", "grants": [t("bg_assets", True), t("bg_asset_versions", True), t("bg_memberships"), t("bg_audit_logs", True), folder("/brandguard")],
    },
    "bg_document_ingest": {
        "description": "Register an uploaded pod file as a BrandGuard document and extract its text (PDF/DOCX/MD/TXT converted by the platform).",
        "type": "API", "grants": [t("bg_documents", True), t("bg_memberships"), t("bg_audit_logs", True), folder("/brandguard")],
    },
    "bg_guideline_extract": {
        "description": "Propose draft guideline rules from an uploaded brand document. Proposals are never authoritative until a human approves them.",
        "type": "JOB", "grants": [t("bg_documents"), t("bg_guidelines", True), t("bg_guideline_versions", True), t("bg_memberships"), t("bg_audit_logs", True), agent("brandguard-guideline-extractor")],
    },
    "bg_review_create": {
        "description": "Create a content review: validates input, extracts attached documents, stores version 1 and its segments, records the submission.",
        "type": "API", "grants": [t("bg_reviews", True), t("bg_review_versions", True), t("bg_segments", True), t("bg_documents", True), t("bg_memberships"), t("bg_audit_logs", True), t("bg_notifications", True), folder("/brandguard")],
    },
    "bg_review_analyse": {
        "description": "Brand compliance engine: deterministic rule checks, visual checks, evidence retrieval and an evidence-grounded AI pass, reconciled into stored findings.",
        "type": "JOB", "grants": [t("bg_reviews", True), t("bg_review_versions"), t("bg_segments", True), t("bg_analysis_runs", True), t("bg_findings", True), t("bg_guidelines"), t("bg_facts"), t("bg_fact_evidence"), t("bg_assets"), t("bg_policies"), t("bg_organizations"), t("bg_memberships"), t("bg_audit_logs", True), t("bg_notifications", True), t("bg_documents"), t("bg_corrections", True), agent("brandguard-analyst"), folder("/brandguard")],
    },
    "bg_correction_action": {
        "description": "Correction assistant: regenerate a suggested correction, accept/reject/edit it, apply it as a new version and validate the result on re-scan.",
        "type": "JOB", "grants": [t("bg_findings", True), t("bg_corrections", True), t("bg_reviews", True), t("bg_review_versions", True), t("bg_memberships"), t("bg_audit_logs", True), t("bg_guidelines"), t("bg_analysis_runs", True), agent("brandguard-analyst")],
    },
    "bg_review_workflow": {
        "description": "Human approval workflow: submit, assign, request changes, resubmit, approve, reject, escalate, archive and override, with policy guards and audit records.",
        "type": "API", "grants": [t("bg_reviews", True), t("bg_review_versions", True), t("bg_findings", True), t("bg_approvals", True), t("bg_policies"), t("bg_guidelines"), t("bg_memberships"), t("bg_audit_logs", True), t("bg_notifications", True), t("bg_corrections", True), t("bg_analysis_runs")],
    },
    "bg_comment_action": {
        "description": "Collaboration: add a comment or reply, resolve or reopen a thread, with workspace-scoped permission checks.",
        "type": "API", "grants": [t("bg_comments", True), t("bg_reviews"), t("bg_memberships"), t("bg_audit_logs", True), t("bg_notifications", True)],
    },
    "bg_insights_generate": {
        "description": "Governance memory: compute recurring-problem and guideline-gap insights from actual review history and persist them with their supporting records.",
        "type": "API", "grants": [t("bg_insights", True), t("bg_findings"), t("bg_reviews"), t("bg_guidelines", True), t("bg_guideline_versions", True), t("bg_corrections"), t("bg_approvals"), t("bg_assets"), t("bg_memberships"), t("bg_audit_logs", True)],
    },
    "bg_team_action": {
        "description": "Workspace membership management (invite, change role, suspend, remove) with administrator-only checks and audit records.",
        "type": "API", "grants": [t("bg_memberships", True), t("bg_audit_logs", True), t("bg_notifications", True), t("bg_reviews"), t("bg_organizations")],
    },
    "bg_workspace_action": {
        "description": "Create or update a workspace and its brand profile (name, tone, brand colours). Administrator only for changes.",
        "type": "API", "grants": [t("bg_organizations", True), t("bg_memberships", True), t("bg_policies", True), t("bg_audit_logs", True)],
    },
    "bg_seed_workspace": {
        "description": "Provision a workspace with brand guidelines, approved facts, approved assets and review history (idempotent; administrator only).",
        "type": "API", "grants": [t(x, True) for x in BG_TABLES] + [folder("/brandguard", True)],
    },
    "bg_eval_run": {
        "description": "Reliability and evaluation harness: exercises the real pipeline (state machine, permissions, workspace isolation, ingestion, evidence handling) and reports measured results.",
        "type": "JOB", "grants": [t("bg_reviews", True), t("bg_review_versions", True), t("bg_segments", True), t("bg_findings"), t("bg_analysis_runs"), t("bg_guidelines"), t("bg_facts"), t("bg_policies"), t("bg_memberships"), t("bg_documents", True), t("bg_audit_logs", True), t("bg_organizations"), fn("bg_review_workflow"), fn("bg_document_ingest"), fn("bg_review_create"), folder("/brandguard")],
    },
}


def main():
    missing = []
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        if not (d / "code.py").exists():
            missing.append(name)
            continue
        spec = SPECS.get(name)
        if spec is None:
            print(f"!! no spec for {name}", file=sys.stderr)
            continue
        (d / f"{name}.json").write_text(json.dumps({
            "name": name, "description": spec["description"], "type": spec["type"],
            "visibility": "POD", "code": {"$file": "code.py"},
            "permissions": {"grants": spec["grants"]},
        }, indent=2) + "\n")
    if missing:
        print("functions without code.py:", missing, file=sys.stderr)
    print(f"manifests written for {len(SPECS)} functions")


if __name__ == "__main__":
    main()
