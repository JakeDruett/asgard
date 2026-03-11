"""
Heimdall Issue Tracker Service

Persists and manages tracked issues using a local SQLite database at
~/.asgard/issues.db.  Supports upsert (find-or-create with line-proximity
matching), lifecycle status transitions, assignment, commenting, and
git blame enrichment.
"""

import json
import sqlite3
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from Asgard.Heimdall.Issues.models.issue_models import (
    IssueFilter,
    IssueStatus,
    IssueSeverity,
    IssueType,
    IssuesSummary,
    TrackedIssue,
)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS issues (
    issue_id TEXT PRIMARY KEY,
    project_path TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    first_detected TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    resolved_at TEXT,
    false_positive_reason TEXT,
    assigned_to TEXT,
    git_blame_author TEXT,
    git_blame_commit TEXT,
    tags_json TEXT DEFAULT '[]',
    comments_json TEXT DEFAULT '[]',
    scan_count INTEGER DEFAULT 1
);
"""

_CREATE_IDX_PROJECT_SQL = "CREATE INDEX IF NOT EXISTS idx_issues_project ON issues(project_path);"
_CREATE_IDX_STATUS_SQL = "CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);"

_LINE_PROXIMITY = 5


def _row_to_issue(row: sqlite3.Row) -> TrackedIssue:
    """Convert a database row to a TrackedIssue model."""
    return TrackedIssue(
        issue_id=row["issue_id"],
        rule_id=row["rule_id"],
        issue_type=row["issue_type"],
        file_path=row["file_path"],
        line_number=row["line_number"],
        severity=row["severity"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        first_detected=datetime.fromisoformat(row["first_detected"]),
        last_seen=datetime.fromisoformat(row["last_seen"]),
        resolved_at=datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None,
        false_positive_reason=row["false_positive_reason"],
        assigned_to=row["assigned_to"],
        git_blame_author=row["git_blame_author"],
        git_blame_commit=row["git_blame_commit"],
        tags=json.loads(row["tags_json"] or "[]"),
        comments=json.loads(row["comments_json"] or "[]"),
        scan_count=row["scan_count"],
    )


class IssueTracker:
    """
    Manages persistent issue lifecycle tracking backed by a local SQLite database.

    The database is stored at ~/.asgard/issues.db by default and uses WAL mode
    for better concurrent-read performance.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or Path.home() / ".asgard" / "issues.db"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        """Create the issues table and indexes if they do not yet exist."""
        with self._get_connection() as conn:
            conn.execute(_CREATE_TABLE_SQL)
            conn.execute(_CREATE_IDX_PROJECT_SQL)
            conn.execute(_CREATE_IDX_STATUS_SQL)
            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Open and return a database connection with WAL mode enabled."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    # ------------------------------------------------------------------
    # Core issue operations
    # ------------------------------------------------------------------

    def upsert_issue(
        self,
        project_path: str,
        rule_id: str,
        file_path: str,
        line_number: int,
        issue_type: IssueType,
        severity: IssueSeverity,
        title: str,
        description: str,
    ) -> TrackedIssue:
        """
        Insert a new issue or update an existing matching issue.

        Matching is performed by (project_path, rule_id, file_path) where the
        stored line_number is within _LINE_PROXIMITY lines of the given
        line_number.  When a match is found, last_seen and scan_count are
        updated.  When no match is found, a new issue is created with a UUID.

        Args:
            project_path: Absolute path of the project root.
            rule_id: Rule identifier that produced the finding.
            file_path: Absolute path of the file containing the issue.
            line_number: Line number of the finding.
            issue_type: Classification of the issue type.
            severity: Severity level of the issue.
            title: Short descriptive title.
            description: Detailed description of the issue.

        Returns:
            The upserted TrackedIssue.
        """
        now_str = datetime.now().isoformat()
        issue_type_val = issue_type if isinstance(issue_type, str) else issue_type.value
        severity_val = severity if isinstance(severity, str) else severity.value

        with self._get_connection() as conn:
            # Search for existing issue within line proximity
            rows = conn.execute(
                """
                SELECT * FROM issues
                WHERE project_path = ?
                  AND rule_id = ?
                  AND file_path = ?
                  AND status NOT IN ('resolved', 'closed', 'false_positive', 'wont_fix')
                """,
                (project_path, rule_id, file_path),
            ).fetchall()

            existing = None
            for row in rows:
                if abs(row["line_number"] - line_number) <= _LINE_PROXIMITY:
                    existing = row
                    break

            if existing:
                conn.execute(
                    """
                    UPDATE issues
                    SET last_seen = ?, scan_count = scan_count + 1
                    WHERE issue_id = ?
                    """,
                    (now_str, existing["issue_id"]),
                )
                conn.commit()
                updated = conn.execute(
                    "SELECT * FROM issues WHERE issue_id = ?",
                    (existing["issue_id"],),
                ).fetchone()
                return _row_to_issue(updated)

            # Create new issue
            new_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO issues (
                    issue_id, project_path, rule_id, issue_type, file_path,
                    line_number, severity, title, description, status,
                    first_detected, last_seen, resolved_at, false_positive_reason,
                    assigned_to, git_blame_author, git_blame_commit,
                    tags_json, comments_json, scan_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, NULL, NULL, NULL, NULL, NULL, '[]', '[]', 1)
                """,
                (
                    new_id, project_path, rule_id, issue_type_val, file_path,
                    line_number, severity_val, title, description,
                    now_str, now_str,
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM issues WHERE issue_id = ?",
                (new_id,),
            ).fetchone()
            return _row_to_issue(row)

    def mark_resolved(self, project_path: str, scan_start_time: datetime) -> int:
        """
        Mark as resolved all open/confirmed issues not observed in the latest scan.

        Issues whose last_seen timestamp is before scan_start_time are assumed
        to have been fixed and are transitioned to 'resolved'.

        Args:
            project_path: The project whose issues should be evaluated.
            scan_start_time: The datetime the most recent scan began.

        Returns:
            Number of issues transitioned to resolved.
        """
        now_str = datetime.now().isoformat()
        scan_start_str = scan_start_time.isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE issues
                SET status = 'resolved', resolved_at = ?
                WHERE project_path = ?
                  AND status IN ('open', 'confirmed')
                  AND last_seen < ?
                """,
                (now_str, project_path, scan_start_str),
            )
            conn.commit()
            return cursor.rowcount

    def update_status(
        self,
        issue_id: str,
        new_status: IssueStatus,
        reason: Optional[str] = None,
    ) -> Optional[TrackedIssue]:
        """
        Transition an issue to a new lifecycle status.

        Args:
            issue_id: UUID of the issue to update.
            new_status: The target status.
            reason: Optional reason string (stored in false_positive_reason
                    when new_status is FALSE_POSITIVE).

        Returns:
            Updated TrackedIssue, or None if the issue_id was not found.
        """
        status_val = new_status if isinstance(new_status, str) else new_status.value
        now_str = datetime.now().isoformat()

        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM issues WHERE issue_id = ?",
                (issue_id,),
            ).fetchone()
            if not row:
                return None

            resolved_at = now_str if status_val in ("resolved", "closed") else row["resolved_at"]
            false_positive_reason = (
                reason
                if status_val == IssueStatus.FALSE_POSITIVE.value
                else row["false_positive_reason"]
            )

            conn.execute(
                """
                UPDATE issues
                SET status = ?, resolved_at = ?, false_positive_reason = ?
                WHERE issue_id = ?
                """,
                (status_val, resolved_at, false_positive_reason, issue_id),
            )
            conn.commit()
            updated = conn.execute(
                "SELECT * FROM issues WHERE issue_id = ?",
                (issue_id,),
            ).fetchone()
            return _row_to_issue(updated)

    def assign_issue(self, issue_id: str, assignee: str) -> Optional[TrackedIssue]:
        """
        Assign an issue to a user.

        Args:
            issue_id: UUID of the issue.
            assignee: Username or email to assign to.

        Returns:
            Updated TrackedIssue, or None if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE issues SET assigned_to = ? WHERE issue_id = ?",
                (assignee, issue_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            row = conn.execute(
                "SELECT * FROM issues WHERE issue_id = ?",
                (issue_id,),
            ).fetchone()
            return _row_to_issue(row)

    def add_comment(self, issue_id: str, comment: str) -> Optional[TrackedIssue]:
        """
        Append a comment to an issue.

        Args:
            issue_id: UUID of the issue.
            comment: Free-text comment to append.

        Returns:
            Updated TrackedIssue, or None if not found.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM issues WHERE issue_id = ?",
                (issue_id,),
            ).fetchone()
            if not row:
                return None
            existing_comments = json.loads(row["comments_json"] or "[]")
            existing_comments.append(comment)
            conn.execute(
                "UPDATE issues SET comments_json = ? WHERE issue_id = ?",
                (json.dumps(existing_comments), issue_id),
            )
            conn.commit()
            updated = conn.execute(
                "SELECT * FROM issues WHERE issue_id = ?",
                (issue_id,),
            ).fetchone()
            return _row_to_issue(updated)

    # ------------------------------------------------------------------
    # Query operations
    # ------------------------------------------------------------------

    def get_issues(
        self,
        project_path: str,
        issue_filter: Optional[IssueFilter] = None,
    ) -> List[TrackedIssue]:
        """
        Retrieve issues for a project with optional filtering.

        Args:
            project_path: The project root path to query.
            issue_filter: Optional filter criteria.

        Returns:
            List of matching TrackedIssue objects.
        """
        query = "SELECT * FROM issues WHERE project_path = ?"
        params: List = [project_path]

        if issue_filter:
            if issue_filter.status:
                placeholders = ",".join("?" for _ in issue_filter.status)
                values = [
                    s if isinstance(s, str) else s.value
                    for s in issue_filter.status
                ]
                query += f" AND status IN ({placeholders})"
                params.extend(values)

            if issue_filter.severity:
                placeholders = ",".join("?" for _ in issue_filter.severity)
                values = [
                    s if isinstance(s, str) else s.value
                    for s in issue_filter.severity
                ]
                query += f" AND severity IN ({placeholders})"
                params.extend(values)

            if issue_filter.issue_type:
                placeholders = ",".join("?" for _ in issue_filter.issue_type)
                values = [
                    t if isinstance(t, str) else t.value
                    for t in issue_filter.issue_type
                ]
                query += f" AND issue_type IN ({placeholders})"
                params.extend(values)

            if issue_filter.file_path_contains:
                query += " AND file_path LIKE ?"
                params.append(f"%{issue_filter.file_path_contains}%")

            if issue_filter.assigned_to:
                query += " AND assigned_to = ?"
                params.append(issue_filter.assigned_to)

            if issue_filter.rule_id:
                query += " AND rule_id = ?"
                params.append(issue_filter.rule_id)

        query += " ORDER BY first_detected DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [_row_to_issue(row) for row in rows]

    def get_summary(self, project_path: str) -> IssuesSummary:
        """
        Generate an aggregated summary of issues for a project.

        Args:
            project_path: The project root path.

        Returns:
            IssuesSummary with counts broken down by status, severity, and type.
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM issues WHERE project_path = ?",
                (project_path,),
            ).fetchall()

        summary = IssuesSummary(project_path=project_path)
        oldest: Optional[datetime] = None

        for row in rows:
            status = row["status"]
            severity = row["severity"]
            issue_type = row["issue_type"]

            if status == IssueStatus.OPEN.value:
                summary.total_open += 1
                summary.open_by_severity[severity] = summary.open_by_severity.get(severity, 0) + 1
                summary.open_by_type[issue_type] = summary.open_by_type.get(issue_type, 0) + 1
                first = datetime.fromisoformat(row["first_detected"])
                if oldest is None or first < oldest:
                    oldest = first

            elif status == IssueStatus.CONFIRMED.value:
                summary.total_confirmed += 1
                summary.open_by_severity[severity] = summary.open_by_severity.get(severity, 0) + 1
                summary.open_by_type[issue_type] = summary.open_by_type.get(issue_type, 0) + 1

            elif status == IssueStatus.FALSE_POSITIVE.value:
                summary.total_false_positives += 1

            elif status == IssueStatus.WONT_FIX.value:
                summary.total_wont_fix += 1

            elif status in (IssueStatus.RESOLVED.value, IssueStatus.CLOSED.value):
                summary.total_resolved += 1

        summary.oldest_open_issue = oldest
        return summary

    def get_issue(self, issue_id: str) -> Optional[TrackedIssue]:
        """
        Retrieve a single issue by its UUID.

        Args:
            issue_id: UUID of the issue.

        Returns:
            TrackedIssue if found, otherwise None.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM issues WHERE issue_id = ?",
                (issue_id,),
            ).fetchone()
            if not row:
                return None
            return _row_to_issue(row)

    # ------------------------------------------------------------------
    # Git blame enrichment
    # ------------------------------------------------------------------

    def get_git_blame(self, file_path: str, line_number: int) -> Optional[Dict[str, str]]:
        """
        Run git blame on a specific line to identify the author and commit.

        Args:
            file_path: Absolute path to the file.
            line_number: The 1-based line number to blame.

        Returns:
            Dict with 'author' and 'commit' keys, or None on failure.
        """
        try:
            result = subprocess.run(
                ["git", "blame", "-L", f"{line_number},{line_number}", "--porcelain", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return None
            output = result.stdout
            lines = output.splitlines()
            if not lines:
                return None

            commit_hash = lines[0].split()[0] if lines[0].split() else ""
            author = ""
            for line in lines[1:]:
                if line.startswith("author "):
                    author = line[len("author "):]
                    break

            if not commit_hash:
                return None

            return {"author": author, "commit": commit_hash}
        except (subprocess.SubprocessError, OSError, IndexError):
            return None
