# Classroom Mode Changes

This document tracks all modifications made to the Dify codebase for classroom use.

---

## 1. Configuration: Classroom Mode Settings

### Why
Enable classroom-specific features through environment variables.

### What
- **File**: `api/configs/feature/__init__.py`
- **Added**: `ClassroomConfig` with:
  - `CLASSROOM_MODE: bool` - Enable/disable classroom features
  - `CLASSROOM_TEACHERS: str` - Comma-separated teacher emails
  - `CLASSROOM_STUDENT_WHITELIST: str` - Comma-separated allowed student emails

### How
New Pydantic config class reads from environment variables.

### Risks
Low - additive change, no conflict with upstream config structure.

---

## 2. Registration Whitelist

### Why
Only allow pre-approved students and teachers to register.

### What
- **File**: `api/services/account_service.py` (`RegisterService.register`)
- **Added**: Whitelist check before account creation

### How
```python
if system_features.classroom_mode:
    allowed_list = teachers + students
    if email not in allowed_list:
        raise AccountRegisterError("Registration restricted...")
```

### Risks
Medium - `RegisterService.register` may change upstream. Check this method on each merge.

---

## 3. Auto-Add Teachers to Student Workspaces

### Why
Teachers need admin access to all student workspaces to grade assignments.

### What
- **File**: `api/events/event_handlers/classroom_init.py` (NEW FILE)
- **File**: `api/events/event_handlers/__init__.py` (register handler)
- **Listens to**: `tenant_was_created` event

### How
When a new workspace is created:
1. Read `CLASSROOM_TEACHERS` config
2. Find teacher accounts
3. Add each teacher as admin to the new workspace

### Risks
Medium - event system changes could break this. Verify `tenant_was_created` event still exists.

---

## 4. Block Student Invitations

### Why
Prevent students from inviting unauthorized users.

### What
- **File**: `api/services/account_service.py` (`InviteService.invite_new_member`)
- **Added**: Check if inviter is in `CLASSROOM_TEACHERS`

### How
```python
if classroom_mode and inviter.email not in teachers:
    raise ValueError("Students cannot invite members...")
```

### Risks
Medium - invitation logic may be refactored upstream.

---

## 5. Block Workspace Renaming (Students)

### Why
Keep workspace names consistent for grading.

### What
- **File**: `api/controllers/console/workspace/workspace.py`
- **Modified**: Workspace rename endpoint

### How
Check if current user is in `CLASSROOM_TEACHERS` before allowing rename.

### Risks
Low - endpoint-level change, easy to re-apply.

---

## 6. Feature Service: Expose Classroom Config

### Why
Frontend and other services need access to classroom settings.

### What
- **File**: `api/services/feature_service.py`
- **Added**: Classroom mode fields to system features response

### How
```python
system_features.classroom_mode = dify_config.CLASSROOM_MODE
system_features.classroom_teachers = dify_config.CLASSROOM_TEACHERS
system_features.classroom_student_whitelist = dify_config.CLASSROOM_STUDENT_WHITELIST
```

### Risks
Low - additive change to response schema.

---

## 7. Docker Compose: Mount Local API Code

### Why
Apply classroom patches without rebuilding images.

### What
- **File**: `docker/docker-compose.yaml`
- **Modified**: `api`, `worker`, `worker_beat` services

### How
```yaml
volumes:
  - ../api:/app/api
  - /app/api/.venv  # Protect container's venv
```

### Risks
High - volume mounts can cause issues if code structure changes.

---

## 8. Password Encryption Compatibility Fix

### Why
Web image 1.11.1 doesn't have password encryption (PR #29659 merged after 1.11.1).

### What
- **File**: `api/controllers/console/auth/login.py`
- **Removed**: `@decrypt_password_field` decorator from login endpoint

### How
Commented out the decorator with explanation.

### Risks
Low - re-enable when web image is updated to include encryption.

---

## 📋 Files Modified Summary

| File | Type | Risk |
|------|------|------|
| `api/configs/feature/__init__.py` | Config | Low |
| `api/services/account_service.py` | Service | Medium |
| `api/services/feature_service.py` | Service | Low |
| `api/events/event_handlers/classroom_init.py` | NEW | Medium |
| `api/events/event_handlers/__init__.py` | Handler | Low |
| `api/controllers/console/workspace/workspace.py` | Controller | Low |
| `api/controllers/console/auth/login.py` | Controller | Low |
| `docker/docker-compose.yaml` | Config | High |

---

## 🔧 Environment Variables

Add these to `docker/.env`:

```bash
# Classroom Mode
CLASSROOM_MODE=true
CLASSROOM_TEACHERS=teacher1@school.edu,teacher2@school.edu
CLASSROOM_STUDENT_WHITELIST=student1@school.edu,student2@school.edu

# Required for multi-tenant
ALLOW_REGISTER=true
ALLOW_CREATE_WORKSPACE=true
```

---

## 🧪 Testing Checklist

Before marking a version stable:

- [ ] Teacher can register
- [ ] Whitelisted student can register
- [ ] Non-whitelisted email cannot register
- [ ] Student workspace created on registration
- [ ] Teachers auto-added to student workspace as admin
- [ ] Student cannot invite members
- [ ] Student cannot rename workspace
- [ ] Teacher can rename workspace
- [ ] Login works for both teacher and student

---

*Last updated: 2025-12-26*

