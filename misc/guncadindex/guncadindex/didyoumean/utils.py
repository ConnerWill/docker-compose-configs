import string

from didyoumean.models import SearchToken
from didyoumean.stopwords import stopwords

MAXIMUM_TOKEN_LENGTH = 24
MINIMUM_TOKEN_LENGTH = 3
PUNCTUATION = r'!"#$%&\'()*,.<=>[\\]^`{}'


def add_tokens(string, popularity=1.0):
    """
    Adds SearchToken objects given some string with them in it
    Returns how many new tokens were added
    """
    added = 0
    for token in tokenize(string):
        if not validate_token(token):
            continue
        obj, created = SearchToken.objects.get_or_create(
            token=remove_punctuation(token),
            defaults={"popularity": popularity},
        )
        if not created and obj.popularity < popularity:
            obj.popularity = popularity
            obj.save(update_fields=["popularity"])
        if created:
            added += 1
    return added


def get_correction(string):
    """
    Takes a string and returns the most likely correction based on known SearchTokens
    """
    original = []
    returnval = []
    for token in tokenize(string):
        original += [token]
        if not validate_token(token):
            # Invalid tokens won't get any matches, but should still be part of the returned replacement query
            returnval += [token]
            continue
        closest = SearchToken.objects.closest(token).first()
        if closest:
            closest_token = closest.token
            # Handle quotes, if they exist in the original
            if token.startswith('"'):
                closest_token = f'"{closest_token}'
            if token.endswith('"'):
                closest_token = f'{closest_token}"'
            returnval += [closest_token]
        else:
            returnval += [token]
    return (" ".join(original), " ".join(returnval))


def tokenize(string):
    """
    Takes a string and tokenizes it
    """
    return string.lower().split()


def remove_punctuation(token):
    # https://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string
    return token.translate(str.maketrans("", "", PUNCTUATION))


def validate_token(string):
    """
    Takes a token and returns whether or not it should be considered valid
    """
    token = remove_punctuation(string)
    if (
        not token
        or token.isnumeric()
        or token.startswith("-")
        or len(token) < MINIMUM_TOKEN_LENGTH
        or len(token) > MAXIMUM_TOKEN_LENGTH
        # If the token is just a bunch of one character
        # like "aaaaaaa"
        or token.count(token[0]) == len(token)
        or token in stopwords
    ):
        return False
    return True
