# Nagrivanta — Round 2 submission notes

## Project summary

Nagrivanta is a civic issue workflow prototype that connects citizen reports to a municipal work order, field-repair evidence and a separate inspector decision. It addresses fragmented tickets, opaque prioritisation and unverified closure with one traceable end-to-end journey.

## Working project

Run with `python server.py`, or deploy the Python app and provide the public URL here: **[add deployed project URL]**.

## Source repository

**[add Git repository URL]**

## Completed features

1. Citizen submits an issue with category, area, precise location, description and initial photo; the app returns a trackable ID.
2. Similar reports in the same location/category are linked to a master issue while preserving each original report and evidence.
3. Municipal view explains completeness and priority factors before a human assigns department and crew.
4. Field crew submits repair note and after-photo evidence.
5. Inspector completes a five-check review and records either verified closure or rework.
6. Citizen tracks status and full event timeline; synthetic dataset can be restored for a repeatable demo.

## Technology and implementation

- HTML/CSS/vanilla JavaScript frontend.
- Python standard-library JSON REST API.
- SQLite persistence via `sqlite3`.
- Explainable rules for completeness, priority and duplicate matching; no trained model or external integration is claimed.
- Synthetic demo records and images only.

## Changes from Round 1

Round 1 proposed React/TypeScript/Vite and FastAPI/Pydantic/SQLAlchemy. For a reproducible, dependency-light event MVP, the implementation uses browser-native HTML/CSS/JavaScript and Python's standard HTTP/SQLite libraries. This preserves a working end-to-end workflow and transparent logic while reducing setup risk. The demo roles are not real authentication; production security and live municipal integration are not claimed. The proposed trust signal is shown as evidence completeness—not a judgement about the reporter or truth of a claim.

## Three substantial Round 3 improvements

1. **Production-grade identity and role permissions:** add authenticated citizen, officer, crew and inspector accounts; enforce server-side authorization, secure image handling and audit access controls.
2. **Geospatial duplicate detection and field operations:** add a map-backed location workflow with PostGIS, distance-aware matching, ward boundaries and a reviewable merge/split process that preserves source reports.
3. **Tested reliability and multilingual access:** add automated end-to-end testing, accessibility review, resilient uploads/offline draft support and a multilingual citizen reporting flow, then publish measured test results.

## Limitations / demo disclosure

This is a prototype using synthetic data. Score weights and match thresholds are illustrative heuristics, not validated accuracy. It is not connected to a municipality, production map, SMS service, identity provider or trained AI model. Do not submit real citizen or sensitive data.
