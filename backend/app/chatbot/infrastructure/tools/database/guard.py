"""SQL Safety Guard ensuring strict read-only execution and preventing data leakage."""

import re

SENSITIVE_COLUMNS: set[str] = {
    "hashed_password",
    "password",
    "token",
    "refresh_token",
    "api_key",
    "secret",
    "zalo_bind_code",
    "cookie",
}

FORBIDDEN_SQL_KEYWORDS: set[str] = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "replace",
    "grant",
    "revoke",
    "execute",
    "exec",
    "call",
    "commit",
    "rollback",
}


class SqlSecurityError(Exception):
    """Raised when an unsafe SQL statement is detected."""


class SqlSafetyGuard:
    """Enforces read-only SELECT queries, limits row counts, and masks sensitive columns."""

    @staticmethod
    def _check_forbidden_tokens(cleaned: str) -> None:
        """Verifies no mutation keywords or sensitive columns exist in the query."""
        for kw in FORBIDDEN_SQL_KEYWORDS:
            if re.search(rf"\b{kw}\b", cleaned, re.IGNORECASE):
                raise SqlSecurityError(f"Phát hiện từ khóa nguy hiểm bị cấm: '{kw.upper()}'.")

        for col in SENSITIVE_COLUMNS:
            if re.search(rf"\b{col}\b", cleaned, re.IGNORECASE):
                raise SqlSecurityError(f"Truy vấn chứa cột bảo mật bị cấm truy cập: '{col}'.")

    @classmethod
    def validate_and_format_query(cls, query: str, default_limit: int = 50, max_limit: int = 100) -> str:
        """Validates that query is strictly SELECT/WITH and enforces safe LIMIT."""
        cleaned = re.sub(r";+\s*$", "", query.strip())
        if not cleaned:
            raise SqlSecurityError("Câu lệnh SQL không được để trống.")
        if ";" in cleaned:
            raise SqlSecurityError("Chỉ được phép thực thi một câu lệnh SQL duy nhất.")

        first_word_match = re.match(r"^\s*([a-zA-Z]+)", cleaned)
        if not first_word_match or first_word_match.group(1).lower() not in {"select", "with"}:
            raise SqlSecurityError("Chỉ cho phép các câu lệnh truy vấn dữ liệu (SELECT hoặc WITH).")

        cls._check_forbidden_tokens(cleaned)

        # Check / enforce LIMIT
        limit_match = re.search(r"\blimit\s+(\d+)\b", cleaned, re.IGNORECASE)
        if limit_match:
            if int(limit_match.group(1)) > max_limit:
                cleaned = re.sub(r"\blimit\s+\d+\b", f"LIMIT {max_limit}", cleaned, flags=re.IGNORECASE)
        else:
            cleaned = f"{cleaned} LIMIT {default_limit}"

        return cleaned
