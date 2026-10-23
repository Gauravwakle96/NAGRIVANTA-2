# Judge demonstration script (about 4 minutes)

## Before the demo

1. Run the application and create the first system administrator with `python server.py create-admin <email>` or configure the documented bootstrap secrets on the host. Do not paste credentials into source code or this document.
2. Sign in to the System Administrator portal. Create one municipal administrator, one field worker and one inspector. Share their passwords securely outside the demo.
3. Have the field worker and inspector sign in once if you want to show their portals; sign out between accounts. Confirm the app is using synthetic test data only.

## Walkthrough

1. **Citizen report:** register/sign in as a citizen. Select a matching category and subcategory, add a concise title, ward/locality, specific test location and synthetic evidence image. Optionally enter coordinates for a clearly labelled test location. Submit and note the generated `NG-…` ID.
2. **Explain the route:** show the configured department suggestion and explain that keyword/category routing is deterministic, not a trained model or official assignment. Human review remains required.
3. **Municipal review:** sign in as the municipal administrator. Find the new complaint, filter/search it and assign it to the correct demo department and named field-worker account. Point out that assignment is a protected server action.
4. **Field action:** sign in as the assigned field worker. Start work, add a repair note and upload a synthetic after-photo. Show the status becoming “Awaiting inspection.”
5. **Independent inspection:** sign in as inspector. Review original and repair evidence. Record all five checks and an inspection note. Approve only if the demo evidence supports each check; alternatively fail one check to demonstrate the rework loop.
6. **Citizen follow-up:** sign in as the report owner. Show the status, event timeline, allowed repair/inspection history and unread/read in-app notifications. Mention that other citizens cannot open this complaint's evidence.
7. **Heritage Watch and analytics:** optionally create a heritage-category demo complaint with a coordinate explicitly chosen as a test value. Show that the map depicts only submitted complaint locations; reports without coordinates remain listed. Open analytics to show database-derived values and definitions.
8. **Admin configuration:** show role controls, departments, category/keyword routing rules, escalation thresholds and recent audit events.

## Claims to avoid

Do not describe the app as integrated with a real city/authority, claim official heritage locations, claim AI confidence, promise response times, or report social/financial impact based on the four synthetic seed records. Do not enter a real person's home address, faces, sensitive issue photos or emergency reports.
