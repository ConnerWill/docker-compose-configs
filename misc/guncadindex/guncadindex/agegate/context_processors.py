from .utils import has_valid_disclaimer


def age_gate(request):
    result = has_valid_disclaimer(request)
    return {"age_gate": not result}
