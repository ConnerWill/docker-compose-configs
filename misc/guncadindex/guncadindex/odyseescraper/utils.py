from didyoumean.utils import add_tokens


def add_release_to_search_tokens(release):
    add_tokens(release.name, release.popularity)
    # add_tokens(release.description, 0.9)
