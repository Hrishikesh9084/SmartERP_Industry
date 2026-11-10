Start Backend :- 

1. py -3.12 -m venv .venv 
2. alembic upgrade head 
3. uvicorn app.main:app --reload
4. Configure Gmail SMTP locally in `backend/.env`:

1. `SMTP_HOST=smtp.gmail.com`
2. `SMTP_PORT=587`
3. `SMTP_USER=<your Gmail address>`
4. `SMTP_PASSWORD=<your 16-character Gmail app password>`
5. `SMTP_FROM=SmartERP <your Gmail address>`
6. `SMTP_USE_TLS=true`
7. `SMTP_USE_SSL=false`

Create the app password in your Google Account under **Security > 2-Step
Verification > App passwords**. Use the generated app password, not your
normal Gmail password. Never commit it or put it in `render.yaml`.

OTP emails use a branded HTML layout, include a plain-text fallback, and are
marked as automatically generated with a no-reply instruction.