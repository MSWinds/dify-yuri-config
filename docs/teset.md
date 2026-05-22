# Dataset Permission Management via Database

## Permission Values

| Value | Meaning |
|-------|---------|
| `only_me` | Only creator can access (default) |
| `all_team_members` | All workspace members can access |
| `partial_members` | Specified members only (requires `dataset_permissions` table entries) |

## Common Queries

### Find user account ID
```sql
SELECT id, name, email FROM accounts WHERE name ILIKE '%keyword%' OR email ILIKE '%keyword%';
```

### List user's datasets
```sql
SELECT id, name, permission, created_at
FROM datasets
WHERE created_by = '<account_id>'
ORDER BY created_at DESC;
```

### Check single dataset permission
```sql
SELECT name, permission, created_by FROM datasets WHERE id = '<dataset_id>';
```

## Modify Permission

### Batch update (by user)
```sql
UPDATE datasets SET permission = 'all_team_members' WHERE created_by = '<account_id>';
```

### Revert back
```sql
UPDATE datasets SET permission = 'only_me' WHERE created_by = '<account_id>';
```

### Single dataset
```sql
UPDATE datasets SET permission = 'all_team_members' WHERE id = '<dataset_id>';
```

## Execution Method

Through Docker Postgres container:
```bash
docker exec docker-db_postgres-1 psql -U postgres -d dify -c "<SQL>"
```
