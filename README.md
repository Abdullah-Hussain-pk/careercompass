# CareerCompass

An explainable career exploration application for M. Abdullah Hussain, F-24-BSSE-099, BSSE 5B, Foundation University Islamabad. Built from the supplied CareerCompass proposal and presentation, with the requested replacement stack: **React + NestJS + Supabase**.

## Run the local demo

Install Node.js 22.12 or later, open a terminal in this folder, then run:

```powershell
npm.cmd ci
Copy-Item .env.example .env
npm.cmd run dev
```

Open **http://localhost:5174**. The API listens on port 4001. Wait for both processes to report ready on first startup. No Supabase account or Docker installation is needed for the demo. Use the four demo workspace buttons on the sign-in page.

| Role | Email |
| --- | --- |
| Student | student@careercompass.demo |
| Counsellor | counsellor@careercompass.demo |
| Administrator | admin@careercompass.demo |
| Industry expert | expert@careercompass.demo |

All demo accounts use `CompassDemo!2026`. These credentials are deliberately public and must never be deployed. The demo student has a synthetic assessment so the dashboard can be explored immediately. Register a new account to test the empty-state and assessment journey.

Demo data runs in embedded PostgreSQL and is saved to `.data/demo.snapshot.gz` after a short idle period and on graceful shutdown. Stop with Ctrl+C and let the API close. Use only one API process for a given demo data path. Abrupt process termination can lose the latest changes. Demo mode is not a multi-user production database.

## Included workflows

- Students: registration, optional academic profile, 48 RIASEC activities, 16 skill ratings, saved assessment drafts, top-10 career matches, three score contributions, relevant/not-relevant feedback with optional ratings, skill roadmaps and progress, booking, consent withdrawal and account deletion.
- Counsellors: 30-minute availability, sessions, consent-gated assessment context and private session notes.
- Industry experts: structured profile proposals with supporting sources and approval status.
- Administrators: career creation/editing/deactivation, expert moderation, role assignment, editable scoring weights and operational analytics.

Dark responsive interface with mint, violet and peach accents, native SVG interest charts, keyboard-operable forms and dialogs, loading/error/empty states and reduced-motion support.

## Supabase configuration

1. Create your Supabase project. In `.env`, set `APP_MODE=supabase`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `DATABASE_URL`. Use the project dashboard’s PostgreSQL connection string, preferably its session pooler where direct IPv6 is unavailable. Keep `DATABASE_SSL=true`.
2. Run `npm.cmd run db:setup` from this folder. This applies `supabase/migrations/001_initial.sql` and inserts the 42 starter career profiles. It creates no live sample accounts.
3. Configure email/password Auth in Supabase. Set the local Site URL to `http://localhost:5174` while developing. Enable email confirmation for public use. Set access-token expiry to **1800 seconds** to match the proposal.
4. Start the app. Register, confirm your email if required, then sign in once. A student profile is created using the verified Supabase identity.
5. Bootstrap the first administrator from a trusted operator terminal:

```powershell
npm.cmd run staff:role -- your-email@example.com admin
```

Register the other staff accounts normally, then assign counsellor/expert roles using User management. Roles are stored in the application database, never accepted from public signup metadata. `staff:role` is an operator bootstrap/recovery command; use the UI for normal role changes.

The browser talks only to NestJS. Supabase Auth tokens are held in HTTP-only cookies and checked against Supabase `/auth/v1/user` on protected requests. The backend connects to Supabase PostgreSQL using a privileged server credential. RLS is enabled and `anon`/`authenticated` table access is revoked; there are intentionally no browser-facing data policies. This does not replace backend authorization. Do not expose database/service keys through `VITE_*` variables.

If PostgreSQL reports an untrusted certificate, obtain your provider’s CA certificate and set `NODE_EXTRA_CA_CERTS` before starting Node. Do not disable certificate verification. The schema belongs in a new project; the initial migration is idempotent for this version and is not a general schema-upgrade tool.

## Verify and build

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
npm.cmd run evaluate -- path-to-deidentified-pilot.json
```

Tests use isolated in-memory databases and temporary snapshot files, not your configured Supabase database. The suite covers scoring endpoints, role restrictions, public role injection, assessment validation, draft persistence, simultaneous booking, consent revocation, private notes, approval atomicity, weights, deactivation, analytics and deletion cascades. A separate test verifies snapshot save and reload.

The evaluation script compares interest-only, skill-only and hybrid variants on precision@5 and nDCG@5. Run `npm.cmd run evaluate` for the input format. Rate the common pooled candidate set across variants and keep identities out of exported data. No pilot results are invented.

## Deployment

Use a Node server/container behind an HTTPS reverse proxy. The production server serves the built React assets and `/api` from one origin.

```powershell
npm.cmd run build
# Configure APP_MODE=supabase, NODE_ENV=production, COOKIE_SECURE=true
# Set WEB_ORIGIN to your exact public HTTPS origin and supply server secrets.
npm.cmd start
```

Production refuses demo mode and insecure cookies. `HOST` defaults to `0.0.0.0` in production and loopback in development. `PORT` defaults to 4001. The Dockerfile provides a two-stage build; run the database setup from a trusted development/operator environment before deploying. Docker deployment is supplied but was not executed during delivery. Provision provider backups, restore procedures, TLS and monitoring separately. The built-in rate limiter is per process; use a shared limiter before horizontal scaling.

## Project structure

```text
apps/web/src/         React UI, CSS and API client
apps/api/src/         NestJS controller, authentication, services and storage
packages/shared/     Domain types, questionnaire, scoring and starter careers
supabase/migrations/ PostgreSQL schema, constraints and RLS restrictions
scripts/             Database setup, trusted role bootstrap and pilot evaluation
tests/               Mathematics, API integration and snapshot tests
docs/                Complete setup guide and project documentation in Word
```

## Evidence limits

The 48 activities are original educational items based on the RIASEC categories, not the standardised O*NET questionnaire. The 42 career profiles contain editorial starter interest vectors, required levels and degree lists. The O*NET background links do not validate these numeric values or Pakistani market demand. No salary or demand claims are made. Review the content with a qualified expert, conduct the planned pilot and measure the deployment before claiming accuracy, usability, 50-user latency or 99% availability.

The score is a weighted similarity estimate, not a probability of success. Learning progress is self-reported and does not silently increase assessed skills. No payments, video calling, mobile app, deep-learning model or production password-recovery UI is included. Live Supabase connectivity, email delivery and cloud deletion need verification after you provide credentials. Database/back-up retention and Supabase infrastructure logs are governed by the operator/provider beyond application-level deletion.

## References

- [Supabase verified user lookup](https://supabase.com/docs/reference/javascript/auth-getuser)
- [Supabase row-level security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [NestJS authorization](https://docs.nestjs.com/security/authorization)
- [O*NET Interest Profiler background](https://www.onetcenter.org/reports/IP_Manual.html)

The original DOCX and PPTX remain unchanged in Downloads. Their FastAPI technology proposal is superseded by the user’s React/NestJS/Supabase decision. Their benchmark and research claims are not presented as newly verified findings.
