"""
User Domain Value Objects — encapsulate user-related domain rules.
"""

from pydantic import BaseModel, Field


class PhoneNumber:
    """Value object for Vietnamese phone number normalization and validation."""

    @staticmethod
    def normalize(phone_raw: object) -> str | None:
        if phone_raw is None:
            return None

        phone_str = str(phone_raw).strip()
        if not phone_str or phone_str.lower() in ("nan", "none", "null"):
            return None

        # Strip floating point artifact from Excel (e.g. 901234567.0)
        if phone_str.endswith(".0"):
            phone_str = phone_str[:-2]

        # Strip common formatting characters
        for char in (" ", "-", ".", "(", ")", "+"):
            phone_str = phone_str.replace(char, "")

        if not phone_str:
            return None

        # Convert country code 84 -> 0
        if phone_str.startswith("84") and len(phone_str) > 9:
            phone_str = "0" + phone_str[2:]

        # Prepend 0 if 9-digit valid local number
        if len(phone_str) == 9 and phone_str[0] in "35789":
            phone_str = "0" + phone_str

        return phone_str


class NormalizedEmail:
    """Value object for normalized email addresses."""

    @staticmethod
    def normalize(email_raw: object) -> str:
        if email_raw is None:
            return ""
        return str(email_raw).strip().lower()

    @staticmethod
    def is_valid(email: str) -> bool:
        return bool(email and "@" in email and "." in email and len(email) >= 5)


class UserImportRow(BaseModel):
    """Domain model representing a single row parsed from user import source."""

    row_num: int
    name: str
    email: str
    phone_number: str | None = None
    validation_error: str | None = None
    raw_data: dict[str, object] = Field(default_factory=dict)
