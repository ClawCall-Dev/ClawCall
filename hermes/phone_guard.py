"""Strict US +1 NANP and emergency-number guard for ClawCall."""

from __future__ import annotations

from dataclasses import dataclass
import re

# Emergency and N11 / special service short codes that must never be dialed.
EMERGENCY_AND_SERVICE_CODES: frozenset[str] = frozenset(
    {
        "000",
        "112",
        "211",
        "311",
        "411",
        "511",
        "611",
        "711",
        "811",
        "911",
        "988",
        "999",
    }
)

# NANP N11 and 988 codes cannot appear as area codes or central office exchanges.
BLOCKED_NANP_PREFIXES: frozenset[str] = frozenset(
    {
        "211",
        "311",
        "411",
        "511",
        "611",
        "711",
        "811",
        "911",
        "988",
    }
)

# Non-US NANP area codes: Canada (NANPA assigned Canadian NPAs).
CANADIAN_AREA_CODES: frozenset[str] = frozenset(
    {
        "204",
        "226",
        "236",
        "249",
        "250",
        "263",
        "289",
        "306",
        "343",
        "354",
        "365",
        "367",
        "368",
        "382",
        "387",
        "403",
        "416",
        "418",
        "428",
        "431",
        "437",
        "438",
        "450",
        "468",
        "474",
        "506",
        "514",
        "519",
        "548",
        "579",
        "581",
        "584",
        "587",
        "604",
        "613",
        "639",
        "647",
        "672",
        "683",
        "705",
        "709",
        "742",
        "753",
        "778",
        "780",
        "782",
        "807",
        "819",
        "825",
        "867",
        "873",
        "879",
        "902",
        "905",
        "942",
    }
)

# Non-US NANP area codes: Caribbean and Atlantic countries sharing +1.
CARIBBEAN_NON_US_AREA_CODES: frozenset[str] = frozenset(
    {
        "242",  # Bahamas
        "246",  # Barbados
        "264",  # Anguilla
        "268",  # Antigua and Barbuda
        "284",  # British Virgin Islands
        "345",  # Cayman Islands
        "441",  # Bermuda
        "473",  # Grenada
        "649",  # Turks and Caicos Islands
        "658",  # Jamaica
        "664",  # Montserrat
        "721",  # Sint Maarten
        "758",  # Saint Lucia
        "767",  # Dominica
        "784",  # Saint Vincent and the Grenadines
        "809",  # Dominican Republic
        "829",  # Dominican Republic
        "849",  # Dominican Republic
        "868",  # Trinidad and Tobago
        "869",  # Saint Kitts and Nevis
        "876",  # Jamaica
    }
)

# Premium-rate NANP area and exchange codes blocked locally.
PREMIUM_RATE_AREA_CODES: frozenset[str] = frozenset({"900", "976"})
PREMIUM_RATE_EXCHANGES: frozenset[str] = frozenset({"976"})

NON_US_NANP_AREA_CODES: frozenset[str] = (
    CANADIAN_AREA_CODES | CARIBBEAN_NON_US_AREA_CODES
)

_SEPARATOR_RE = re.compile(r"[\s().-]+")


class PhoneValidationError(ValueError):
    """Raised when a phone number fails the US +1 or emergency-number guard."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class PhoneValidationResult:
    valid: bool
    normalized: str | None = None
    code: str | None = None
    error: str | None = None


def validate_us_phone_number(
    phone: object,
    *,
    field_name: str = "to",
) -> PhoneValidationResult:
    """Validate that `phone` is a dialable US +1 NANP number and not an emergency/N11 code."""
    if not isinstance(phone, str) or not phone.strip():
        return PhoneValidationResult(
            valid=False,
            code="invalid_phone",
            error=f"{field_name}: Phone number is required in US +1 E.164 format (for example +14155550123).",
        )

    compact = _SEPARATOR_RE.sub("", phone.strip())

    # Check raw short codes and +1-prefixed short codes first so emergency/N11 numbers
    # always get an explicit safety refusal.
    digits_only = compact[1:] if compact.startswith("+") else compact
    if compact in EMERGENCY_AND_SERVICE_CODES or digits_only in EMERGENCY_AND_SERVICE_CODES:
        return PhoneValidationResult(
            valid=False,
            code="emergency_number_blocked",
            error=f"{field_name}: Emergency and N11 service numbers ({digits_only}) cannot be dialed through ClawCall.",
        )

    if compact.startswith("+1") and compact[2:] in EMERGENCY_AND_SERVICE_CODES:
        return PhoneValidationResult(
            valid=False,
            code="emergency_number_blocked",
            error=f"{field_name}: Emergency and N11 service numbers ({compact[2:]}) cannot be dialed through ClawCall.",
        )

    if digits_only.startswith("1") and digits_only[1:] in EMERGENCY_AND_SERVICE_CODES:
        return PhoneValidationResult(
            valid=False,
            code="emergency_number_blocked",
            error=f"{field_name}: Emergency and N11 service numbers ({digits_only[1:]}) cannot be dialed through ClawCall.",
        )

    # Reject non-+1 international prefixes explicitly.
    if compact.startswith("+") and not compact.startswith("+1"):
        return PhoneValidationResult(
            valid=False,
            code="unsupported_destination",
            error=f"{field_name}: ClawCall supports US +1 numbers only. International numbers outside US +1 are not supported.",
        )

    if compact.startswith("011"):
        return PhoneValidationResult(
            valid=False,
            code="unsupported_destination",
            error=f"{field_name}: ClawCall supports US +1 numbers only. International dialing prefixes are not supported.",
        )

    if not compact.startswith("+1"):
        return PhoneValidationResult(
            valid=False,
            code="invalid_phone",
            error=f"{field_name}: Only US +1 numbers in E.164 format are supported (for example +14155550123).",
        )

    national_digits = compact[2:]
    if not national_digits.isdigit() or len(national_digits) != 10:
        return PhoneValidationResult(
            valid=False,
            code="invalid_phone",
            error=f"{field_name}: US +1 phone numbers must contain exactly 10 digits after +1.",
        )

    area_code = national_digits[:3]
    exchange_code = national_digits[3:6]

    if area_code in BLOCKED_NANP_PREFIXES:
        return PhoneValidationResult(
            valid=False,
            code="emergency_number_blocked",
            error=f"{field_name}: Emergency and N11 service area code ({area_code}) cannot be dialed through ClawCall.",
        )

    if area_code[0] in ("0", "1"):
        return PhoneValidationResult(
            valid=False,
            code="invalid_phone",
            error=f"{field_name}: Invalid US +1 area code ({area_code}). Area codes cannot start with 0 or 1.",
        )

    if area_code in PREMIUM_RATE_AREA_CODES:
        return PhoneValidationResult(
            valid=False,
            code="premium_number_blocked",
            error=f"{field_name}: Premium-rate area code ({area_code}) cannot be dialed through ClawCall.",
        )

    if area_code in NON_US_NANP_AREA_CODES:
        return PhoneValidationResult(
            valid=False,
            code="unsupported_destination",
            error=(
                f"{field_name}: Area code {area_code} is a non-US +1 region (Canada or Caribbean). "
                "ClawCall supports US +1 numbers only."
            ),
        )

    if exchange_code in BLOCKED_NANP_PREFIXES:
        return PhoneValidationResult(
            valid=False,
            code="emergency_number_blocked",
            error=f"{field_name}: Emergency and N11 service exchange code ({exchange_code}) cannot be dialed through ClawCall.",
        )

    if exchange_code in PREMIUM_RATE_EXCHANGES:
        return PhoneValidationResult(
            valid=False,
            code="premium_number_blocked",
            error=f"{field_name}: Premium-rate exchange code ({exchange_code}) cannot be dialed through ClawCall.",
        )

    if exchange_code[0] in ("0", "1"):
        return PhoneValidationResult(
            valid=False,
            code="invalid_phone",
            error=f"{field_name}: Invalid US +1 exchange code ({exchange_code}). Exchange codes cannot start with 0 or 1.",
        )

    return PhoneValidationResult(valid=True, normalized=f"+1{national_digits}")


def assert_us_phone_number(phone: object, *, field_name: str = "to") -> str:
    """Validate and return normalized +1XXXXXXXXXX string, or raise PhoneValidationError."""
    result = validate_us_phone_number(phone, field_name=field_name)
    if not result.valid or result.normalized is None:
        raise PhoneValidationError(
            result.code or "invalid_phone",
            result.error or f"{field_name}: Invalid US +1 phone number.",
        )
    return result.normalized
