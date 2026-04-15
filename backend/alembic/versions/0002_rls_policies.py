"""RLS policies

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-01 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE case_workspaces ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE case_memberships ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE evidence ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE derived_artifacts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE evidence FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY")

    op.execute("""
        CREATE POLICY case_member_select ON case_workspaces FOR SELECT
        USING (id IN (
            SELECT case_id FROM case_memberships
            WHERE user_id = current_setting('app.current_user_id', true)::uuid
              AND removed_at IS NULL
        ))
    """)
    op.execute("""
        CREATE POLICY membership_select ON case_memberships FOR SELECT
        USING (case_id IN (
            SELECT case_id FROM case_memberships cm2
            WHERE cm2.user_id = current_setting('app.current_user_id', true)::uuid
              AND cm2.removed_at IS NULL
        ))
    """)
    op.execute("""
        CREATE POLICY evidence_case_member ON evidence FOR ALL
        USING (case_id IN (
            SELECT case_id FROM case_memberships
            WHERE user_id = current_setting('app.current_user_id', true)::uuid
              AND removed_at IS NULL
        ))
    """)
    op.execute("""
        CREATE POLICY artifact_via_evidence ON derived_artifacts FOR ALL
        USING (evidence_id IN (SELECT id FROM evidence))
    """)
    op.execute("""
        CREATE POLICY audit_select ON audit_logs FOR SELECT
        USING (
            case_id IS NULL
            OR case_id IN (
                SELECT case_id FROM case_memberships
                WHERE user_id = current_setting('app.current_user_id', true)::uuid
                  AND removed_at IS NULL
            )
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS audit_select ON audit_logs")
    op.execute("DROP POLICY IF EXISTS artifact_via_evidence ON derived_artifacts")
    op.execute("DROP POLICY IF EXISTS evidence_case_member ON evidence")
    op.execute("DROP POLICY IF EXISTS membership_select ON case_memberships")
    op.execute("DROP POLICY IF EXISTS case_member_select ON case_workspaces")
    op.execute("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE evidence DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE derived_artifacts DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE case_memberships DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE case_workspaces DISABLE ROW LEVEL SECURITY")
