# Scripts Guide

This document provides a summary and usage instructions for the utility scripts located in the `scripts/` directory.

These scripts are primarily run from the **host machine** (local), not inside the Docker containers.

## 🛠️ General Utility Scripts

### 1. Initialize Admin Account
**Script:** `scripts/init_admin.py`

**Description:**
Automatically creates a default administrator account if the Dify instance is fresh (in the "install" state). Used to skip the initial setup wizard.
- **Default User:** `kaijie.yu@cgu.edu` (Name: Yuri)
- **Default Password:** `CGUgenaiclassTA2026`

**Usage:**
```bash
uv run --project api python scripts/init_admin.py
```

### 2. Verify Authentication (Internal)
**Script:** `scripts/verify_auth.py`

**Description:**
Directly invokes the backend `AccountService` to verify if a user can authenticate. Useful for debugging password checking/hashing logic without going through the HTTP API.

**Usage:**
```bash
docker exec docker-api-1 python /app/scripts/init_admin.py

uv run --project api python scripts/verify_auth.py
```

### 3. Frontend Development Helper
**Script:** `scripts/dev-web.sh`

**Description:**
A comprehensive helper script for the Next.js frontend (`web` directory). It handles dependency installation, starting the dev server, linting, testing, and building docker images.

**Usage:**
```bash
./scripts/dev-web.sh [command]
```
**Commands:**
- `setup`: Install dependencies and create `.env.local`.
- `dev`: Start the local development server (localhost:3000).
- `check`: Run linting and type checks.
- `build`: Build the frontend.
- `deploy`: Build and run the web container in Docker.

### 4. Hard Reset Environment
**Script:** `scripts/my-test/reset-dev.sh`

**Description:**
⚠️ **Destructive!** Stops all Docker containers and **deletes all persistent data** (Postgres, Redis, Weaviate volumes), then restarts the containers. Use this to get a completely clean slate.

**Usage:**
```bash
./scripts/my-test/reset-dev.sh
```

---

## 🧪 Stress Testing & Benchmarking

The `scripts/stress-test/` directory contains tools to benchmark the Dify API, specifically focusing on SSE (Server-Sent Events) streaming performance.

### 5. Stress Test Setup
**Script:** `scripts/stress-test/setup_all.py`

**Description:**
Automates the preparation of the Dify environment for testing. It will:
1. Create an admin account.
2. Initialize a Mock OpenAI server (to simulate LLM responses without costs).
3. Import a test workflow app.
4. Generate API keys.

**Usage:**
```bash
uv run --project api python scripts/stress-test/setup_all.py
```

### 6. Run Locust Stress Test
**Script:** `scripts/stress-test/run_locust_stress_test.sh`

**Description:**
Executes the Locust load test using the `sse_benchmark.py` runner. It supports both a Web UI mode (for real-time monitoring) and a Headless mode (for CI/CD or automated runs).
- **Target:** `localhost:5001`
- **Metric:** SSE Streaming Token/Event throughput.

**Usage:**
```bash
./scripts/stress-test/run_locust_stress_test.sh
```
Follow the interactive prompts to choose Web UI or Headless mode.

### 7. Cleanup Stress Test Data
**Script:** `scripts/stress-test/cleanup.py`

**Description:**
Removes temporary configuration files (`.json` states) and report files generated during the stress test setup and execution.

**Usage:**
```bash
uv run --project api python scripts/stress-test/cleanup.py
```

### 8. Delete Student Accounts
**Script:** `scripts/delete_users.py`

**Description:**
Safely deletes student accounts and their associated data.
- Deletes the account.
- Deletes their **personal** workspace (Tenant) if they are the **OWNER**, regardless of member count.
- Removes them from any **shared** workspaces (where they are only Admin/Editor/Member) without deleting the workspace.
- Cleans up Apps, Knowledge Base (Datasets), Documents, and Provider settings associated with the deleted tenant.
- **Safety First:** Runs in "Dry Run" mode by default.

**Usage:**
```bash
uv run --project api python scripts/delete_users.py email1@example.com [email2@example.com ...] [--force]
```
- Run without `--force` to see what will be deleted.
- Add `--force` to actually delete.

**Note:** This script automatically detects if it's running locally and patches the database connection settings to work with `docker-compose` services exposed on localhost.

---

## ℹ️ Notes on `uv`

We use `uv` as the Python package manager. The flag `--project api` tells `uv` to use the dependencies and environment defined in the `api/pyproject.toml` file (or equivalent), ensuring that scripts run with the correct libraries installed.
