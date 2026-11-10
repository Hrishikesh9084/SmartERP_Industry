# SmartERP — Multi-tenant ERP SaaS foundation

SmartERP is a modular ERP SaaS codebase with a FastAPI backend, React/Vite frontend, PostgreSQL, SQLAlchemy, Alembic, tenant-scoped APIs, and optional email/SMS/payment integrations. It is an extensible engineering foundation; it is **not yet certified, audited, or ready to process live payroll/tax/payment data without your implementation review and jurisdiction-specific configuration**.

## Modules included in this release
- Authentication: email verification OTP, email OTP login, JWT sessions, configurable Super Admin bootstrap.
- HR: employee records, attendance, leave requests and approval.
- Payroll: period-based payroll calculation and payslips (configurable gross/deduction inputs; not a statutory payroll engine).
- Accounting: chart of accounts, balanced double-entry journal posting and trial balance. Journal lines use decimal amounts and enforce equal debit/credit totals.
- Procurement: supplier directory, purchase orders, line items and receiving into stock.
- RBAC: company-level role/permission matrix with owner bypass; seed permissions for manager/employee roles before onboarding.
- Security: database-backed OTP request limits, phone OTP verification via Twilio, audit records for posted journals.
- Billing: Razorpay order creation, Stripe Checkout Session creation, signature-verified webhook handlers. These are payment collection integrations, not a complete recurring subscription lifecycle.
- AI analytics: existing forecasting, inventory, customer clustering and expense anomaly endpoints.
- Operations: Docker Compose, PostgreSQL, Redis service, Alembic, health/readiness endpoints, pytest, Bandit, pip-audit CI.

## Requirements
Python 3.12 recommended; Node.js 22 LTS; Docker Desktop (optional); PostgreSQL 15+ for production.

## Local development — Windows PowerShell
```powershell
# Terminal 1
cd SmartERP_Industry
Copy-Item .env.example .env
# Edit .env and set POSTGRES_PASSWORD

cd backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# For Neon development, set DATABASE_URL to the pooled Neon URL with the
# postgresql+psycopg scheme and keep sslmode=require.
# Create/update schema using migrations (recommended)
alembic upgrade head
# Provision the platform Super Admin from SUPERADMIN_EMAIL/PASSWORD in .env
python scripts\provision_superadmin.py
# Optional: add repeatable development data for dashboard/module testing
python scripts\seed_demo_data.py
uvicorn app.main:app --reload

API docs: http://localhost:8000/docs

```powershell
# Terminal 2
cd SmartERP_Industry\frontend
npm install
npm run dev
```
Frontend: http://localhost:5173

The development seed is disabled when `APP_ENV=production`. It creates the
`demo@smarterp.local` account with password `DemoPassword123!`; change or
remove this development-only account before using a shared environment.

## Installable desktop and mobile apps

The React frontend is packaged from the same build for all supported clients:

- **Windows:** Electron NSIS installer or portable executable.
- **macOS:** Electron DMG/ZIP.
- **Android:** Capacitor Android project, targeting Android 13 (API 33) and newer.
- **iOS:** Capacitor iOS project, targeting iOS 16 and newer (including iPhone 14).
- **Browser/PWA:** Install SmartERP from a supported browser using the manifest.

From `frontend`, install dependencies and create the native projects:

```powershell
npm install
npx cap add android
npx cap add ios
```

Set `VITE_API_URL` in `frontend/.env` to the deployed HTTPS API before syncing mobile
projects. After `npm run mobile:sync`, set Android `minSdk = 33` in the generated
`android/variables.gradle` and iOS `IPHONEOS_DEPLOYMENT_TARGET = 16.0` in the
generated Xcode project. Open the projects with `npm run mobile:android` or
`npm run mobile:ios`, then build signed release packages in Android Studio/Xcode.

### Publishing the Android app on Google Play

The Android project is already created at `frontend/android` with application ID
`com.smarterp.industry`. A Windows `.exe` cannot be uploaded to Google Play; the
Play Store release must be an Android App Bundle (`.aab`).

Before creating a release:

1. Install Android Studio and a supported JDK, then set `JAVA_HOME`.
2. Deploy the FastAPI backend at a public HTTPS URL.
3. Set that URL in `frontend/.env`:
   `VITE_API_URL=https://api.example.com`
4. Run `npm run mobile:sync`.
5. Open `frontend/android` in Android Studio.
6. Create a private upload key, configure a signed **release** build, and run
   **Build > Generate Signed Bundle / APK > Android App Bundle**.
7. Upload the generated `.aab` to Google Play Console, complete the store
   listing, privacy policy, data-safety form, content rating, and testing track.

Do not use `localhost` for a store build: it refers to the individual user's
phone, not the development computer. Do not commit `backend/.env`, signing keys,
or provider credentials.

For desktop development and release:

```powershell
npm run desktop:dev
npm run desktop:build
```

`desktop:build` creates Windows installers/portable builds on Windows and macOS
DMG/ZIP builds on macOS. Signing certificates and store accounts are required
before distributing production packages.

### Deploying the API for mobile stores

The repository includes a Render Blueprint at [`render.yaml`](./render.yaml).
To create the public API required by Android and iOS:

1. Push this repository to GitHub.
2. In Render, choose **New > Blueprint**, select the repository, and apply
   `render.yaml`.
3. Enter the requested SMTP, Twilio, and super-admin secrets in Render.
4. Wait for the service health check to pass at `/health`.
5. Copy the generated `https://smarterp-api-....onrender.com` URL into
   `frontend/.env` as `VITE_API_URL`.
6. Run `npm run mobile:sync` before creating signed Android and iOS releases.

Do not put provider secrets in `render.yaml`, source control, or the mobile
bundle. The Blueprint marks those values as secret inputs.

## Production with Docker Compose
1. Copy root `.env.example` to `.env`; set a long random `POSTGRES_PASSWORD`.
2. Configure `backend/.env` with `APP_ENV=production`, a unique `SECRET_KEY`, PostgreSQL URL (Compose overrides it), SMTP/Twilio/payment credentials and frontend origin.
3. Run `docker compose up --build -d`. The API container runs `alembic upgrade head` before Uvicorn.
4. Put a TLS reverse proxy (Caddy/Nginx/managed ingress) in front; restrict database/Redis to private networking.

## Super Admin
Set `SUPERADMIN_EMAIL` and `SUPERADMIN_PASSWORD` in `backend/.env` before first boot.
The account is provisioned with the password currently configured there. The
development fallback is only used when those variables are absent. Changing
environment variables later requires rerunning `python scripts\provision_superadmin.py`
to rotate the existing account password. Never use sample credentials in a
shared or production environment.

Super Admin and company administrator accounts are stored in the `users` table:
Super Admin uses `role=super_admin` and no company; a company administrator uses
`role=owner` and is linked to a company. There are intentionally no separate
administrator tables because authentication and role checks are centralized.

Workspace deletion is a soft delete. A company owner can delete their own
workspace from the Admin Panel, while Super Admin can delete or restore any
workspace. Business records are retained and deleted workspaces cannot sign in
or access company APIs.

## Integrations
- SMTP: set `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, your Gmail address as `SMTP_USER`, a 16-character Google app password as `SMTP_PASSWORD`, and `SMTP_FROM=SmartERP <your-gmail-address>`. Use `SMTP_USE_TLS=true` and `SMTP_USE_SSL=false`. Google 2-Step Verification must be enabled before creating the app password; never use or commit your normal Gmail password.
- OTP emails are sent as branded HTML with a plain-text fallback and are marked as automatically generated. Set `SMTP_REPLY_TO` only if replies should go to a monitored address.
- Twilio: set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`. SMS verification only works after provider configuration and an E.164 phone number.
- Razorpay: configure `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`; configure webhook URL `/api/billing/webhooks/razorpay`.
- Stripe: configure `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`; configure webhook URL `/api/billing/webhooks/stripe`.

## Main API routes
- `/api/dashboard`, `/api/products`, `/api/customers`, `/api/sales`, `/api/expenses`
- `/api/hr/employees`, `/api/hr/attendance`, `/api/hr/leaves`, `/api/hr/payroll/runs`
- `/api/accounting/accounts`, `/api/accounting/journals`, `/api/accounting/trial-balance`
- `/api/purchasing/suppliers`, `/api/purchasing/orders`, `/api/purchasing/orders/{id}/receive`
- `/api/admin/permissions`
- `/api/auth/phone/request-otp`, `/api/auth/phone/verify`
- `/api/billing/checkout`, `/api/billing/subscriptions`
- `/api/ai/*` analytics and forecasting routes

The FastAPI application registers these route groups from `backend/app/main.py`;
they are tenant-scoped through the authenticated user and company permissions.

## RBAC permissions
Examples: `hr.employees.read`, `hr.employees.write`, `hr.attendance.read`, `hr.attendance.write`, `hr.leave.read`, `hr.leave.write`, `hr.leave.approve`, `payroll.read`, `payroll.run`, `accounting.read`, `accounting.accounts.write`, `accounting.journals.write`, `purchasing.read`, `purchasing.suppliers.write`, `purchasing.orders.write`, `purchasing.receive`, `rbac.manage`. Owners bypass these checks. Configure non-owner roles via `PUT /api/admin/permissions`.

## Test and security checks
```powershell
cd backend
pytest -q
bandit -r app -ll
pip-audit -r requirements.txt
```

## Important production gaps to close before launch
- Replace the initial metadata migration with reviewed, immutable Alembic revisions for every schema change; test upgrades and rollbacks against a disposable PostgreSQL database.
- Configure DB-backed rate limiting for distributed deployments (the included table-based limiter is shared across API workers but adds DB write load; Redis-backed throttling is recommended at scale). Add CAPTCHA, lockouts and alerting.
- Complete password reset, MFA, session revocation, role provisioning UI, full audit coverage and tenant-isolation tests. Add PostgreSQL RLS as defense in depth.
- Payroll is a calculation scaffold only: implement applicable Indian payroll rules (PF, ESI, TDS, professional tax, gratuity, payslip formats, statutory filings), rounding and approvals with a qualified payroll/accounting professional.
- Accounting needs immutable posted entries, reversal workflows, fiscal periods, tax rules, bank reconciliation, AR/AP, closing controls and external audit review before financial use.
- Billing needs signature verification for every event, idempotency/event ledger, plan entitlements, renewals, cancellations, refunds, dunning and reconciliation. Validate currency minor-unit handling per provider.
- SMS/email delivery, sender registration, privacy notices, consent, retention and local telecom/data-protection requirements are deployment responsibilities.
- Add real integration tests, frontend build checks, load tests, backup/restore drills, error tracking, structured logs, metrics dashboards, secrets management and TLS.

## Honest status
The repository includes the listed backend building blocks and deployment scaffolding. The UI is still a starter UI and does not yet expose every new module. The code has not been validated against live Razorpay/Stripe/Twilio/SMTP credentials or a production PostgreSQL cluster. Run tests, review generated migrations and complete the production gaps before using real company data.
