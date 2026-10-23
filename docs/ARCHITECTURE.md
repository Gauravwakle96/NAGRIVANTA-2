# Nagrivanta architecture

## System boundary

```text
Browser (HTML/CSS/JS)
  ├─ same-origin JSON API requests
  ├─ session cookie: opaque, HttpOnly, SameSite=Lax, Secure on Render/HTTPS
  ├─ CSRF header on authenticated mutations
  └─ optional Leaflet + OpenStreetMap tiles for submitted coordinates
       ↓
Python standard-library ThreadingHTTPServer
  ├─ request-size and field validation
  ├─ session lookup, role checks and record-level authorization
  ├─ workflow transition rules, notifications, audit events
  ├─ SQLite transactions and additive schema migration
  └─ private evidence file service with per-report access checks
       ↓
SQLite file + private uploads directory
```

No separate SPA build, third-party Python dependency, official identity provider, mail/SMS provider, municipal API, or heritage register is integrated. The external map tile/CDN requests are browser-side only and do not supply complaint or account data to the map provider beyond ordinary tile requests and submitted map center/zoom.

## Workflow and trust boundaries

1. Public registration can create only a `citizen`. Sign-in validates a PBKDF2-SHA256 password hash and creates a random server-side session token; the database stores a SHA-256 hash of that cookie token.
2. Every protected API call resolves the account and current role from SQLite. UI navigation is convenience only; it is not an authorization control.
3. Report list/detail and evidence access are additionally scoped to the citizen owner, assigned worker, inspection queue/history, or staff privilege.
4. Citizen submissions are stored with a unique tracking ID, optional coordinates, configured category route, report event and private evidence metadata.
5. Municipal administrators assign to an active configured department and a specific active `field_worker` account.
6. Only the assigned worker can start work and submit repair notes/evidence. Only an `inspector` can record the five checks. Approval requires all five checks to be true; rejection requires a failed check and notes.
7. Work submissions and each inspection decision are append-only history rows. The current report status is a projection for queueing and display; event history is retained for traceability.
8. Relevant notifications are created for owners, assignees, inspectors and municipal administrators. Notifications are in-app only.

## Design choices

- **Explainable triage:** configured category keywords and departments produce deterministic suggestions. The response says rule-based and requires human review; no confidence score is invented.
- **SQLite:** appropriate for a single-instance hackathon demo. A multi-instance or high-availability deployment would need a server database and an explicit migration/backup plan.
- **Filesystem evidence:** file bytes are outside `public/`; metadata, generated filename, content type, size, uploader and digest are stored in SQLite. The route uses authorization and `nosniff` headers. Production needs durable shared storage when multiple instances are involved.
- **Map:** Leaflet and OpenStreetMap display only report coordinates provided by a submitter. No guessed city center, official asset layer or heritage designation is implied.
- **Analytics:** calculations are made from persisted report and inspection rows. Empty denominators yield `null` rather than fabricated percentages.

## Operational considerations

`render.yaml` retains the existing free web-service plan and does not attach a disk. Application code supports configurable database and upload paths, but storage durability must be verified on an eligible host/mount before production use. See the root README for bootstrap and deployment steps.
