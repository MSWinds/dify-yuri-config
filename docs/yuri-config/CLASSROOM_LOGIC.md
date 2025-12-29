# Classroom Mode: Logic & Rules

This document outlines the current implemented logic for the Classroom Mode in Dify, after the recent fixes.

## 1. Registration Whitelist (The Gatekeeper)

*   **Code Location**: `api/services/account_service.py` -> `create_account()`
*   **Trigger**: Any attempt to create a new account (Email or OAuth).
*   **Logic**:
    1.  System checks if `CLASSROOM_MODE` is enabled.
    2.  System loads `CLASSROOM_TEACHERS` and `CLASSROOM_STUDENT_WHITELIST` from environment variables.
    3.  **Verification**: The registering email is compared against these lists (Case-Insensitive Match).
        *   **MATCH**: Registration proceeds.
        *   **NO MATCH**: Registration is blocked immediately with a 403 Error ("Your email is not in the classroom whitelist").

## 2. Auto-Association (The Connector)

*   **Code Location**: `api/events/event_handlers/classroom_init.py`
*   **Trigger**: Immediately after a new Workspace (Tenant) is created.

### Scenario A: A Student Registers (Standard Flow)
*Use Case: Student signs up, system pulls teachers in.*

1.  **Detection**: System identifies the new workspace owner is **NOT** in the `CLASSROOM_TEACHERS` list (therefore, a Student).
2.  **Loop**: System iterates through the configured `CLASSROOM_TEACHERS` list.
3.  **Lookup**: Queries the database for each teacher's account.
4.  **Action**: **Injects** the found teacher accounts into the new Student Workspace as **Admins**.

### Scenario B: A Teacher Registers (Late Arrival Flow)
*Use Case: Teacher signs up late, system pushes them into existing student workspaces.*

1.  **Detection**: System identifies the new workspace owner **IS** in the `CLASSROOM_TEACHERS` list.
2.  **Loop**: System iterates through the configured `CLASSROOM_STUDENT_WHITELIST`.
3.  **Lookup**: Queries the database for each student's account.
4.  **Scanning**: Finds all workspaces owned by these students.
5.  **Action**: **Injects** this new teacher into all found Student Workspaces as **Admin**.

## 3. Workspace Rules

1.  **One-Person-One-Workspace**: Every user creates their own unique Workspace upon registration.
2.  **Hierarchy**:
    *   **Student Workspace**: Owned by Student, managed/monitored by Teachers (Admins).
    *   **Teacher Workspace**: Owned by Teacher. Private (Students are not added here).
3.  **Data Consistency Requirement**:
    *   For the logic to work, the **Email string in database** must exactly match (ignoring case) the **Email string in .env config**.
    *   *Note: Invisible characters or spaces in the database will cause the lookup to fail.*
