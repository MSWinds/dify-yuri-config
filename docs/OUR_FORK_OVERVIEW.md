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
| `main` | Tracks upstream Dify main branch |
| `school-stable` | Production-ready classroom version (only tested, stable changes) |
| `school-dev` | Development branch for merging upstream + resolving conflicts |

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

# 2. Update tracking branch
git checkout main
git merge upstream/main

# 3. Merge to dev and resolve conflicts
git checkout school-dev
git merge main

# 4. Test thoroughly

# 5. If stable, merge to school-stable and tag
git checkout school-stable
git merge school-dev
git tag school-YYYY-MM-DD
```

## 📁 Key Documentation

| Document | Description |
|----------|-------------|
| [CLASSROOM_CHANGES.md](./CLASSROOM_CHANGES.md) | All customization details |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Docker deployment guide |

## ⚠️ Known Compatibility Notes

### Web Image Version Mismatch

As of 2025-12-26:
- **Docker web image**: `langgenius/dify-web:1.11.1`
- **Upstream main**: includes PR #29659 (password encryption)

The 1.11.1 web image does NOT include password encryption. If you update API code beyond 1.11.1, ensure:
1. Remove `@decrypt_password_field` from login endpoint, OR
2. Build custom web image with latest code

See `api/controllers/console/auth/login.py` for current workaround.

## 👥 Maintainers

- Yuri (kaijie.yu@cgu.edu)

