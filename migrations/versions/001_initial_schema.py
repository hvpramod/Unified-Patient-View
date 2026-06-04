"""Initial UPV schema

Revision ID: 001
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("azure_oid", sa.String(255), unique=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("role", sa.String(50), nullable=False, server_default="APC"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── patients ───────────────────────────────────────────────────────────
    op.create_table(
        "patients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("external_ids", JSONB, server_default="{}"),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("date_of_birth", sa.Date),
        sa.Column("gender", sa.String(20)),
        sa.Column("mrn", sa.String(100)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_patients_mrn", "patients", ["mrn"])

    # ── fhir_resources ─────────────────────────────────────────────────────
    op.create_table(
        "fhir_resources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("patient_id", UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=False),
        sa.Column("source_system", sa.String(50), nullable=False),
        sa.Column("source_version", sa.String(20), server_default="1"),
        sa.Column("fhir_version", sa.String(10), server_default="R4"),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("valid_from", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("valid_to", sa.TIMESTAMP(timezone=True)),
        sa.Column("ingested_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_fhir_patient_type", "fhir_resources", ["patient_id", "resource_type"])
    op.create_index("idx_fhir_source", "fhir_resources", ["source_system", "resource_id"])
    op.create_index("idx_fhir_hash", "fhir_resources", ["content_hash"])

    # ── conflicts ──────────────────────────────────────────────────────────
    op.create_table(
        "conflicts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("patient_id", UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("conflict_type", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50)),
        sa.Column("resource_ids", ARRAY(UUID(as_uuid=True))),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("auto_resolved", sa.Boolean, server_default="false"),
        sa.Column("resolution", JSONB),
        sa.Column("confidence_score", sa.Numeric(4, 3)),
        sa.Column("sources", JSONB),
        sa.Column("detected_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("idx_conflicts_patient", "conflicts", ["patient_id"])
    op.create_index("idx_conflicts_unresolved", "conflicts", ["patient_id", "auto_resolved"])

    # ── ai_summaries ───────────────────────────────────────────────────────
    op.create_table(
        "ai_summaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("patient_id", UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("summary_type", sa.String(50), nullable=False),
        sa.Column("model_used", sa.String(100)),
        sa.Column("model_version", sa.String(50)),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("sources", JSONB),
        sa.Column("confidence_score", sa.Numeric(4, 3)),
        sa.Column("reasoning_summary", sa.Text),
        sa.Column("input_hash", sa.String(64)),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("is_current", sa.Boolean, server_default="true"),
    )
    op.create_index("idx_summaries_patient_type_current", "ai_summaries", ["patient_id", "summary_type", "is_current"])

    # ── apc_actions ────────────────────────────────────────────────────────
    op.create_table(
        "apc_actions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("summary_id", UUID(as_uuid=True), sa.ForeignKey("ai_summaries.id")),
        sa.Column("conflict_id", UUID(as_uuid=True), sa.ForeignKey("conflicts.id")),
        sa.Column("recommendation_id", UUID(as_uuid=True)),
        sa.Column("action_type", sa.String(20), nullable=False),
        sa.Column("annotation", sa.Text),
        sa.Column("acted_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── audit_log ──────────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True)),
        sa.Column("actor_role", sa.String(50)),
        sa.Column("patient_id", UUID(as_uuid=True)),
        sa.Column("resource_type", sa.String(50)),
        sa.Column("resource_id", UUID(as_uuid=True)),
        sa.Column("payload", JSONB),
        sa.Column("source_ip", INET),
        sa.Column("session_id", UUID(as_uuid=True)),
        sa.Column("event_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_audit_patient", "audit_log", ["patient_id"])
    op.create_index("idx_audit_actor", "audit_log", ["actor_id"])
    op.create_index("idx_audit_event_at", "audit_log", ["event_at"])

    # ── clinical_guideline_chunks (pgvector RAG) ───────────────────────────
    op.create_table(
        "clinical_guideline_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("source_doc", sa.String(255)),
        sa.Column("chunk_index", sa.Integer),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("embedding", sa.Text),  # stored as text; cast to vector at query time
        sa.Column("metadata", JSONB),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── analytics view for Power BI ────────────────────────────────────────
    op.execute("""
        CREATE VIEW analytics_patient_summary AS
        SELECT
            p.id AS patient_id,
            p.gender,
            DATE_PART('year', AGE(p.date_of_birth)) AS age_years,
            COUNT(DISTINCT c.id) FILTER (WHERE c.resolved_at IS NULL) AS open_conflicts,
            COUNT(DISTINCT s.id) FILTER (WHERE s.summary_type = 'CLINICAL' AND s.is_current) AS has_clinical_summary,
            MAX(s.generated_at) AS last_summary_at
        FROM patients p
        LEFT JOIN conflicts c ON c.patient_id = p.id
        LEFT JOIN ai_summaries s ON s.patient_id = p.id
        GROUP BY p.id, p.gender, p.date_of_birth
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS analytics_patient_summary")
    op.drop_table("clinical_guideline_chunks")
    op.drop_table("audit_log")
    op.drop_table("apc_actions")
    op.drop_table("ai_summaries")
    op.drop_table("conflicts")
    op.drop_table("fhir_resources")
    op.drop_table("patients")
    op.drop_table("users")
