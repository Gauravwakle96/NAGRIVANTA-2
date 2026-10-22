# Nagrivanta — Round 2 project update

## Project summary

Nagrivanta is a synthetic-data civic workflow prototype connecting citizen reports to a suggested municipal department, assigned work, field evidence and a separate human inspection decision.

## Working project and source

- Working demo: https://nagrivanta-round2.onrender.com/
- Source repository: https://github.com/Gauravwakle96/NAGRIVANTA-2

The published URL and repository should be rechecked after the updated source is deployed. The source changes in this package are not automatically published to GitHub or Render.

## Completed features in the current code

1. Citizen report form with description, location and evidence, generating a unique issue ID.
2. Database-seeded multi-department categories and subcategories, including roads, heritage, water/drainage, waste, gardens/environment, electrical, health, encroachment, fire/disaster and public facilities.
3. Configured department suggestions and a keyword-based triage fallback, labelled rule-based and requiring human review.
4. Duplicate grouping preserves original source reports and evidence.
5. Municipal assignment, crew repair evidence and a separate inspector decision.
6. Heritage Watch list and a heritage-specific review checklist; no legal status or damage is automatically asserted.
7. Additive schema migration preserves existing report IDs and history.

## Technology

- HTML, CSS and vanilla JavaScript.
- Python standard-library HTTP/JSON API.
- SQLite (`sqlite3`) with additive migration for department/category/routing configuration.
- Rule-based classification, priority and duplicate recommendations; no trained AI claim.

## Round 1 plan changes

The original plan named React/TypeScript/Vite and FastAPI/Pydantic/SQLAlchemy. The existing dependency-light UI and Python standard-library API were retained. The multi-department catalog and rule-based route suggestions extend the workflow without claiming a live municipal integration.

## Three substantial Round 3 improvements

1. Secure identity, server-side role permissions, privacy controls and safe evidence storage.
2. Authorized geospatial data integration, ward-aware matching and a provenance-backed Heritage Watch map.
3. End-to-end reliability, accessibility, multilingual reporting, offline/resilient uploads and measured evaluation.

## Limitations / disclosure

This is a prototype using synthetic records. The four role views remain demo navigation tabs and are **not authentication or access control**. The API is not suitable for real citizen data. Department assignments and priorities are illustrative, not verified PMC commitments. No municipal API, official heritage registry, map provider, live identity system or trained AI model is integrated. Render/SQLite persistence must be verified before claiming durable storage. Do not submit real personal or sensitive information.

## Verification

After this code update, run `python -m unittest discover -s tests -v` and `node --check public/app.js`. Report only the test results actually observed for the final version.
