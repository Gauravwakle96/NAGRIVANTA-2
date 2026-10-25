# Security notes

## Implemented controls

- Password hashes use PBKDF2-HMAC-SHA256 with random salts and 310,000 iterations; passwords are never stored or returned in plaintext.
- Public registration can create only citizen accounts. Privileged account creation and role changes require an active system administrator. The last active system administrator cannot be removed.
- Municipal administrators, field workers, and inspectors have explicit department assignments. Municipal administrators are scoped to their department's reports, workers, assignment actions, and analytics; worker/inspector report access is department-checked server-side. Legacy department-scoped accounts without an active assignment fail closed until a system administrator assigns them.
- Opaque random session cookies are stored server-side by token hash, HttpOnly, SameSite=Lax, 12-hour expiry, Secure on Render/HTTPS. Logout deletes the session; password change revokes all existing sessions before creating a replacement.
- Public demo launches create five role identities on the server with random, undisclosed credentials and one random group. Demo reports and evidence carry the group ID; report listing, detail, evidence, duplicate matching, worker selection, notifications, metrics, reset and audit reads are group-scoped. Demo sessions expire after one hour.
- Ordinary users and operational analytics exclude both isolated demo groups and legacy synthetic reports; global audit and notification monitoring omit demo-account activity.
- Demo role switching is allowed only for an existing demo session and selects a pre-created role identity in the same group; ordinary accounts cannot switch roles. Demo System Administrator access is limited to synthetic-only analytics/audit; global user and configuration APIs reject demo users. Demo-to-ordinary assignments are rejected.
- Demo reset deletes only the active group after session/CSRF checks. Public launcher requests are origin-checked and rate-limited per client address in-process; inactive groups are cleaned up only after six hours and when no live session remains.
- Failed sign-in attempts are throttled by normalized email. This is a lightweight demo control, not a full abuse-management system.
- CSRF tokens are required for authenticated mutations; supplied `Origin` headers must match the host. No CORS allowlist or wildcard is emitted.
- Every report/evidence read and workflow write is role- and record-checked in the API. Private evidence uses random server-generated names outside the static directory and `nosniff` response headers.
- SQL values are parameterized. Public JSON request size, string lengths, coordinate ranges, supported image MIME/signatures, and upload size are checked.
- Security headers include a restrictive Content Security Policy, frame denial, MIME sniffing denial, referrer policy and a limited permissions policy.
- Repair submissions and inspection decisions are append-only history records; administrative and workflow writes create audit events.
- Duplicate checks return only a generic match reason/status, not another citizen's ID, description, address or identity. A potential match cannot silently prevent submission; explicit confirmation is required and a separate report remains independently tracked.
- Citizen feedback is accepted only from the owner after verified closure, stored as a separate row and write-once. Synthetic feedback is separated from actual feedback analytics.

## Not a production security certification

- `http.server` is intended for a small demonstration, not hardened public service operation. Use a production server/reverse proxy, security review, secret rotation, observability and incident response before real users.
- Image data is signature-checked but not decoded/re-encoded or EXIF-stripped. Add content scanning, canonical re-encoding, retention/deletion policies and image safety review.
- No MFA, email verification, password recovery, forced first-login password change or device/session list is implemented.
- Login throttling is email-keyed in one SQLite file; network-wide controls, CAPTCHA/abuse response, alerting and account recovery are not implemented.
- The public demo limiter is in-process and address-based; it does not coordinate across multiple app instances or reverse proxies. Add shared rate limiting and abuse monitoring before broader public exposure.
- Demo group cleanup is launched on new demo-session creation, so an abandoned deployment with no new launches may retain synthetic rows/files. Add scheduled retention for long-running deployments and verify no live demo session is being removed.
- Temporary demo identities share the regular users table but are flagged and hidden from normal user administration. Review data retention and exercise the unauthenticated launcher under the actual proxy/Render topology before a public event.
- No encryption-at-rest layer or separate backup encryption is supplied by the app.
- Map library and tile requests go to the configured CDN/OSM services. There is no official asset dataset.
- SQLite/filesystem durability depends on host configuration. The current free Render service has no persistent disk configured.

Use synthetic records only until a dedicated threat model, privacy impact review, accessibility review, retention policy and operational review are complete.
