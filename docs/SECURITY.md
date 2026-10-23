# Security notes

## Implemented controls

- Password hashes use PBKDF2-HMAC-SHA256 with random salts and 310,000 iterations; passwords are never stored or returned in plaintext.
- Public registration can create only citizen accounts. Privileged account creation and role changes require an active system administrator. The last active system administrator cannot be removed.
- Opaque random session cookies are stored server-side by token hash, HttpOnly, SameSite=Lax, 12-hour expiry, Secure on Render/HTTPS. Logout deletes the session; password change revokes all existing sessions before creating a replacement.
- Failed sign-in attempts are throttled by normalized email. This is a lightweight demo control, not a full abuse-management system.
- CSRF tokens are required for authenticated mutations; supplied `Origin` headers must match the host. No CORS allowlist or wildcard is emitted.
- Every report/evidence read and workflow write is role- and record-checked in the API. Private evidence uses random server-generated names outside the static directory and `nosniff` response headers.
- SQL values are parameterized. Public JSON request size, string lengths, coordinate ranges, supported image MIME/signatures, and upload size are checked.
- Security headers include a restrictive Content Security Policy, frame denial, MIME sniffing denial, referrer policy and a limited permissions policy.
- Repair submissions and inspection decisions are append-only history records; administrative and workflow writes create audit events.

## Not a production security certification

- `http.server` is intended for a small demonstration, not hardened public service operation. Use a production server/reverse proxy, security review, secret rotation, observability and incident response before real users.
- Image data is signature-checked but not decoded/re-encoded or EXIF-stripped. Add content scanning, canonical re-encoding, retention/deletion policies and image safety review.
- No MFA, email verification, password recovery, forced first-login password change or device/session list is implemented.
- Login throttling is email-keyed in one SQLite file; network-wide controls, CAPTCHA/abuse response, alerting and account recovery are not implemented.
- No encryption-at-rest layer or separate backup encryption is supplied by the app.
- Map library and tile requests go to the configured CDN/OSM services. There is no official asset dataset.
- SQLite/filesystem durability depends on host configuration. The current free Render service has no persistent disk configured.

Use synthetic records only until a dedicated threat model, privacy impact review, accessibility review, retention policy and operational review are complete.
