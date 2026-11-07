Start Backend :- 

1. py -3.12 -m venv .venv 
2. alembic upgrade head 
3. uvicorn app.main:app --reload


<!-- Resend SMTP -->

Set these values locally in `backend/.env` using a Resend API key and a verified sender:

1. `SMTP_HOST=smtp.resend.com`
2. `SMTP_PORT=465`
3. `SMTP_USER=resend`
4. `SMTP_PASSWORD=<your-resend-api-key>`
5. `SMTP_FROM=SmartERP <your-verified-sender@example.com>`
6. `SMTP_USE_TLS=false`
7. `SMTP_USE_SSL=true`