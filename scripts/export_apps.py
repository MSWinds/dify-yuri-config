"""
Batch-export every app in every workspace as a DSL YAML file.

Usage (from repo root):
    docker cp scripts/export_apps.py docker-api-1:/tmp/export_apps.py
    docker exec docker-api-1 python /tmp/export_apps.py
    docker exec docker-api-1 tar czf /tmp/export_output.tar.gz -C /tmp export_output
    docker cp docker-api-1:/tmp/export_output.tar.gz scripts/

Output layout:
    /tmp/export_output/
        <owner-email>/
            <app-name>.yml
            <app-name>-2.yml   # duplicate name within same workspace
        ...
        _summary.txt
"""

import os
import re
import sys
import logging
from collections import defaultdict
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Bootstrap Flask app context (must happen before any model imports)
# ---------------------------------------------------------------------------
sys.path.insert(0, "/app/api")

from app_factory import create_app  # noqa: E402

flask_app = create_app()

# ---------------------------------------------------------------------------
# Imports that need the app context
# ---------------------------------------------------------------------------
with flask_app.app_context():
    from extensions.ext_database import db
    from models.account import TenantAccountJoin, TenantAccountRole
    from models.model import Account, App, Tenant
    from services.app_dsl_service import AppDslService

OUTPUT_ROOT = "/tmp/export_output"


def safe_filename(name: str) -> str:
    """Turn an app name into a safe filename (no path separators, trim length)."""
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', "-", name)
    name = re.sub(r"\s+", " ", name)
    return name[:100]


def unique_path(directory: str, base: str) -> str:
    """Return a path that doesn't collide with existing files; append -2, -3 … if needed."""
    candidate = os.path.join(directory, f"{base}.yml")
    if not os.path.exists(candidate):
        return candidate
    counter = 2
    while True:
        candidate = os.path.join(directory, f"{base}-{counter}.yml")
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def run() -> None:
    logging.basicConfig(level=logging.WARNING)
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    # owner_email → list of (app, workspace_name)
    WorkspaceRow = tuple  # (owner_email, tenant_name, app_obj)

    with flask_app.app_context():
        rows: list[WorkspaceRow] = (
            db.session.query(Account.email, Tenant.name, App)
            .join(TenantAccountJoin, TenantAccountJoin.tenant_id == App.tenant_id)
            .join(Account, Account.id == TenantAccountJoin.account_id)
            .join(Tenant, Tenant.id == App.tenant_id)
            .filter(TenantAccountJoin.role == TenantAccountRole.OWNER.value)
            .order_by(Account.email, App.name)
            .all()
        )

        # db_counts[email] = number of apps owned (from DB query)
        db_counts: dict[str, int] = defaultdict(int)
        file_counts: dict[str, int] = defaultdict(int)
        errors: list[str] = []

        for owner_email, _workspace_name, app in rows:
            db_counts[owner_email] += 1

            owner_dir = os.path.join(OUTPUT_ROOT, owner_email)
            os.makedirs(owner_dir, exist_ok=True)

            try:
                yaml_content = AppDslService.export_dsl(app_model=app, include_secret=False)
            except Exception as exc:
                msg = f"SKIP  {owner_email}/{app.name!r}: {exc}"
                print(msg)
                errors.append(msg)
                continue

            out_path = unique_path(owner_dir, safe_filename(app.name))
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(yaml_content)

            file_counts[owner_email] += 1
            print(f"  OK  {out_path}")

    # -----------------------------------------------------------------------
    # Summary / check report
    # -----------------------------------------------------------------------
    all_emails = sorted(set(db_counts) | set(file_counts))
    total_db = sum(db_counts.values())
    total_files = sum(file_counts.values())

    lines = [
        f"Export Summary  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "=" * 60,
    ]

    mismatches = []
    for email in all_emails:
        db_n = db_counts[email]
        file_n = file_counts[email]
        status = "OK" if db_n == file_n else "MISMATCH"
        lines.append(f"{email:<42}  DB: {db_n:>3}   Files: {file_n:>3}   {status}")
        if status != "OK":
            mismatches.append(email)

    lines += [
        "=" * 60,
        f"{'TOTAL':<42}  DB: {total_db:>3}   Files: {total_files:>3}",
    ]

    if errors:
        lines.append("")
        lines.append("Errors:")
        lines.extend(f"  {e}" for e in errors)

    summary = "\n".join(lines) + "\n"
    summary_path = os.path.join(OUTPUT_ROOT, "_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write(summary)

    print()
    print(summary)

    if mismatches:
        print(f"WARNING: {len(mismatches)} workspace(s) have mismatches — check _summary.txt")
        sys.exit(1)
    else:
        print("All counts match.")


if __name__ == "__main__":
    run()
