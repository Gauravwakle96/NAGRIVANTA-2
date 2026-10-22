# Nagrivanta — Round 2 MVP

A judge-ready, synthetic-data prototype for the core civic issue → assignment → repair evidence → human inspection loop.

## Run locally

Requirements: Python 3.10+ (the app uses only the Python standard library).

```bash
python server.py
```

Open <http://localhost:8000>. The app creates `nagrivanta.sqlite3` and seeds four synthetic issues on first run. It has no login, third-party API, or external service dependency. Use **Reset demo data** to restore the sample dataset.

To change the port/database path:

```bash
PORT=8080 DATABASE_PATH=/path/to/nagrivanta.sqlite3 python server.py
```

## Judge walkthrough

1. Open **Citizen**. Select **Use synthetic sample evidence instead**, complete the report fields, and submit. Save the generated `NG-…` issue ID.
2. Open **Municipal**. Review the priority breakdown and completeness signals, then assign a department and crew.
3. Open **Field crew**. Add a repair note, use synthetic after-evidence, and submit the repair for inspection.
4. Open **Inspector**. Complete all five checks and add an inspection note to verify closure. Or return it for rework to see that alternate path.
5. Return to **Citizen** and track the issue by ID. Use an existing duplicate sample (NG-DEMO-101/102) to see source-report preservation and duplicate linkage.

The seeded `NG-DEMO-104` is already awaiting inspection, so judges can explore the inspector workflow immediately.

## Completed features

- Citizen report form: title, category, ward, specific location, description and image evidence; image resized client-side.
- Unique issue IDs and citizen-visible status timeline.
- SQLite-backed REST endpoints and validated state transitions.
- Rule-based report-completeness signal with explicit factors; deliberately not a truthfulness/person score.
- Explainable rule-based priority recommendation with category, safety-keyword, corroboration, evidence and baseline factors.
- Duplicate grouping by category, area/location and text overlap; original source reports and evidence remain separate.
- Municipal assignment and crew work-order queue.
- Before/after evidence capture, five-point inspection and explicit human verified/rework decision.
- Synthetic seed cases, reset control, responsive interface, error/empty states and image limits.

## Implementation details

- UI: semantic HTML, CSS and vanilla JavaScript; no build step or external JS library.
- API: Python standard-library `http.server`, JSON REST routes and SQLite (`sqlite3`).
- Persistence: local SQLite database on the server. A deployment must use persistent storage if records should survive restarts.
- Demo roles are navigation only, **not authentication or access control**. Do not use real citizen data or expose this prototype as a production municipal service.
- All seeded evidence and records are synthetic. The rule scores are transparent demo heuristics, not validated models or real-world performance claims. No live municipal, map, SMS, identity or AI service is integrated.

## Round 1 plan changes

The proposal named React + TypeScript + Vite, FastAPI + Pydantic + SQLAlchemy, and SQLite. This MVP uses a dependency-free HTML/CSS/JavaScript interface and Python standard-library JSON API with SQLite. The change keeps the judge link easy to run and avoids build/dependency failures in the short event window. The workflow and explainable rules remain aligned with the proposal. Real authentication, hardened API permissions, production deployment, geospatial services and any municipal integration remain out of scope.

## Tests

Run the API smoke/regression tests with:

```bash
python -m unittest discover -s tests -v
```

The tests use an isolated temporary SQLite database and cover the main state transitions, validation, duplicate linkage and inspection gate.


## Public demo deployment

A `render.yaml` Blueprint and `Procfile` are included for a quick Python web-service deploy. Push this folder to your Git repository, connect the repository to Render, and deploy the Blueprint. Then open the service URL and confirm `/api/health` responds with `ok: true`. Add the resulting public URL to the submission form. SQLite is a local file: attach persistent storage or use another durable database if demo records must survive service restarts/redeployments.
