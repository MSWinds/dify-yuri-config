# Dify Classroom Fork Overview

## 🎯 Purpose

This is a fork of [Dify](https://github.com/langgenius/dify) customized for **classroom/teaching use**.

**Core Goal**: Enable multi-tenant workspace where:
- Students can self-register (whitelist controlled)
- Each student gets their own isolated workspace
- Teachers/TAs are automatically added to all student workspaces as admins
- Students cannot invite others or rename workspaces

## 📌 Branch Strategy

| Branch | Purpose |
|--------|---------|
| `school-stable` | **Production branch** - Deploy from this. Only tested, stable changes. |
| `main` | Testing branch for merging upstream updates and resolving conflicts |

## 🏷️ Tagging Convention

Format: `school-YYYY-MM-DD` (e.g., `school-2025-12-26`)

Tag when:
- A version is verified working in classroom
- Before merging upstream updates
- After significant changes

## 🔄 Upstream Sync Workflow

```bash
# 1. Fetch upstream
git fetch upstream

# 2. Test merge on main branch
git checkout main
git merge upstream/main

# 3. Resolve conflicts if any, then test thoroughly

# 4. If stable, merge to school-stable and tag
git checkout school-stable
git merge main
git tag school-YYYY-MM-DD
git push origin school-stable
git push origin school-YYYY-MM-DD
```

## 📁 Key Documentation

| Document | Description |
|----------|-------------|
| [CLASSROOM_CHANGES.md](./CLASSROOM_CHANGES.md) | All customization details |

## ⚠️ Version Compatibility

### Current Version: 1.12.1

As of 2026-02-11, we are using:
- `langgenius/dify-api:1.12.1`
- `langgenius/dify-plugin-daemon:0.5.2-local`
- `web` is built locally from `../web`

The 1.11.2 release includes password encryption (PR #29659), so `@decrypt_password_field` is enabled.

### Deployment Architecture (IMPORTANT)

Our setup uses a **hybrid approach** that is easy to break on upgrades:

| Component | Source | Notes |
|-----------|--------|-------|
| Python source code (`/app/api/`) | **Local bind mount** (`../api:/app/api`) | Our classroom patches, agent tweaks, etc. |
| Python dependencies (`.venv`) | **Image built-in** | Protected by anonymous volume `/app/api/.venv` |
| Entrypoint (`/entrypoint.sh`) | **Image built-in** | NOT affected by bind mount; lives at `/entrypoint.sh`, not `/app/api/docker/entrypoint.sh` |
| Web frontend | **Local build** | Built from `../web` via Dockerfile |

**Key implication**: When upstream updates `api/docker/entrypoint.sh` (e.g. adds a new Celery queue), our bind-mounted code picks up the change immediately, but the **container's actual entrypoint stays on the old image version**. This mismatch caused the 2026-02-11 chatflow outage.

### When Upgrading (Checklist)

```
Pre-upgrade:
  [ ] Tag current working state: git tag school-YYYY-MM-DD
  [ ] Backup .env: cp docker/.env docker/.env.backup.$(date +%Y-%m-%d)
  [ ] Backup docker-compose.yaml

After merging upstream:
  [ ] 1. Image versions: check if docker-compose-template.yaml bumped image tags
  [ ] 2. .env variables: diff .env.example for new required variables
  [ ] 3. Classroom files: verify our patched files weren't rewritten upstream
  [ ] 4. **Entrypoint drift** (CRITICAL):
         diff the image's /entrypoint.sh vs the repo's api/docker/entrypoint.sh
         Specifically check Celery queue list (DEFAULT_QUEUES) and startup flags.
         If the repo version added new queues, you MUST either:
           a) Add them to CELERY_QUEUES in docker-compose.yaml (current approach), or
           b) Upgrade the image to a version that includes the new entrypoint
  [ ] 5. DB migrations: run `docker compose exec api flask db upgrade`
  [ ] 6. New Celery tasks: check if new task modules were added in ext_celery.py
  [ ] 7. New dependencies: if pyproject.toml changed significantly, the image's
         .venv may be outdated - consider rebuilding or upgrading the image

Smoke test after deploy:
  [ ] Chatflow (advanced-chat) app works (streaming mode)
  [ ] Agent (agent-chat) app works
  [ ] Workflow app works
  [ ] Web UI loads and login works
```

### Entrypoint Queue Sync (Manual Override)

Because the image's `/entrypoint.sh` can lag behind the repo code, we explicitly
set `CELERY_QUEUES` in `docker-compose.yaml` for the worker service. This value
must be kept in sync with the `DEFAULT_QUEUES` in `api/docker/entrypoint.sh`.

To check for drift:
```bash
# Show what the image thinks the queues should be
docker compose exec worker grep DEFAULT_QUEUES /entrypoint.sh

# Show what the repo code expects
grep DEFAULT_QUEUES api/docker/entrypoint.sh

# Show what the worker is actually using
docker compose logs worker | grep "Starting Celery worker with queues"
```

## 🔧 Environment Backup

Always backup `.env` before upgrades:
```bash
cp docker/.env docker/.env.backup.$(date +%Y-%m-%d)
```

Key classroom variables to preserve:
```bash
CLASSROOM_MODE=true
CLASSROOM_TEACHERS=teacher1@school.edu,teacher2@school.edu
CLASSROOM_STUDENT_WHITELIST=student1@school.edu,student2@school.edu
ALLOW_REGISTER=true
ALLOW_CREATE_WORKSPACE=true
```

## 👥 Maintainers

- Yuri (kaijie.yu@cgu.edu)
