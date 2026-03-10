from django.core import signing

AGE_GATE_COOKIE_NAME = "guncad_age_verified"
AGE_GATE_COOKIE_AGE = 60 * 60 * 24 * 30
AGE_GATE_COOKIE_SALT = "guncad-age-verified"


def has_valid_disclaimer(request):
    """
    Takes in a request and checks if their age gate disclaimer cookie is good
    """
    raw = request.COOKIES.get(AGE_GATE_COOKIE_NAME)
    if not raw:
        return False
    try:
        signing.loads(
            raw,
            max_age=AGE_GATE_COOKIE_AGE,
            salt=AGE_GATE_COOKIE_SALT,
        )
        return True
    except signing.BadSignature:
        return False


def generate_age_gate_cookie():
    return signing.dumps({"accepted": True}, salt=AGE_GATE_COOKIE_SALT)
