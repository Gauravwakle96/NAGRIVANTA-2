# Nagrivanta — Multi-department civic workflow demo

Nagrivanta is a synthetic-data prototype for a civic report → triage recommendation → department assignment → field evidence → human inspection workflow. It now includes a database-seeded multi-department issue catalog and a Heritage Watch list. It is **not connected to PMC or another municipal system** and is not ready for real citizen records.

## Run locally

Requirements: Python 3.10+; runtime uses only the standard library.

```bash
python server.py
```

Open <http://localhost:8000>. SQLite is created at `nagrivanta.sqlite3`; on first run, four synthetic demo reports and the catalog are seeded. Set a different database path with `DATABASE_PATH=/path/to/nagrivanta.sqlite3`.

To expose the reset button for a disposable synthetic demo only:

```bash
NAGRIVANTA_DEMO_RESET=1 python server.py
```

Reset is disabled by default so a public deployment cannot delete added records through the demo control.

## Judge walkthrough

1. Open **Citizen**, choose a department area and subcategory, and use the sample evidence button.
2. Try **Suggest category (rule-based demo)** with a description such as “Garbage is overflowing from a public bin.” Review the suggestion; it is not an AI model or an official decision.
3. Submit the report. Its recommended department is derived from the configured catalog; an operator can choose another active department during assignment.
4. Use **Municipal**, **Field crew**, and **Inspector** to complete the assignment, repair-evidence and human-inspection stages.
5. Use **Heritage watch** to review reported heritage-category cases. It is a list only; no official heritage register or map is connected.
6. Use existing synthetic duplicate samples `NG-DEMO-101` and `NG-DEMO-102` to see linked reports remain separate records.

The demo role switcher is for walkthroughs only; it is **not authentication or access control**. Do not expose real personal or municipal data through this build.

## Implemented in this upgrade

- Additive SQLite migration adds `subcategory`, `suggested_department`, and `synthetic` columns without changing existing complaint IDs or deleting reports.
- Database tables for `departments`, `issue_categories`, and `routing_rules`, seeded with configurable multi-department categories and proposed routing defaults.
- Citizen form loads the category/subcategory catalog from the API and displays a suggested department.
- Legacy category names (`Road damage`, `Water & drainage`, `Streetlight`, `Waste`, `Other`) remain accepted by the existing report API and are mapped to the expanded category groups.
- Water, waste, heritage and other department recommendations are exposed in a transparent response; routing and priority defaults are demo configuration, not verified municipal service commitments.
- Keyword-overlap triage endpoint (`POST /api/triage`) is explicitly labelled **rule-based** and returns an explanation without a confidence percentage.
- Heritage Watch list and a heritage-oriented five-item inspection checklist; reports remain unverified allegations until assessed by authorized personnel.
- Emergency notice: the ordinary report form is not an emergency response channel.
- Original duplicate, assignment, repair-evidence and inspector-closure workflow retained.

## API

- `GET /api/health` — health check.
- `GET /api/catalog` — active departments and category/subcategory routing defaults.
- `POST /api/triage` — transparent keyword-rule suggestion; not trained AI.
- `GET /api/reports`, `GET /api/reports/{id}`, `POST /api/reports`, `POST /api/reports/{id}` — existing demo report workflow.
- `POST /api/demo/reset` — resets to synthetic seed records only when `NAGRIVANTA_DEMO_RESET=1`; disabled by default.

## Data and configuration

The seeded department names and routing rules are **proposed examples**, not confirmed PMC department assignments. No PMC data, Open Data API, live municipal service, official heritage register, map provider, external AI, SMS, identity provider, or trained model is integrated. The official Open Data reference should be reviewed for its current dataset/API documentation before building an importer; this app does not scrape or assume that a departments page is a data API.

Priority scores are illustrative heuristics, not measured outcomes. The rule-based suggestion is not trained AI, and all routing/classification decisions require human review.

## Security and deployment limitations

- The current four-role UI is a demo role switcher, **not server-side role-based authentication**. API routes are not protected by user identity. Use synthetic records only; do not deploy for real citizen use.
- The default SQLite database is a local file. Render free services may not retain filesystem writes across redeploys/restarts unless persistent storage is explicitly configured. Do not claim durable storage without verifying the deployment plan.
- Uploaded demo evidence is stored as data URLs in SQLite. Production use needs a reviewed file-storage strategy, access control, retention policy, upload validation and privacy/security review.
- No credentials or external integrations are required. Do not add secrets to Git.

## Tests

```bash
python -m unittest discover -s tests -v
node --check public/app.js
```

The API tests use an isolated temporary SQLite database and cover the existing workflow plus catalog, heritage routing, waste/water routing and rule-based triage. Passing tests do not establish production security or real-world model performance.
