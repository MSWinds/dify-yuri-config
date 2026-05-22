import argparse
import os
import socket
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DOCKER_ENV_PATH = REPO_ROOT / "docker" / ".env"
API_DIR = REPO_ROOT / "api"


def setup_environment() -> None:
    if DOCKER_ENV_PATH.exists() and load_dotenv:
        load_dotenv(DOCKER_ENV_PATH)

    db_host = os.environ.get("DB_HOST")
    if db_host == "db_postgres":
        try:
            socket.gethostbyname("db_postgres")
        except socket.gaierror:
            os.environ["DB_HOST"] = "localhost"
            os.environ["REDIS_HOST"] = "localhost"
            broker_url = os.environ.get("CELERY_BROKER_URL", "")
            if broker_url:
                os.environ["CELERY_BROKER_URL"] = broker_url.replace("redis:6379", "localhost:6379")

            log_file = os.environ.get("LOG_FILE", "")
            if log_file.startswith("/app/"):
                local_log_path = API_DIR / log_file.replace("/app/", "", 1)
                local_log_path.parent.mkdir(parents=True, exist_ok=True)
                os.environ["LOG_FILE"] = str(local_log_path)

    if not os.environ.get("OPENDAL_FS_ROOT"):
        os.environ["OPENDAL_FS_ROOT"] = str(API_DIR / "storage")

    for key in ("DEBUG", "FLASK_DEBUG"):
        value = os.environ.get(key)
        if value and value.lower() in {"release", "prod", "production"}:
            os.environ[key] = "false"

    sys.path.append(str(API_DIR))


setup_environment()

from app import create_app  # noqa: E402
from extensions.ext_database import db  # noqa: E402


DETAILS_QUERY = text(
    """
    WITH workflow_source AS (
        SELECT
            a.id AS app_id,
            a.name AS app_name,
            acc.name AS owner_name,
            acc.email AS owner_email,
            w.id AS workflow_id,
            w.created_at,
            extract(epoch FROM w.created_at) * 1000 AS created_ms,
            (w.graph)::jsonb AS graph
        FROM apps a
        JOIN accounts acc ON acc.id = a.created_by
        JOIN workflows w ON w.app_id = a.id
        WHERE a.mode IN ('workflow', 'advanced-chat')
    ),
    latest_workflow AS (
        SELECT DISTINCT ON (app_id)
            app_id,
            app_name,
            owner_name,
            owner_email,
            workflow_id,
            created_at,
            created_ms,
            graph
        FROM workflow_source
        ORDER BY app_id, created_at DESC
    ),
    selected_workflows AS (
        SELECT * FROM workflow_source
        WHERE NOT :latest_only
        UNION ALL
        SELECT * FROM latest_workflow
        WHERE :latest_only
    ),
    node_scan AS (
        SELECT
            sw.app_id,
            sw.app_name,
            sw.owner_name,
            sw.owner_email,
            sw.workflow_id,
            sw.created_at,
            sw.created_ms,
            node ->> 'id' AS node_id,
            CASE
                WHEN node ->> 'id' ~ '^[0-9]{13,}$' THEN (node ->> 'id')::numeric
                ELSE NULL
            END AS numeric_node_id,
            node -> 'position' AS position
        FROM selected_workflows sw
        CROSS JOIN LATERAL jsonb_array_elements(sw.graph -> 'nodes') AS node
    )
    SELECT
        owner_name,
        owner_email,
        app_name,
        workflow_id,
        created_at,
        COUNT(*) AS node_count,
        MIN(numeric_node_id) AS min_numeric_id,
        MAX(numeric_node_id) AS max_numeric_id,
        BOOL_AND(node_id ~ '^[0-9]{13,}$') AS all_numeric_ids,
        (
            MAX(numeric_node_id) - MIN(numeric_node_id) + 1
            = COUNT(*) FILTER (WHERE numeric_node_id IS NOT NULL)
        ) AS exact_plus_one_sequence,
        BOOL_AND(
            (position ->> 'x') ~ '^-?[0-9]+(?:\\.0+)?$'
            AND (position ->> 'y') ~ '^-?[0-9]+(?:\\.0+)?$'
        ) AS all_integer_coords,
        BOOL_AND(numeric_node_id > created_ms + 2592000000)
            FILTER (WHERE numeric_node_id IS NOT NULL) AS future30_ids
    FROM node_scan
    GROUP BY owner_name, owner_email, app_name, workflow_id, created_at, created_ms
    HAVING
        BOOL_AND(node_id ~ '^[0-9]{13,}$')
        AND COUNT(*) > 2
        AND (
            MAX(numeric_node_id) - MIN(numeric_node_id) + 1
            = COUNT(*) FILTER (WHERE numeric_node_id IS NOT NULL)
        )
    ORDER BY future30_ids DESC, created_at DESC, owner_email, app_name
    """
)


@dataclass
class Finding:
    owner_name: str
    owner_email: str
    app_name: str
    workflow_id: str
    created_at: datetime
    node_count: int
    min_numeric_id: int
    max_numeric_id: int
    all_integer_coords: bool
    future30_ids: bool


def format_bool(value: bool) -> str:
    return "yes" if value else "no"


def print_table(headers: list[str], rows: list[list[object]]) -> None:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(str(cell)))

    header_line = " | ".join(str(header).ljust(widths[index]) for index, header in enumerate(headers))
    separator = "-+-".join("-" * width for width in widths)
    print(header_line)
    print(separator)
    for row in rows:
        print(" | ".join(str(cell).ljust(widths[index]) for index, cell in enumerate(row)))


def fetch_findings(latest_only: bool) -> list[Finding]:
    rows = db.session.execute(DETAILS_QUERY, {"latest_only": latest_only}).mappings().all()
    findings: list[Finding] = []
    for row in rows:
        findings.append(
            Finding(
                owner_name=row["owner_name"] or "",
                owner_email=row["owner_email"],
                app_name=row["app_name"],
                workflow_id=str(row["workflow_id"]),
                created_at=row["created_at"],
                node_count=int(row["node_count"]),
                min_numeric_id=int(row["min_numeric_id"]),
                max_numeric_id=int(row["max_numeric_id"]),
                all_integer_coords=bool(row["all_integer_coords"]),
                future30_ids=bool(row["future30_ids"]),
            )
        )
    return findings


def summarize(findings: list[Finding]) -> list[list[object]]:
    summary: dict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {
            "workflow_count": 0,
            "app_names": set(),
            "future30_count": 0,
            "integer_grid_count": 0,
        }
    )

    for finding in findings:
        key = (finding.owner_name, finding.owner_email)
        summary[key]["workflow_count"] += 1
        summary[key]["app_names"].add(finding.app_name)
        if finding.future30_ids:
            summary[key]["future30_count"] += 1
        if finding.all_integer_coords:
            summary[key]["integer_grid_count"] += 1

    rows: list[list[object]] = []
    for (owner_name, owner_email), stats in sorted(
        summary.items(),
        key=lambda item: (-int(item[1]["workflow_count"]), item[0][1]),
    ):
        rows.append(
            [
                owner_name or "(no name)",
                owner_email,
                stats["workflow_count"],
                len(stats["app_names"]),
                stats["future30_count"],
                stats["integer_grid_count"],
            ]
        )
    return rows


def detail_rows(findings: list[Finding]) -> list[list[object]]:
    return [
        [
            finding.owner_email,
            finding.app_name,
            finding.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            finding.node_count,
            finding.min_numeric_id,
            finding.max_numeric_id,
            format_bool(finding.all_integer_coords),
            format_bool(finding.future30_ids),
            finding.workflow_id,
        ]
        for finding in findings
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit workflows whose numeric node IDs form an exact +1 consecutive sequence."
    )
    parser.add_argument(
        "--latest-only",
        action="store_true",
        help="Only inspect the latest workflow revision for each app.",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        findings = fetch_findings(latest_only=args.latest_only)

    scope_label = "latest workflow revision per app" if args.latest_only else "all workflow revisions"
    print(f"Consecutive numeric node ID audit scope: {scope_label}")
    print(f"Matched workflows: {len(findings)}")
    print()

    summary_headers = [
        "owner_name",
        "owner_email",
        "workflow_count",
        "app_count",
        "future30_count",
        "integer_grid_count",
    ]
    summary_rows = summarize(findings)
    print("By owner")
    if summary_rows:
        print_table(summary_headers, summary_rows)
    else:
        print("(no matches)")
    print()

    detail_headers = [
        "owner_email",
        "app_name",
        "created_at",
        "node_count",
        "min_numeric_id",
        "max_numeric_id",
        "integer_grid",
        "future30_ids",
        "workflow_id",
    ]
    print("Workflow details")
    if findings:
        print_table(detail_headers, detail_rows(findings))
    else:
        print("(no matches)")


if __name__ == "__main__":
    main()
