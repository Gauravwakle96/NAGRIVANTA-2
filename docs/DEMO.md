# Judge demo guide

## Start

1. Run `python server.py` locally or open the deployed site root.
2. Select **Explore Live Demo**. No real account or password is needed.
3. Choose **Start Guided Tour** to begin as Citizen, or **Explore Freely** and open any role card.
4. The top bar displays the synthetic-data notice, a server-authorized role selector, **Reset demo**, and **Exit demo**.

Each launch creates five distinct demo accounts with generated credentials that are never exposed to the browser. All roles share one random demo-group identifier, and every demo report/evidence item is marked synthetic and scoped to that group. The session expires after one hour. Inactive groups are removed after six hours when no unexpired session remains. No ordinary users or complaint records are used. Reset operates only on the active group and its files; it does not reset other visitors' demos.

## Guided walkthrough

1. **Citizen** — review the synthetic complaint list, open a sample timeline, and optionally submit a new clearly synthetic report with a sample location/evidence. A duplicate warning is explainable and never prevents a separate report after confirmation.
2. **Municipal Administrator** — review the road-work queue, see the category/departments suggested by configured rules, and assign a sample complaint to the demo field worker.
3. **Field Worker** — open assigned work, start a job, submit a completion note and an isolated private image. The records use the existing persisted workflow.
4. **Inspector** — inspect evidence and the five-check checklist. Approve only when all checks pass or fail a check and request rework.
5. **Citizen follow-up** — return to the same demo citizen. See the status, chronological workflow history and related in-app notifications. A verified sample can accept one satisfaction rating with an optional comment.
6. **System Administrator** — inspect only the demo group's synthetic operational metrics and audit events. Global account management and routing configuration are deliberately disabled in this public role.

Use **Continue tour** to move through roles or change roles directly to explore. The guided tour explains the next action; it does not fake a completed workflow transition. Actual state changes are sent to the backend and appear in the stored report timeline.

## Language and help

Use the English/Marathi/Hindi selector on the landing page or in the workspace. The compact deterministic Civic Assistant answers common workflow questions in the selected language. It does not access private report records, use an unconfigured LLM, or contact an authority.

## Safety and operational notes

- The on-screen label is **INTERACTIVE DEMO — Uses synthetic demonstration data.** Demo complaints, people, locations, inspection decisions, feedback and analytics are fabricated examples, not government records or measured public impact.
- Do not enter real addresses, faces, sensitive documents, emergencies or confidential details. Uploaded demo evidence is private to the demo group.
- Demo role switching is server-side and only maps to one of the group's five generated identities. Public demo users cannot manage ordinary accounts, global configuration, or read/write another group.
- Public launches are rate-limited per client address in-process. A multi-instance production deployment would need shared rate limiting and a dedicated persistence/abuse strategy.
- The legacy `NAGRIVANTA_DEMO_RESET` system-admin reset applies only to old ungrouped synthetic records, refuses ordinary reports and public demo groups, and is not required for the public launcher.
- The Render blueprint remains on a free ephemeral filesystem. A restart may remove database and evidence files; use and verify a persistent mount before promising durable demo state.
