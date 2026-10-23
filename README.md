# Nagrivanta — Civic Governance Demo

Nagrivanta is a synthetic-data civic issue workflow: citizens report an issue, staff review a transparent routing suggestion, a municipal administrator assigns work, a field worker submits repair evidence, and an inspector approves or returns the work. The application is **not connected to a municipal authority, official heritage register, or live government system**. Do not use it to submit emergencies or sensitive real-world records.

## What is implemented

- Citizen registration, sign-in/sign-out, password changes, PBKDF2 password hashing, opaque server-side sessions, 12-hour session expiry, CSRF tokens and origin checks.
- Five server-authorized roles: citizen, municipal administrator, field worker, inspector and system administrator.
- Role-specific responsive portals; backend authorization is enforced independently of the UI.
- Complaint submission, unique tracking IDs, optional coordinates, report timelines, rule-based triage and configured department suggestions.
- Work assignment to an active field-worker account, work start, secure completion evidence, five-check inspection, rejection/rework and verified closure.
- Private image files with database metadata and permission-checked evidence routes; no new evidence data URLs are stored in complaint rows.
- In-app notifications targeted to relevant accounts, read/unread state, audit events, user/department/category/routing configuration.
- Heritage Watch map and list backed only by submitted heritage complaints that have coordinates. It does not show official heritage assets.
- Database-derived queue metrics, resolution times, rework and inspection rates, department workload and configurable escalation thresholds.
- Additive SQLite startup migrations that preserve existing report IDs and workflow events. Old data-URL evidence is migrated to private storage where it can be decoded and is kept non-inline if its format is not a supported raster image.

Routing and priority are deterministic rules, not a trained AI model. Recommendations are explainable and require human review. Priority values and seeded department names are illustrative, not official service commitments.

## Run locally

Requires Python 3.10+; no third-party Python runtime packages are used.

```bash
python server.py
```

Open <http://localhost:8000>. On first start the app creates `nagrivanta.sqlite3`, initializes the catalog and adds four clearly synthetic demo complaints. Citizen accounts can be registered through the UI; public registration cannot create staff or administrator accounts.

Create the first system administrator in a terminal (the password prompt does not echo):

```bash
python server.py create-admin admin@example.test
```

Or supply the following environment variables on first startup. An account is created only if that email does not already exist; startup will not reset an existing password:

```text
NAGRIVANTA_BOOTSTRAP_ADMIN_EMAIL
NAGRIVANTA_BOOTSTRAP_ADMIN_PASSWORD  # 12+ characters; keep in the host's secret manager
NAGRIVANTA_BOOTSTRAP_ADMIN_NAME     # optional
```

System administrators can create municipal, worker and inspector accounts in the admin portal. Give each person their account credentials through a separate secure channel. This demo does not provide email verification, password recovery, MFA, or forced first-login password reset.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `PORT` | HTTP listening port | `8000` |
| `DATABASE_PATH` | SQLite database file | `./nagrivanta.sqlite3` |
| `UPLOADS_DIR` | Private evidence directory (must not be under `public/`) | `./private_uploads` |
| `NAGRIVANTA_BOOTSTRAP_ADMIN_EMAIL` | Optional one-time initial admin email | unset |
| `NAGRIVANTA_BOOTSTRAP_ADMIN_PASSWORD` | Optional initial admin secret; never commit | unset |
| `NAGRIVANTA_BOOTSTRAP_ADMIN_NAME` | Optional initial admin display name | `System Administrator` |
| `NAGRIVANTA_COOKIE_SECURE` | Force `Secure` session cookie (`1`/`0`) | inferred from Render/HTTPS proxy |
| `NAGRIVANTA_DEMO_RESET` | Enable destructive synthetic-demo reset endpoint | disabled |

See [`.env.example`](.env.example). Use distinct, writable database and evidence paths. Both paths must be placed on persistent storage if records must survive host restarts.

## Database, evidence and migration

The current schema includes `users`, `sessions`, `reports`, `departments`, `issue_categories`, `routing_rules`, `evidence_files`, `repair_submissions`, `inspections`, `notifications`, `audit_events`, `login_throttles` and `schema_migrations`. See [`docs/DATABASE.md`](docs/DATABASE.md).

Startup applies idempotent additive changes and records schema version 2. Existing complaint IDs, report text, statuses and events are preserved. Before deploying this version against any existing database, take a database backup and copy the existing evidence directory; test the upgrade on a copy first. Startup migration is not a substitute for a production backup or rollback plan.

Evidence is limited to PNG/JPEG/WebP and 1 MB per image. Files are saved under generated names outside `public/`, and are served only after checking the requester's report access. Unsupported legacy formats are archived as non-inline attachments where possible.

## API and roles

See [`docs/API.md`](docs/API.md) for endpoint shapes and CSRF/session requirements. The main state transitions are:

`submitted → assigned → in_progress → repair_submitted → verified`

An inspector can return a repair to `needs_rework`; municipal staff reassign it, the worker starts another attempt, and each repair and inspection remains in history. Citizens see only their own complaints; workers see their assignments; inspectors see the inspection queue and records they inspected; municipal administrators see the operational queue; system administrators manage accounts and configuration.

## Tests and checks

```bash
python -m unittest discover -s tests -v
node --check public/app.js
python -m py_compile server.py
```

The 13 automated API tests cover registration/login/logout, password rotation, origin and CSRF controls, login throttling, role and evidence access, complaint lifecycle, inspection rejection and rework, notifications, configuration, analytics and additive migration. A local Chromium run completed the full citizen → municipal assignment → field repair → inspector approval → citizen resolution flow without browser console errors or failed local responses. This was a one-off environment check, not a committed test dependency.

## Render deployment and storage warning

The repository's existing `render.yaml` config is a **Render `free` web service**, build command `echo 'No external dependencies'`, start command `python server.py`, and health check `/api/health`. It does **not** define a persistent disk. A read-only GET to the public health endpoint returned HTTP 200 and identified the running service as `Nagrivanta demo API`; this is the current public deployment, not the local `round2-hardening` branch. The free filesystem is ephemeral, so SQLite and private uploads may be lost on restart/redeploy; durable storage is **not verified or guaranteed** by this configuration.

To demonstrate durable persistence, use a Render service/plan that supports a persistent disk, attach and verify a mount (for example `/var/data`), then set both `DATABASE_PATH=/var/data/nagrivanta.sqlite3` and `UPLOADS_DIR=/var/data/nagrivanta-uploads`. Verify that the paths are writable and survive an actual restart before describing the service as persistent. Keep the bootstrap password in the host's secret settings and remove the bootstrap variables after account creation. No production deployment was performed from this working branch.

## Limitations and security notes

- This standard-library `http.server` app is a hackathon/demo implementation, not a production-reviewed municipal service. Use synthetic data only until a security, privacy, operational and legal review is complete.
- In-app notifications are persisted; email, SMS, WhatsApp, push, identity-provider and government integrations are not configured.
- The map uses the Leaflet CDN and OpenStreetMap tiles; map pins represent submitted complaint coordinates, never verified heritage assets.
- Image validation checks declared type and file signatures but does not fully decode, re-encode, strip EXIF, or malware-scan images. Keep uploads small and non-sensitive; add production image processing and retention controls before real use.
- Login throttling is a lightweight SQLite per-email lockout. A public production deployment needs additional network-aware abuse controls, account recovery, monitoring and incident response.
- Render free storage is ephemeral; a local SQLite file is persistent only as long as its filesystem is retained.
- No real-world adoption, response-time, environmental or public-impact statistics are claimed. Analytics are calculated from records in the database; the four seeded records are synthetic.

## Judge demonstration

Use [`docs/DEMO.md`](docs/DEMO.md) for a short end-to-end script. Create staff accounts first, register a citizen, submit a synthetic report, assign it, show repair evidence, inspect all five checks, and confirm the citizen's status and notification. For Heritage Watch, enter coordinates only for a clearly labelled test location; missing coordinates stay in the report list and are not invented.

## Working branch

Changes in this package are on local branch `round2-hardening`. They have **not** been pushed to GitHub or deployed to Render. Review the diff and run the tests before pushing or deploying.
