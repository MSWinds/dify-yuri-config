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

### Current Version: 1.11.2

As of 2025-12-26, we are using:
- `langgenius/dify-api:1.11.2`
- `langgenius/dify-web:1.11.2`
- `langgenius/dify-plugin-daemon:0.5.2-local`

The 1.11.2 release includes password encryption (PR #29659), so `@decrypt_password_field` is enabled.

### When Upgrading

1. Check if `docker-compose.yaml` image versions changed
2. Compare `.env.example` for new required variables
3. Verify classroom-related files weren't modified upstream (see CLASSROOM_CHANGES.md)

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
