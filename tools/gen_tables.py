"""Generate the BrandGuard AI table bundle (tables/<name>/<name>.json)."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1] / "tables"

T = lambda **kw: {"type": "TEXT", **kw}
def E(name, options, **kw): return {"name": name, "type": "ENUM", "options": options, **kw}
def C(name, typ, **kw): return {"name": name, "type": typ, **kw}
def fk(col, ref, **kw): return {"name": col, "type": "UUID", "required": True, "foreign_key": {"references": ref}, **kw}

TABLES = {}

TABLES["bg_organizations"] = [
    C("name", "TEXT", required=True, max_length=200),
    C("slug", "TEXT", required=True, unique=True, max_length=80),
    C("description", "TEXT"),
    C("tone_summary", "TEXT"),
    C("primary_contact", "TEXT"),
    C("settings", "JSON"),
    C("is_active", "BOOLEAN", default=True),
]

TABLES["bg_memberships"] = [
    C("organization_id", "UUID", required=True),
    C("member_user_id", "UUID"),
    C("user_email", "TEXT", required=True, max_length=320),
    C("display_name", "TEXT"),
    C("role", "ENUM", required=True, options=["admin", "brand_manager", "creator", "reviewer", "compliance_reviewer"]),
    E("status", ["active", "invited", "suspended"], default="active"),
    C("invited_by", "TEXT"),
    C("notes", "TEXT"),
]

TABLES["bg_guidelines"] = [
    C("organization_id", "UUID", required=True),
    C("code", "TEXT", required=True, max_length=40),
    C("title", "TEXT", required=True, max_length=300),
    C("description", "TEXT"),
    E("category", ["tone", "terminology", "messaging", "factual_accuracy", "promotional_claim",
                   "visual_identity", "accessibility", "confidentiality", "legal_compliance", "formatting"], required=True),
    E("rule_type", ["prohibited_term", "required_term", "deprecated_term", "tone_rule", "messaging_rule",
                    "numeric_fact", "required_disclaimer", "claim_policy", "confidentiality_rule",
                    "visual_rule", "accessibility_rule", "formatting_rule"], required=True),
    E("severity", ["critical", "high", "medium", "low", "informational"], required=True),
    E("enforcement", ["mandatory", "recommended", "advisory"], required=True),
    C("rule_text", "TEXT", required=True),
    C("compliant_examples", "JSON"),
    C("noncompliant_examples", "JSON"),
    C("match_terms", "JSON"),
    C("source_document_id", "UUID"),
    C("source_section", "TEXT"),
    C("source_page", "INTEGER"),
    C("version", "INTEGER", default=1),
    E("status", ["draft", "pending_approval", "active", "archived"], default="draft"),
    C("created_by", "TEXT"),
    C("created_by_email", "TEXT"),
    C("approved_by", "TEXT"),
    C("approved_at", "DATETIME"),
    C("archived_at", "DATETIME"),
    C("notes", "TEXT"),
]

TABLES["bg_guideline_versions"] = [
    fk("guideline_id", "bg_guidelines.id"),
    C("version", "INTEGER", required=True),
    C("snapshot", "JSON"),
    C("change_summary", "TEXT"),
    C("changed_by", "TEXT"),
    C("changed_by_email", "TEXT"),
]

TABLES["bg_facts"] = [
    C("organization_id", "UUID", required=True),
    C("statement", "TEXT", required=True),
    E("category", ["product_specification", "price", "warranty", "discount", "availability",
                   "company_description", "marketing_statement", "certification", "promotional_claim",
                   "disclaimer", "other"], required=True),
    C("scope", "TEXT"),
    C("value_text", "TEXT"),
    C("numeric_value", "FLOAT"),
    C("unit", "TEXT"),
    C("match_keywords", "JSON"),
    C("source_document_id", "UUID"),
    C("source_location", "TEXT"),
    E("verification_status", ["verified", "pending", "rejected", "superseded", "no_evidence"],
      required=True, default="pending"),
    E("approval_status", ["approved", "pending", "rejected", "superseded"], default="pending"),
    C("effective_date", "DATE"),
    C("expiration_date", "DATE"),
    C("owner", "TEXT"),
    C("last_verified_at", "DATETIME"),
    C("version", "INTEGER", default=1),
    C("notes", "TEXT"),
]

TABLES["bg_fact_evidence"] = [
    fk("fact_id", "bg_facts.id"),
    E("evidence_type", ["lab_test", "certificate", "document", "internal_record", "external_source", "testimonial"]),
    C("title", "TEXT"),
    C("description", "TEXT"),
    C("source_document_id", "UUID"),
    C("source_location", "TEXT"),
    C("url", "TEXT"),
    E("strength", ["strong", "moderate", "weak", "unverified"]),
    C("added_by", "TEXT"),
]

TABLES["bg_assets"] = [
    C("organization_id", "UUID", required=True),
    C("name", "TEXT", required=True, max_length=200),
    E("category", ["logo", "logo_variant", "image", "campaign_image", "template", "font",
                   "brand_manual", "other"], required=True),
    C("file_path", "FILE_PATH", max_length=700),
    C("mime_type", "TEXT"),
    C("size_bytes", "INTEGER"),
    C("version", "INTEGER", default=1),
    E("approval_status", ["pending", "approved", "archived"], default="pending"),
    C("usage_restrictions", "TEXT"),
    C("guideline_id", "UUID"),
    C("dominant_colors", "JSON"),
    C("image_hash", "TEXT"),
    C("width", "INTEGER"),
    C("height", "INTEGER"),
    C("uploaded_by", "TEXT"),
    C("uploaded_by_email", "TEXT"),
    C("approved_by", "TEXT"),
    C("approved_at", "DATETIME"),
    C("notes", "TEXT"),
]

TABLES["bg_asset_versions"] = [
    fk("asset_id", "bg_assets.id"),
    C("version", "INTEGER", required=True),
    C("file_path", "FILE_PATH", max_length=700),
    C("change_summary", "TEXT"),
    C("replaced_by", "TEXT"),
    C("created_by", "TEXT"),
]

TABLES["bg_reviews"] = [
    C("organization_id", "UUID", required=True),
    C("title", "TEXT", required=True, max_length=300),
    E("content_type", ["social_post", "marketing_email", "advertisement", "blog_post",
                       "product_description", "landing_page", "promotional_banner",
                       "product_brochure", "marketing_document", "other"], required=True),
    C("campaign", "TEXT"),
    C("audience", "TEXT"),
    C("channel", "TEXT"),
    C("language", "TEXT", default="en"),
    C("context_notes", "TEXT"),
    C("source_text", "TEXT"),
    C("current_text", "TEXT"),
    E("status", ["draft", "submitted", "analysing", "analysis_failed", "awaiting_review",
                 "changes_requested", "resubmitted", "approved", "rejected", "archived"],
      required=True, default="draft"),
    E("risk_level", ["low", "medium", "high", "critical"]),
    C("current_version", "INTEGER", default=1),
    C("created_by", "TEXT"),
    C("created_by_email", "TEXT"),
    C("created_by_name", "TEXT"),
    C("assigned_reviewer_id", "UUID"),
    C("assigned_reviewer_email", "TEXT"),
    C("required_reviewer_role", "ENUM", options=["admin", "brand_manager", "reviewer", "compliance_reviewer"]),
    C("analysis_run_id", "UUID"),
    E("analysis_status", ["queued", "running", "completed", "failed"], default="queued"),
    C("submitted_at", "DATETIME"),
    C("decided_at", "DATETIME"),
    C("decision_reason", "TEXT"),
    C("model", "TEXT"),
    C("analysis_version", "TEXT"),
    C("attachment_paths", "JSON"),
    C("image_paths", "JSON"),
    C("error_message", "TEXT"),
    C("last_analysis_at", "DATETIME"),
    C("blocked_reason", "TEXT"),
]

TABLES["bg_review_versions"] = [
    fk("review_id", "bg_reviews.id"),
    C("version", "INTEGER", required=True),
    C("content", "TEXT"),
    C("change_summary", "TEXT"),
    E("change_source", ["original", "ai_correction", "manual_edit", "restore", "resubmission"]),
    C("author_id", "UUID"),
    C("author_email", "TEXT"),
    C("author_name", "TEXT"),
    C("findings_snapshot", "JSON"),
    C("is_approved", "BOOLEAN", default=False),
    C("approved_by", "TEXT"),
    C("approved_at", "DATETIME"),
]

TABLES["bg_segments"] = [
    fk("review_id", "bg_reviews.id"),
    C("seq", "INTEGER"),
    E("kind", ["text", "heading", "image", "file"]),
    C("content", "TEXT"),
    C("start_offset", "INTEGER"),
    C("end_offset", "INTEGER"),
    C("page", "INTEGER"),
    C("metadata", "JSON"),
]

TABLES["bg_analysis_runs"] = [
    fk("review_id", "bg_reviews.id"),
    C("version", "INTEGER"),
    E("status", ["queued", "running", "completed", "failed"], required=True, default="queued"),
    C("model", "TEXT"),
    C("analysis_version", "TEXT"),
    C("started_at", "DATETIME"),
    C("completed_at", "DATETIME"),
    C("error_message", "TEXT"),
    C("stats", "JSON"),
    C("findings_count", "INTEGER"),
    C("deterministic_count", "INTEGER"),
    C("ai_count", "INTEGER"),
    C("sources_used", "JSON"),
    C("triggered_by", "TEXT"),
]

TABLES["bg_findings"] = [
    C("organization_id", "UUID"),
    fk("review_id", "bg_reviews.id"),
    C("run_id", "UUID"),
    C("version", "INTEGER"),
    E("category", ["tone", "terminology", "messaging", "factual_accuracy", "promotional_claim",
                   "visual", "accessibility", "confidentiality", "formatting"], required=True),
    C("title", "TEXT", required=True),
    C("description", "TEXT"),
    E("severity", ["critical", "high", "medium", "low", "informational"], required=True),
    C("confidence", "FLOAT"),
    E("evidence_status", ["supported", "contradicted", "not_found", "expired", "ambiguous",
                          "stylistic", "unverified"], required=True),
    C("original_text", "TEXT"),
    C("location_start", "INTEGER"),
    C("location_end", "INTEGER"),
    C("location_excerpt", "TEXT"),
    C("location_page", "INTEGER"),
    C("rule_id", "UUID"),
    C("rule_code", "TEXT"),
    C("source_reference", "JSON"),
    C("explanation", "TEXT"),
    C("suggested_correction", "TEXT"),
    C("correction_rationale", "TEXT"),
    E("review_status", ["open", "accepted", "rejected", "resolved", "escalated", "wont_fix"], default="open"),
    C("resolved_by", "TEXT"),
    C("resolved_at", "DATETIME"),
    C("resolution_note", "TEXT"),
    E("detection_method", ["deterministic", "ai", "visual"], default="deterministic"),
    C("fingerprint", "TEXT", max_length=200),
    E("escalated_to_role", ["admin", "brand_manager", "reviewer", "compliance_reviewer"]),
]

TABLES["bg_corrections"] = [
    fk("finding_id", "bg_findings.id"),
    C("review_id", "UUID"),
    C("proposed_text", "TEXT"),
    C("rationale", "TEXT"),
    C("instructions", "TEXT"),
    E("status", ["proposed", "accepted", "rejected", "edited", "regenerated", "applied", "restored"],
      required=True, default="proposed"),
    E("source", ["ai", "human"], default="ai"),
    C("created_by", "TEXT"),
    C("applied_version", "INTEGER"),
    C("applied_at", "DATETIME"),
]

TABLES["bg_comments"] = [
    C("organization_id", "UUID"),
    fk("review_id", "bg_reviews.id"),
    C("finding_id", "UUID"),
    C("parent_id", "UUID"),
    C("author_id", "UUID"),
    C("author_email", "TEXT"),
    C("author_name", "TEXT"),
    C("body", "TEXT", required=True),
    C("range_start", "INTEGER"),
    C("range_end", "INTEGER"),
    C("is_resolved", "BOOLEAN", default=False),
    C("resolved_by", "TEXT"),
    C("resolved_at", "DATETIME"),
]

TABLES["bg_approvals"] = [
    C("organization_id", "UUID"),
    fk("review_id", "bg_reviews.id"),
    C("version", "INTEGER"),
    C("reviewer_id", "UUID"),
    C("reviewer_email", "TEXT"),
    C("reviewer_name", "TEXT"),
    E("required_role", ["admin", "brand_manager", "reviewer", "compliance_reviewer"]),
    E("kind", ["assignment", "decision"], default="assignment"),
    E("status", ["pending", "approved", "rejected", "changes_requested", "escalated", "skipped", "withdrawn"],
      default="pending"),
    C("reason", "TEXT"),
    C("is_override", "BOOLEAN", default=False),
    C("override_reason", "TEXT"),
    C("decided_at", "DATETIME"),
    C("created_by", "TEXT"),
]

TABLES["bg_audit_logs"] = [
    C("organization_id", "UUID"),
    C("actor_id", "UUID"),
    C("actor_email", "TEXT"),
    C("actor_name", "TEXT"),
    C("action", "TEXT", required=True, max_length=80),
    C("subject_type", "TEXT"),
    C("subject_id", "UUID"),
    C("summary", "TEXT"),
    C("metadata", "JSON"),
]

TABLES["bg_notifications"] = [
    C("organization_id", "UUID"),
    C("recipient_user_id", "UUID"),
    C("user_email", "TEXT"),
    C("title", "TEXT", required=True),
    C("body", "TEXT"),
    C("kind", "TEXT"),
    C("link_type", "TEXT"),
    C("link_id", "UUID"),
    C("is_read", "BOOLEAN", default=False),
]

TABLES["bg_insights"] = [
    C("organization_id", "UUID", required=True),
    E("insight_type", ["recurring_terminology", "recurring_claim", "guideline_ambiguity",
                       "asset_misuse", "high_revision_rate", "reviewer_disagreement",
                       "rejected_corrections", "insufficient_data"], required=True),
    C("title", "TEXT", required=True),
    C("description", "TEXT"),
    C("cases_count", "INTEGER"),
    C("total_count", "INTEGER"),
    C("period_start", "DATE"),
    C("period_end", "DATE"),
    C("supporting_review_ids", "JSON"),
    C("guideline_id", "UUID"),
    C("guideline_code", "TEXT"),
    C("recommended_action", "TEXT"),
    E("status", ["new", "investigating", "draft_created", "dismissed", "resolved"], default="new"),
    C("draft_guideline_id", "UUID"),
    C("confidence_note", "TEXT"),
    C("generated_at", "DATETIME"),
]

TABLES["bg_policies"] = [
    C("organization_id", "UUID", required=True, unique=True),
    C("require_separation_of_duties", "BOOLEAN", default=True),
    C("block_approval_on_mandatory", "BOOLEAN", default=True),
    C("critical_requires_compliance_reviewer", "BOOLEAN", default=True),
    C("high_risk_requires_second_reviewer", "BOOLEAN", default=False),
    C("ai_analysis_enabled", "BOOLEAN", default=True),
    C("external_ai_allowed", "BOOLEAN", default=True),
    C("confidential_content_to_external_ai", "BOOLEAN", default=False),
    C("auto_publish_enabled", "BOOLEAN", default=False),
    C("require_review_after_approved_edit", "BOOLEAN", default=True),
    C("retention_days", "INTEGER", default=365),
    C("ai_model", "TEXT"),
    C("analysis_version", "TEXT"),
    C("updated_by", "TEXT"),
]

TABLES["bg_documents"] = [
    C("organization_id", "UUID", required=True),
    C("title", "TEXT", required=True),
    E("kind", ["guideline_source", "fact_source", "evidence", "content_file", "asset_file", "policy"],
      required=True),
    C("file_path", "FILE_PATH", max_length=700),
    C("mime_type", "TEXT"),
    C("size_bytes", "INTEGER"),
    C("page_count", "INTEGER"),
    C("extracted_text", "TEXT"),
    E("extraction_status", ["pending", "extracted", "partial", "failed", "no_text"], default="pending"),
    C("extraction_note", "TEXT"),
    C("uploaded_by", "TEXT"),
    C("uploaded_by_email", "TEXT"),
    C("metadata", "JSON"),
]

TABLES["bg_ai_providers"] = [
    C("organization_id", "UUID", required=True),
    C("provider", "TEXT", required=True),
    C("model", "TEXT"),
    C("configured", "BOOLEAN", default=False),
    C("is_default", "BOOLEAN", default=False),
    C("status_note", "TEXT"),
    C("data_flow_note", "TEXT"),
    C("last_checked_at", "DATETIME"),
]

def main():
    for name, cols in TABLES.items():
        d = ROOT / name
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.json").write_text(json.dumps(
            {"name": name, "primary_key_column": "id", "enable_rls": False, "columns": cols},
            indent=2) + "\n")
    print(f"wrote {len(TABLES)} tables")

if __name__ == "__main__":
    main()
