# UAT Guide — AI Agent OS (Local MVP)

Phase 18 adds a local User Acceptance Testing (UAT) and feedback system for internal team and client demos.

## Quick links

| Page | URL |
|------|-----|
| UAT dashboard | `/uat/` |
| UAT sessions | `/uat/sessions/` |
| New session | `/uat/sessions/new/` |
| Feedback board | `/uat/feedback/` |
| Report feedback | `/uat/feedback/new/` |
| UAT report (print) | `/uat/report/` |
| CSV export | `/uat/feedback/export.csv` |

## Create a UAT session

1. Log in as **owner** or **admin** (`admin@example.com` / `Admin123!` in local demo).
2. Open **UAT / Feedback** in the sidebar or go to `/uat/`.
3. Click **New UAT session**.
4. Enter title, audience, facilitator, and optional summary.
5. A default MVP checklist (16 sections) is created automatically.

Alternatively, run:

```bash
python scripts/seed_uat_checklist.py
```

This creates an idempotent **MVP Demo UAT** session for the `demo-company` tenant.

## Run demo and mark checklist

1. Open the session detail page (`/uat/sessions/{id}/`).
2. Follow each checklist section during the demo (see `docs/CLIENT_DEMO_SCRIPT.md`).
3. For each item, set status: **Passed**, **Failed**, **Blocked**, or **Skipped**.
4. Add notes for failures or questions.
5. **Sales managers** can update checklist items; **owners/admins** can complete and sign off.

## Record feedback

- Use **Report Feedback** in the top bar from any page (prefills module and URL).
- Or open `/uat/feedback/new/?module=agents&url=/agents/`.
- Categories: bug, improvement, feature request, UX, content, agent quality, security, production blocker, question.
- Priorities: low, medium, high, critical.

**Sales reps** can submit feedback and view their own items. **Managers and above** see all feedback and can triage.

## Export report

1. Open `/uat/report/` for a printable sign-off pack.
2. Click **Print / Save as PDF** in the browser.
3. Export feedback CSV from `/uat/feedback/export.csv` (owner/admin/manager).

## Sign-off rules

- **Mark completed**: owner/admin when demo checklist is finished.
- **Sign off MVP**: owner/admin only when **no critical open blockers** exist.
- Critical blockers = feedback with priority `critical` and status `open`, `triaged`, or `in_progress`.
- If blockers exist, sign-off shows a warning and is rejected.

## Use feedback for next phase

1. Export CSV after each demo.
2. Resolve or defer critical/high items before production planning.
3. Tag production blockers separately from demo UX notes.
4. Link feedback to UAT sessions when reporting client-specific issues.
5. Use the UAT report in stakeholder meetings alongside `/demo/report/`.

## Permissions summary

| Role | UAT dashboard | Create session | Checklist update | All feedback | Sign-off |
|------|---------------|----------------|------------------|--------------|----------|
| Owner / Admin | Yes | Yes | Yes | Yes | Yes |
| Sales manager | Yes | No | Yes | Yes | No |
| Sales rep | No | No | No | Own only | No |

All authenticated users can submit feedback via the top bar link.
