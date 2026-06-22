"""Country dial codes and national-number validation for lead phone fields."""

import re

PHONE_RULES = {
    "+971": {
        "label": "United Arab Emirates",
        "min": 9,
        "max": 9,
        "pattern": r"^[2-9]\d{8}$",
        "strip_leading_zero": True,
        "example": "501234567",
    },
    "+966": {
        "label": "Saudi Arabia",
        "min": 9,
        "max": 9,
        "pattern": r"^5\d{8}$",
        "strip_leading_zero": True,
        "example": "512345678",
    },
    "+974": {
        "label": "Qatar",
        "min": 8,
        "max": 8,
        "pattern": r"^[3-7]\d{7}$",
        "strip_leading_zero": False,
        "example": "33123456",
    },
    "+973": {
        "label": "Bahrain",
        "min": 8,
        "max": 8,
        "pattern": r"^[3-9]\d{7}$",
        "strip_leading_zero": False,
        "example": "36123456",
    },
    "+968": {
        "label": "Oman",
        "min": 8,
        "max": 8,
        "pattern": r"^[79]\d{7}$",
        "strip_leading_zero": False,
        "example": "92123456",
    },
    "+965": {
        "label": "Kuwait",
        "min": 8,
        "max": 8,
        "pattern": r"^[569]\d{7}$",
        "strip_leading_zero": False,
        "example": "50123456",
    },
    "+91": {
        "label": "India",
        "min": 10,
        "max": 10,
        "pattern": r"^[6-9]\d{9}$",
        "strip_leading_zero": False,
        "example": "9876543210",
    },
    "+92": {
        "label": "Pakistan",
        "min": 10,
        "max": 10,
        "pattern": r"^3\d{9}$",
        "strip_leading_zero": False,
        "example": "3001234567",
    },
    "+880": {
        "label": "Bangladesh",
        "min": 10,
        "max": 10,
        "pattern": r"^1\d{9}$",
        "strip_leading_zero": False,
        "example": "1712345678",
    },
    "+63": {
        "label": "Philippines",
        "min": 10,
        "max": 10,
        "pattern": r"^9\d{9}$",
        "strip_leading_zero": False,
        "example": "9123456789",
    },
    "+94": {
        "label": "Sri Lanka",
        "min": 9,
        "max": 9,
        "pattern": r"^7\d{8}$",
        "strip_leading_zero": False,
        "example": "771234567",
    },
    "+977": {
        "label": "Nepal",
        "min": 10,
        "max": 10,
        "pattern": r"^9[78]\d{8}$",
        "strip_leading_zero": False,
        "example": "9812345678",
    },
    "+20": {
        "label": "Egypt",
        "min": 10,
        "max": 10,
        "pattern": r"^1[0125]\d{8}$",
        "strip_leading_zero": False,
        "example": "1012345678",
    },
    "+962": {
        "label": "Jordan",
        "min": 9,
        "max": 9,
        "pattern": r"^7[789]\d{7}$",
        "strip_leading_zero": False,
        "example": "791234567",
    },
    "+961": {
        "label": "Lebanon",
        "min": 7,
        "max": 8,
        "pattern": r"^\d{7,8}$",
        "strip_leading_zero": False,
        "example": "71123456",
    },
    "+44": {
        "label": "United Kingdom",
        "min": 10,
        "max": 10,
        "pattern": r"^7\d{9}$",
        "strip_leading_zero": True,
        "example": "7123456789",
    },
    "+1": {
        "label": "United States / Canada",
        "min": 10,
        "max": 10,
        "pattern": r"^[2-9]\d{9}$",
        "strip_leading_zero": False,
        "example": "2025551234",
    },
}

LEAD_PHONE_COUNTRY_CHOICES = [
    (code, f"{rule['label']} ({code})") for code, rule in PHONE_RULES.items()
]


def phone_rules_for_client():
    """Min/max digit rules for staff add-lead form (client-side hints)."""
    return {
        code: {
            "min": rule["min"],
            "max": rule["max"],
            "example": rule["example"],
            "label": rule["label"],
        }
        for code, rule in PHONE_RULES.items()
    }


def _digits_only(value):
    return re.sub(r"\D", "", value or "")


def split_stored_lead_phone(phone):
    """Split stored international phone into country code and national digits."""
    phone = (phone or "").strip()
    if not phone:
        return "+971", ""
    for code in sorted(PHONE_RULES.keys(), key=len, reverse=True):
        if phone.startswith(code):
            return code, phone[len(code) :]
    return "+971", _digits_only(phone)


def normalize_lead_phone(country_code, national_number):
    """
    Validate and normalize a lead phone number.
    Returns (normalized_phone, error_message).
    """
    country_code = (country_code or "+971").strip()
    rule = PHONE_RULES.get(country_code)
    if not rule:
        return None, "Select a valid country code."

    digits = _digits_only(national_number)
    if not digits:
        return None, "Mobile number is required."

    country_digits = _digits_only(country_code)
    if digits.startswith(country_digits):
        digits = digits[len(country_digits) :]

    if rule.get("strip_leading_zero") and digits.startswith("0"):
        digits = digits.lstrip("0")

    if len(digits) < rule["min"] or len(digits) > rule["max"]:
        if rule["min"] == rule["max"]:
            length_hint = f"exactly {rule['min']} digits"
        else:
            length_hint = f"{rule['min']}–{rule['max']} digits"
        return None, (
            f"{rule['label']} mobile must be {length_hint} "
            f"(e.g. {rule['example']}). You entered {len(digits)} digits."
        )

    pattern = rule.get("pattern")
    if pattern and not re.fullmatch(pattern, digits):
        return None, (
            f"Enter a valid {rule['label']} mobile number (e.g. {rule['example']})."
        )

    return f"{country_code}{digits}", None
