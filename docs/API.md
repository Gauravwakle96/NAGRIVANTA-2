# HTTP API

All endpoints are same-origin. JSON requests use `Content-Type: application/json`. No permissive CORS policy is configured. `GET /api/auth/me` returns `{ "authenticated": false }` when signed out; protected resources return `401`.

## Authentication and CSRF

- `POST /api/auth/register` — `{email, display_name, password}`; citizen role only; returns session cookie and CSRF token.
- `POST /api/auth/login` — `{email, password}`; returns session cookie and CSRF token. Invalid credentials use a generic message. Ten failed attempts for a normalized email trigger a 15-minute lockout.
- `GET /api/auth/me` — current account, CSRF token and session expiry, or `authenticated:false`.
- `POST /api/auth/logout` — authenticated; delete current server session and clear cookie.
- `POST /api/auth/password` — `{current_password, new_password}`; verify current password, revoke prior sessions, and issue a new session.

For authenticated state-changing requests, send the CSRF token from login/register/me as `X-CSRF-Token`. Requests with an `Origin` header must match the request host. The session cookie is HttpOnly, SameSite=Lax and Secure on Render/HTTPS (or when `NAGRIVANTA_COOKIE_SECURE=1`). Session lifetime is 12 hours.

## Public/support endpoints

- `GET /api/health` — basic health response; configured database/evidence paths are not disclosed.
- `GET /api/catalog` — active categories, subcategories and departments.
- `POST /api/triage` — `{description}`; public rule-based keyword recommendation; does not create or change a complaint.

## Complaints and evidence

- `GET /api/reports?status=&category=&q=&heritage=1&limit=50` — authenticated and automatically scoped by role. Search is limited to the permitted report set.
- `POST /api/reports` — citizen only. Required: `title`, `category`, `subcategory`, `description`, `area`, `address`, `before_photo` (data URL; PNG/JPEG/WebP, ≤1 MB). Optional: paired numeric `latitude` and `longitude` in range. The response includes a unique tracking ID and a route recommendation.
- `GET /api/reports/{id}` — authorized report detail with permitted evidence references, timeline and repair/inspection history.
- `GET /api/evidence/{evidence_id}` — authorization-checked private evidence. Unauthorized and unknown files both return 404.
- `POST /api/reports/{id}` — action field selects a server-validated transition:
  - `{action:"assign", department, worker_id}` — municipal/system admin only; must select an active configured department and active field worker.
  - `{action:"work_start"}` — assigned field worker only; `assigned|needs_rework → in_progress`.
  - `{action:"repair", repair_note, after_photo}` — assigned worker only; `in_progress → repair_submitted`; evidence and each repair attempt are saved.
  - `{action:"verify", approved, checks:{"1":true,...,"5":true}, notes}` — inspector only; every check must be a boolean. Approval requires all true; rejection requires at least one false plus notes.

Statuses: `submitted`, `assigned`, `in_progress`, `repair_submitted`, `needs_rework`, `verified`.

## Notifications, analytics and administration

- `GET /api/notifications` — current user's notifications and unread count.
- `POST /api/notifications/{id}` — mark that recipient's notification read.
- `GET /api/workers` — municipal/system staff; active field-worker list for assignment.
- `GET /api/analytics` — municipal/system staff; actual database metrics and definitions.
- `GET /api/admin/users`, `POST /api/admin/users`, `POST /api/admin/users/{id}` — system administrator only; list/create/update role and active state.
- `GET /api/admin/config` — system administrator only; configured categories/departments.
- `POST /api/admin/config/categories` — create/update category, subcategory, department, priority, keywords, active status and escalation hours.
- `POST /api/admin/config/departments` — create/update department.
- `GET /api/admin/audit` — system administrator only; recent audit entries.
- `GET /api/admin/notifications` — system administrator only; in-app notification totals grouped by event type.
- `POST /api/demo/reset` — system administrator plus `NAGRIVANTA_DEMO_RESET=1`; refused if non-synthetic reports exist. Avoid enabling on any shared/production service.

All admin and workflow writes require a valid session and CSRF token. Errors are returned as bounded JSON messages; internal exception details are not returned to clients.
