"""Initial CTF schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-20 17:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("nationality", sa.String(length=10), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_connected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_active_role_score", "users", ["is_active", "role", "score"], unique=False)

    op.create_table(
        "challenges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("flag", sa.String(length=255), nullable=False),
        sa.Column("flag_hash", sa.String(length=64), nullable=True),
        sa.Column("target_url", sa.String(length=255), nullable=True),
        sa.Column("hints", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("repository", sa.String(length=255), nullable=True),
        sa.Column("path", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("solves_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_challenges_id", "challenges", ["id"], unique=False)
    op.create_index("ix_challenges_slug", "challenges", ["slug"], unique=True)
    op.create_index(
        "ix_challenges_active_category_difficulty",
        "challenges",
        ["is_active", "category", "difficulty"],
        unique=False,
    )

    op.create_table(
        "solves",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("challenge_id", sa.String(length=36), nullable=False),
        sa.Column("points_awarded", sa.Integer(), nullable=False),
        sa.Column("solved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "challenge_id", name="uq_user_challenge_solve"),
    )
    op.create_index("ix_solves_id", "solves", ["id"], unique=False)
    op.create_index("ix_solves_user_id", "solves", ["user_id"], unique=False)
    op.create_index("ix_solves_challenge_id", "solves", ["challenge_id"], unique=False)
    op.create_index("ix_solves_user_solved_at", "solves", ["user_id", "solved_at"], unique=False)

    op.create_table(
        "submissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("challenge_id", sa.String(length=36), nullable=False),
        sa.Column("submitted_flag", sa.String(length=255), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_submissions_id", "submissions", ["id"], unique=False)
    op.create_index("ix_submissions_user_id", "submissions", ["user_id"], unique=False)
    op.create_index("ix_submissions_challenge_id", "submissions", ["challenge_id"], unique=False)
    op.create_index(
        "ix_submissions_user_challenge_submitted",
        "submissions",
        ["user_id", "challenge_id", "submitted_at"],
        unique=False,
    )

    op.create_table(
        "challenge_instances",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("challenge_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiration_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_challenge_instances_id", "challenge_instances", ["id"], unique=False)
    op.create_index("ix_challenge_instances_user_id", "challenge_instances", ["user_id"], unique=False)
    op.create_index("ix_challenge_instances_challenge_id", "challenge_instances", ["challenge_id"], unique=False)
    op.create_index(
        "ix_instance_user_challenge_status",
        "challenge_instances",
        ["user_id", "challenge_id", "status"],
        unique=False,
    )

    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("jti"),
    )
    op.create_index("ix_revoked_tokens_jti", "revoked_tokens", ["jti"], unique=False)
    op.create_index("ix_revoked_tokens_expires_at", "revoked_tokens", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_revoked_tokens_expires_at", table_name="revoked_tokens")
    op.drop_index("ix_revoked_tokens_jti", table_name="revoked_tokens")
    op.drop_table("revoked_tokens")

    op.drop_index("ix_instance_user_challenge_status", table_name="challenge_instances")
    op.drop_index("ix_challenge_instances_challenge_id", table_name="challenge_instances")
    op.drop_index("ix_challenge_instances_user_id", table_name="challenge_instances")
    op.drop_index("ix_challenge_instances_id", table_name="challenge_instances")
    op.drop_table("challenge_instances")

    op.drop_index("ix_submissions_user_challenge_submitted", table_name="submissions")
    op.drop_index("ix_submissions_challenge_id", table_name="submissions")
    op.drop_index("ix_submissions_user_id", table_name="submissions")
    op.drop_index("ix_submissions_id", table_name="submissions")
    op.drop_table("submissions")

    op.drop_index("ix_solves_user_solved_at", table_name="solves")
    op.drop_index("ix_solves_challenge_id", table_name="solves")
    op.drop_index("ix_solves_user_id", table_name="solves")
    op.drop_index("ix_solves_id", table_name="solves")
    op.drop_table("solves")

    op.drop_index("ix_challenges_active_category_difficulty", table_name="challenges")
    op.drop_index("ix_challenges_slug", table_name="challenges")
    op.drop_index("ix_challenges_id", table_name="challenges")
    op.drop_table("challenges")

    op.drop_index("ix_users_active_role_score", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
