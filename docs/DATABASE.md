# Database schema and migrations

SQLite foreign keys are enabled on each connection. All new mutations use parameterized SQL and `db_session()` transactions. Timestamps are UTC ISO-8601 strings. Startup uses idempotent `CREATE TABLE IF NOT EXISTS`, `PRAGMA table_info`, additive `ALTER TABLE`, indexes and `schema_migrations` version 2. It does not rebuild or drop legacy complaint tables.

## Tables

| Table | Purpose / important fields |
| --- | --- |
| `users` | User identity, unique case-insensitive email, PBKDF2 password hash, role, active flag, created/updated timestamps. |
| `sessions` | Hash of opaque session cookie, user, CSRF token, created time, absolute expiry. |
| `login_throttles` | Failed sign-in count/window and lockout expiry keyed by normalized email. |
| `reports` | Stable issue ID, description/category/location, workflow status, score, duplicate link, department/assignee, evidence references, optional lat/lon, owner, synthetic marker, timestamps, event JSON. |
| `departments` | Configurable department ID, unique display name and active flag. |
| `issue_categories` | Category/subcategory, default department, priority, keywords, escalation hours and active flag. |
| `routing_rules` | Active category-to-department route and rule precedence. |
| `evidence_files` | Evidence UUID, report, kind (`before`/`after`), uploader, generated storage name, safe content type, byte count, SHA-256 and timestamp. File bytes are in `UPLOADS_DIR`. |
| `repair_submissions` | One row per field-worker repair attempt, worker, repair note, evidence reference and time. |
| `inspections` | One row per inspector decision, approval flag, five boolean checks, notes and time. |
| `notifications` | Recipient, optional report, event type, title/message, created and read timestamps. |
| `audit_events` | Actor, action, entity, JSON details and timestamp. |
| `schema_migrations` | Applied schema version and timestamp. |

Indexes cover report status/category/department/owner/assignee, session expiry, evidence by report, notifications by recipient/read state, and inspections by report.

## Migration behavior

- Existing report IDs, statuses, descriptions, event history and categories are preserved.
- Missing columns/tables are added; new report owner/assignee/coordinates remain nullable for legacy records.
- Legacy category/subcategory and suggested department values are backfilled without changing the original report ID.
- Fresh database startup initializes the catalog but does not create complaint records. Synthetic demo reports are created only through the explicit system-admin-only demo reset endpoint when `NAGRIVANTA_DEMO_RESET=1`; the operation refuses to run if any non-synthetic report exists.
- Legacy data-URL evidence is moved to generated files and references become `evidence:<uuid>`. PNG/JPEG/WebP signatures keep their image content type. Other legacy bytes are preserved as `application/octet-stream` attachments, never served inline.
- A database backup and evidence-directory backup must be made before deploying against an existing production database. Test migration on a copy and verify report IDs, history and downloads before switching traffic.
- Files and SQLite cannot participate in one atomic transaction. The implementation writes a uniquely named file and then its metadata in the active database transaction; a crash at the boundary may leave an orphan file. Production operations should include reconciliation/backup tooling.

## Durability

SQLite and the private evidence folder are durable only if their filesystem is durable. The current Render free blueprint has no persistent disk. Set both `DATABASE_PATH` and `UPLOADS_DIR` inside the same verified persistent mount on a plan that supports it; keep regular database and evidence backups. Do not assume a path named `/var/data` is persistent unless a disk is actually mounted there.
