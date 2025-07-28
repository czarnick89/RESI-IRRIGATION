from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
import math

signer = TimestampSigner()

def generate_verification_token(user):
    return signer.sign(user.pk)

def verify_email_token(token, max_age=60*60*24):  # valid for 24 hours
    try:
        user_pk = signer.unsign(token, max_age=max_age)
        return int(user_pk)
    except (BadSignature, SignatureExpired):
        return None

def sanitize_layout_data(data):
    def sanitize(obj):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return 0.0  # or another fallback default
        elif isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize(item) for item in obj]
        return obj

    return sanitize(data)