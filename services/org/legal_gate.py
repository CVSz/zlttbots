ALLOWED_JURISDICTIONS = {"SG", "US", "EU", "TH"}



def check(jurisdiction: str) -> bool:
    return jurisdiction in ALLOWED_JURISDICTIONS
