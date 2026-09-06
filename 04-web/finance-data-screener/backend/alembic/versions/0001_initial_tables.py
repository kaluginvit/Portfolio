"""initial tables

Revision ID: 0001
Revises:
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", UUID(as_uuid=True), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("data", JSONB(), nullable=False),
    )

    op.create_table(
        "agent_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", UUID(as_uuid=True), sa.ForeignKey("datasets.id"), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("api_url", sa.Text(), nullable=True),
        sa.Column("fields_to_keep", JSONB(), nullable=True),
        sa.Column("filters", JSONB(), nullable=True),
        sa.Column("confidence", sa.String(20), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("plan_steps", JSONB(), nullable=True),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "audit_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("request_body", JSONB(), nullable=True),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # индексы для частых запросов
    op.create_index("ix_records_dataset_id", "records", ["dataset_id"])
    op.create_index("ix_agent_runs_dataset_id", "agent_runs", ["dataset_id"])
    op.create_index("ix_audit_runs_created_at", "audit_runs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_runs")
    op.drop_table("agent_runs")
    op.drop_table("records")
    op.drop_table("datasets")
