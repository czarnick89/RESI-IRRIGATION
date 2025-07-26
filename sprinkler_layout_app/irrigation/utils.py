from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

signer = TimestampSigner()

def generate_verification_token(user):
    return signer.sign(user.pk)

def verify_email_token(token, max_age=60*60*24):  # valid for 24 hours
    try:
        user_pk = signer.unsign(token, max_age=max_age)
        return int(user_pk)
    except (BadSignature, SignatureExpired):
        return None
