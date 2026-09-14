"""sync_legacy_homeworks_data

Revision ID: 02205cd879ae
Revises: c3d4e5f6a7b8
Create Date: 2026-09-14 12:53:07.668985

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '02205cd879ae'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import re
import httpx
from alembic import op
import sqlalchemy as sa


def _extract_slug(link: str | None, slug: str | None) -> str | None:
    if slug and slug.strip():
        return slug.strip()
    if link and link.strip():
        link_clean = link.strip()
        match = re.search(r"/(?:homeworks|game|lessons)/([^/?#]+)", link_clean)
        if match:
            candidate = match.group(1).strip()
            if candidate.lower() in ("game", "homeworks", "coding") and "/lessons/" in link_clean:
                parts = [p for p in link_clean.split("?")[0].split("#")[0].split("/") if p]
                if len(parts) >= 2:
                    return parts[-2].strip()
            return candidate
        if link_clean.startswith("http://") or link_clean.startswith("https://"):
            candidate = link_clean.rstrip("/").split("/")[-1].split("?")[0].split("#")[0].strip()
            if candidate and len(candidate) > 1 and " " not in candidate:
                if candidate.lower() in ("game", "homeworks", "coding"):
                    parts = [p for p in link_clean.rstrip("/").split("/") if p]
                    if len(parts) >= 2:
                        return parts[-2].strip()
                return candidate
    return None


def upgrade() -> None:
    """Automatic legacy homework data sync & cleanup for production database."""
    bind = op.get_bind()

    # 1. Soft-delete old erroneous homework violations created by faulty fallback
    bind.execute(
        sa.text(
            "UPDATE violations SET is_deleted = true WHERE is_deleted = false AND (reason ILIKE '%bài tập%' OR reason ILIKE '%homework%')"
        )
    )

    # 2. Find legacy homeworks missing assignees & teams
    legacy_rows = bind.execute(
        sa.text(
            """
            SELECT id, link, slug FROM homeworks
            WHERE is_deleted = false
              AND id NOT IN (SELECT homework_id FROM homework_assignees WHERE is_deleted = false)
              AND id NOT IN (SELECT homework_id FROM homework_teams WHERE is_deleted = false)
            """
        )
    ).fetchall()

    if not legacy_rows:
        return

    # Base URL for Quiz API (read dynamically from app settings)
    try:
        from app.core.config import settings
        quiz_base_url = (getattr(settings, "QUIZ_API_URL", None) or "https://quiz.dutai.site").rstrip("/")
    except Exception:
        quiz_base_url = "https://quiz.dutai.site"

    for hw_id, link, slug in legacy_rows:
        candidate_slug = _extract_slug(link, slug)
        if not candidate_slug:
            continue

        legacy_uids: set[int] = set()
        headers = {"Content-Type": "application/json"}

        # Fetch coding submissions
        try:
            resp = httpx.get(
                f"{quiz_base_url}/api/v1/homeworks/{candidate_slug}/completed-members",
                headers=headers,
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                members = data.get("data", data) if isinstance(data, dict) else data
                if isinstance(members, list):
                    for m in members:
                        if isinstance(m, dict) and m.get("user_id"):
                            legacy_uids.add(int(m["user_id"]))
                        elif isinstance(m, (int, str)):
                            legacy_uids.add(int(m))
        except Exception:
            pass

        # Fetch game submissions
        try:
            resp = httpx.get(
                f"{quiz_base_url}/api/v1/game/{candidate_slug}/leaderboard",
                headers=headers,
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                members = data.get("data", data) if isinstance(data, dict) else data
                if isinstance(members, list):
                    for m in members:
                        if isinstance(m, dict) and m.get("user_id"):
                            legacy_uids.add(int(m["user_id"]))
                        elif isinstance(m, (int, str)):
                            legacy_uids.add(int(m))
        except Exception:
            pass

        if not legacy_uids:
            continue

        # Insert direct assignees into homework_assignees with homework's original created_at
        for uid in legacy_uids:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO homework_assignees (homework_id, user_id, is_deleted, created_at, updated_at)
                    SELECT :hw_id, :uid, false, created_at, NOW() FROM homeworks WHERE id = :hw_id
                    AND NOT EXISTS (
                        SELECT 1 FROM homework_assignees WHERE homework_id = :hw_id AND user_id = :uid AND is_deleted = false
                    )
                    """
                ),
                {"hw_id": hw_id, "uid": uid},
            )

        # Lookup team_ids for legacy_uids in team_members
        team_rows = bind.execute(
            sa.text(
                "SELECT DISTINCT team_id FROM team_members WHERE user_id IN :uids AND is_deleted = false"
            ).bindparams(sa.bindparam("uids", expanding=True)),
            {"uids": list(legacy_uids)},
        ).fetchall()

        # Insert team_ids into homework_teams with homework's original created_at
        for (tid,) in team_rows:
            if tid:
                bind.execute(
                    sa.text(
                        """
                        INSERT INTO homework_teams (homework_id, team_id, is_deleted, created_at, updated_at)
                        SELECT :hw_id, :tid, false, created_at, NOW() FROM homeworks WHERE id = :hw_id
                        AND NOT EXISTS (
                            SELECT 1 FROM homework_teams WHERE homework_id = :hw_id AND team_id = :tid AND is_deleted = false
                        )
                        """
                    ),
                    {"hw_id": hw_id, "tid": tid},
                )


def downgrade() -> None:
    """Downgrade schema."""
    pass

