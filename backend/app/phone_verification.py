import os
from twilio.rest import Client


def get_twilio_client():
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        raise RuntimeError("Twilio credentials are missing.")

    return Client(account_sid, auth_token)


def get_verify_service_sid():
    service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")

    if not service_sid:
        raise RuntimeError("Twilio Verify Service SID is missing.")

    return service_sid


def send_phone_otp(phone_number: str):
    client = get_twilio_client()
    service_sid = get_verify_service_sid()

    verification = client.verify.v2.services(
        service_sid
    ).verifications.create(
        to=phone_number,
        channel="sms"
    )

    return verification.status


def verify_phone_otp(phone_number: str, otp: str):
    client = get_twilio_client()
    service_sid = get_verify_service_sid()

    verification_check = client.verify.v2.services(
        service_sid
    ).verification_checks.create(
        to=phone_number,
        code=otp
    )

    return verification_check.status == "approved"