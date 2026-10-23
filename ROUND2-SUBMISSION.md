# Nagrivanta — Round 2 implementation update

## Project summary

Nagrivanta is a civic issue-management demo connecting citizen reports to a municipal assignment, field repair evidence and a separate inspection decision. It uses synthetic seed records and is not connected to a real municipal or heritage authority.

## Implemented in this working branch

- Server-side registration, login, logout, password change and role checks for citizen, municipal administrator, field worker, inspector and system administrator.
- PBKDF2 password hashes, server-side session records, 12-hour expiry, HttpOnly/SameSite cookies, production Secure-cookie behavior, CSRF/origin controls and email-keyed failed-login throttling.
- Five responsive role-oriented portals with authenticated navigation and protected APIs.
- Citizen-owned complaint submission/tracking, unique issue IDs, optional coordinates and private image evidence.
- Municipal review, specific worker assignment, and database-backed operational analytics.
- Assigned-worker-only work start and repair submission; append-only repair and inspection records; inspector-only five-check approval/rework decisions.
- Role-targeted in-app notifications, unread/read states and administrative audit events.
- System administrator user/role controls, department/category/routing configuration, escalation thresholds, notification metrics and audit view.
- Rule-based category/keyword suggestions with human-review disclosure.
- Heritage Watch map/list using submitted complaint coordinates only, with status/priority filtering and list fallback.
- Additive database migrations, legacy evidence migration to private storage, indexes, health endpoint and updated documentation.

## Tests run

- `python -m unittest discover -s tests -v` — 13 API tests passed on the last complete run. Rerun after any further changes.
- `node --check public/app.js` — passed on the last syntax check.
- `python -m py_compile server.py` — passed on the last syntax check.
- Chromium local workflow — the full citizen → municipal assignment → field repair → inspector approval → citizen resolution flow succeeded with no browser console errors or failed local responses.

Test results apply to the local working copy and temporary database only. They do not verify the public Render deployment.

## Deployment / data caveat

The existing `render.yaml` declares a Render free web service and does not attach a persistent disk. A read-only GET to the public health endpoint returned HTTP 200 and identified the running build as the existing `Nagrivanta demo API`; this working branch is not deployed. No GitHub push or Render deploy was performed. SQLite and evidence retention across Render restart/redeploy is not verified and must not be claimed. Use an eligible persistent disk for both database and uploads, back up the current production database first, and test the additive migration against a copy before rollout.

## Known limitations

- This is still a hackathon-scale Python `http.server` application, not a production-certified municipal service.
- No email/SMS/WhatsApp/push, MFA, email verification, password recovery, first-login reset, image re-encoding/EXIF removal, or malware scanning is configured.
- Map tiles come from OpenStreetMap and show reports only; no verified heritage asset dataset exists.
- Category names, sample departments, priority and escalation defaults are illustrative. The seeded records are synthetic.
- Review `docs/SECURITY.md`, `docs/DATABASE.md`, `docs/API.md` and the root README before demonstrating or deploying.

## Working copy

Local branch: `round2-hardening`. Changes have not been pushed to the source repository or deployed to the linked service.
