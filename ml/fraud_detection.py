"""
AI/ML Fraud & Duplicate Detection Module
Uses simple fuzzy string matching to flag likely duplicate beneficiaries.
"""
from difflib import SequenceMatcher
from models import Beneficiary


def similarity(a, b):
    """Returns a similarity ratio between two strings, 0 to 1."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def check_duplicate(name, address, id_number, threshold=0.85):
    """
    Checks a new applicant against existing beneficiaries.
    Returns (is_duplicate: bool, matched_with: Beneficiary or None)
    """
    existing = Beneficiary.query.all()

    for b in existing:
        # Exact ID match = certain duplicate
        if b.id_number.strip() == id_number.strip():
            return True, b

        # Fuzzy match on name + address = likely duplicate
        name_sim = similarity(name, b.name)
        address_sim = similarity(address, b.address)

        if name_sim > threshold and address_sim > threshold:
            return True, b

    return False, None