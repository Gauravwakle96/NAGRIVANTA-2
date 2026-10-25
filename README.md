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
- A public **Explore Live Demo** launcher with isolated synthetic identities and records for all five roles, a guided tour, server-validated role switching, group-scoped reset, one-hour sessions, and inactive-group cleanup.
- English, Marathi and Hindi labels for the main portal, forms, statuses, demo guide and deterministic FAQ. Complaint text and other user-authored content remain unchanged.
- Explainable duplicate warnings for unresolved reports from the last 30 days. Citizens explicitly confirm before continuing; a new report always keeps its own ID and history.
- Write-once citizen feedback (1–5 plus optional comment) after verified closure, with separate real-response and synthetic-demo satisfaction metrics.
- A deterministic Civic Assistant FAQ in English, Marathi and Hindi; it does not access private case records or require an external AI provider.
- Additive SQLite startup migrations through schema version 4 that preserve existing report IDs and workflow events. Old data-URL evidence is migrated to private storage where it can be decoded and is kept non-inline if its format is not a supported raster image.

Routing and priority are deterministic rules, not a trained AI model. Recommendations are explainable and require human review. Priority values and seeded department names are illustrative, not official service commitments.

## Run locally

Requires Python 3.10+; no third-party Python runtime packages are used.

```bash
python server.py
```

Open <http://localhost:8000>. On first start the app creates `nagrivanta.sqlite3` and initializes the catalog; it does not automatically create complaint records. Citizen accounts can be registered through the UI; public registration cannot create staff or administrator accounts. Judges can use **Explore Live Demo** without registering: the server creates five isolated synthetic identities and sample records, then opens the selected role. Demo sessions expire after one hour; idle groups are removed after six hours. **Reset demo** replaces only the current synthetic group. Demo roles cannot access ordinary accounts, complaints or global administration.

The older `NAGRIVANTA_DEMO_RESET=1` switch is retained only for a signed-in System Administrator resetting legacy, ungrouped synthetic examples. It refuses to run if ordinary reports or isolated public-demo groups exist. Do not enable it on shared or production data.

Create the first system administrator in a terminal (the password prompt does not echo):

```bash
python server.py create-admin admin@example.test
```

Or supply the following environment variables on first startup. The bootstrap creates the initial system administrator only when the database has no system-administrator account. It never promotes an existing citizen or staff account. If the configured email is already in use, startup stops with a clear error; choose a different, unused email. Once an administrator exists, later restarts do not add another account or change its password:

```text
NAGRIVANTA_BOOTSTRAP_ADMIN_EMAIL
NAGRIVANTA_BOOTSTRAP_ADMIN_PASSWORD  # 12+ characters; keep in the host's secret manager
NAGRIVANTA_BOOTSTRAP_ADMIN_NAME     # optional
```

System administrators can create municipal, worker and inspector accounts in the admin portal. Give each person their account credentials through a separate secure channel. This demo does not provide email verification, password recovery, MFA, or forced first-login password reset.

Open the role-aware app at the site root (`/`) or use the `/admin` entry link. Both paths serve the same app; `/admin` is not an access grant or a separate dashboard. The authenticated server-side account role determines the portal. Sign in with the System Administrator account to open **Administration**; a Citizen account remains limited to the Citizen portal, even when using `/admin`. Sign out before switching accounts.

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
| `NAGRIVANTA_DEMO_RESET` | Enable legacy system-admin reset for ungrouped synthetic examples (not required for public isolated demo) | disabled |

See [`.env.example`](.env.example). Use distinct, writable database and evidence paths. Both paths must be placed on persistent storage if records must survive host restarts.

## Database, evidence and migration

The current schema includes `users`, `sessions`, `reports`, `departments`, `issue_categories`, `routing_rules`, `evidence_files`, `repair_submissions`, `inspections`, `notifications`, `audit_events`, `login_throttles` and `schema_migrations`. See [`docs/DATABASE.md`](docs/DATABASE.md).

Startup applies idempotent additive changes and records schema version 4. Existing complaint IDs, report text, statuses and events are preserved. Version 4 adds isolated demo-group markers, the demo-account flag, an append-only feedback table and supporting indexes. The additive staff-department migration does not infer department assignments; unassigned municipal staff have restricted access until a system administrator assigns an active department. Before deploying this version against any existing database, take a database backup and copy the existing evidence directory; test the upgrade on a copy first. Startup migration is not a substitute for a production backup or rollback plan.

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

The automated API tests cover registration/login/logout, password rotation, origin and CSRF controls, login throttling, role and evidence access, complaint lifecycle, inspection rejection and rework, notifications, configuration, analytics, additive migration, demo isolation/role switching/reset, duplicate confirmation and feedback authorization.

## Render deployment and storage warning

The repository's existing `render.yaml` config is a **Render `free` web service**, build command `echo 'No external dependencies'`, start command `python server.py`, and health check `/api/health`. It does **not** define a persistent disk. A read-only health check of the provided Render service returned HTTP 200 and reported `SQLite + private filesystem`; this confirms availability, not durable persistence. The free filesystem is ephemeral, so SQLite and private uploads may be lost on restart/redeploy; durable storage is **not verified or guaranteed** by this configuration.

To initialize the live System Administrator, open the `nagrivanta-round2` service in Render → **Environment**, set `NAGRIVANTA_BOOTSTRAP_ADMIN_EMAIL` to a new, unused email and set `NAGRIVANTA_BOOTSTRAP_ADMIN_PASSWORD` as a secret (12–256 characters). Optionally set `NAGRIVANTA_BOOTSTRAP_ADMIN_NAME`. Save and redeploy/restart the service. Then open `/admin` (or the site root), sign in with those credentials, and use **Manage users** to create Municipal Administrator and Field Worker accounts. Remove the bootstrap variables after confirming login; the created account remains in the database. If an administrator already exists, bootstrap is a no-op and does not reset its credentials.

To demonstrate durable persistence, use a Render service/plan that supports a persistent disk, attach and verify a mount (for example `/var/data`), then set both `DATABASE_PATH=/var/data/nagrivanta.sqlite3` and `UPLOADS_DIR=/var/data/nagrivanta-uploads`. Verify that the paths are writable and survive an actual restart before describing the service as persistent. This repository's blueprint remains on the free plan and does not attach a disk; durable persistence is not fixed by this change. No production deployment was performed from this working branch.

## Limitations and security notes

- This standard-library `http.server` app is a hackathon/demo implementation, not a production-reviewed municipal service. Use synthetic data only until a security, privacy, operational and legal review is complete.
- In-app notifications are persisted; email, SMS, WhatsApp, push, identity-provider and government integrations are not configured.
- The map uses the Leaflet CDN and OpenStreetMap tiles; map pins represent submitted complaint coordinates, never verified heritage assets.
- Image validation checks declared type and file signatures but does not fully decode, re-encode, strip EXIF, or malware-scan images. Keep uploads small and non-sensitive; add production image processing and retention controls before real use.
- Login throttling is a lightweight SQLite per-email lockout. A public production deployment needs additional network-aware abuse controls, account recovery, monitoring and incident response.
- Render free storage is ephemeral; a local SQLite file is persistent only as long as its filesystem is retained.
- No real-world adoption, response-time, environmental or public-impact statistics are claimed. Analytics are calculated from records in the database; any explicitly initialized demo records are synthetic.

## Judge demonstration

Open `/`, choose **Explore Live Demo**, then select **Start Guided Tour** (begins as Citizen) or open a specific role portal. Use the role selector in the top bar to switch between the five server-side demo identities. Submit a clearly synthetic complaint as Citizen, assign it as Municipal Administrator, submit repair evidence as Field Worker, and approve or return it as Inspector. The Citizen portal displays the stored timeline, notifications and post-verification feedback form. The System Administrator view is limited to synthetic metrics and audit events; account management and global configuration stay disabled. **Reset demo** affects only this group; **Exit demo** signs out. See [`docs/DEMO.md`](docs/DEMO.md) for the walkthrough.

## Working branch

The focused Render bootstrap changes are on local branch `fix/render-admin-bootstrap`. They have **not** been pushed to GitHub or deployed to Render. Review the diff and run the tests before pushing or deploying.
