import re
from pathlib import Path

app_path = Path("backend/app.py")
content = app_path.read_text(encoding="utf-8")

target_sms = """def send_sms_otp(phone, otp):
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_FROM_NUMBER")

    if not account_sid or not auth_token or not from_number:
        raise RuntimeError(
            "SMS is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER."
        )"""

replacement_sms = """def send_sms_otp(phone, otp):
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_FROM_NUMBER")

    if not account_sid or not auth_token or not from_number:
        print(f"DEVELOPMENT MODE: SMS to {phone} - OTP is {otp}")
        return False"""

content = content.replace(target_sms, replacement_sms)

target_route = """    try:
        send_sms_otp(normalized_phone, otp)
    except RuntimeError as exc:
        flash(str(exc))
        return redirect("/otp_login")

    session["otp"] = otp
    session["otp_expires_at"] = (datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()
    session["phone"] = normalized_phone

    flash("OTP sent to your mobile number.")"""

replacement_route = """    try:
        sent_real = send_sms_otp(normalized_phone, otp)
    except RuntimeError as exc:
        flash(str(exc))
        return redirect("/otp_login")

    session["otp"] = otp
    session["otp_expires_at"] = (datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()
    session["phone"] = normalized_phone

    if sent_real is False:
        flash(f"DEV MODE: Your OTP is {otp}")
    else:
        flash("OTP sent to your mobile number.")"""

content = content.replace(target_route, replacement_route)

app_path.write_text(content, encoding="utf-8")
print("Done patching OTP")
