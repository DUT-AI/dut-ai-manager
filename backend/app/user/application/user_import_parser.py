"""
User Import Parser Service — application layer parser for file uploads.
"""

from io import BytesIO
from typing import cast

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.user.domain.value_objects import NormalizedEmail, PhoneNumber, UserImportRow


class UserImportParser:
    """Parses Excel/CSV files into domain UserImportRow models."""

    COLUMN_MAPPING = {
        "name": ["name", "họ và tên", "họ tên", "tên", "full_name", "fullname"],
        "email": ["email", "mail", "thư điện tử"],
        "phone_number": [
            "phone_number",
            "phone",
            "sđt",
            "sdt",
            "số điện thoại",
            "phonenumber",
        ],
    }

    REQUIRED_COLUMNS = ["name", "email"]

    async def parse_file(self, file: UploadFile) -> list[UserImportRow]:
        """Reads and parses the uploaded file into domain UserImportRow instances."""
        content = await file.read()
        df = self._read_content(content, file.filename)

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        df = self._map_columns(df)
        self._validate_required_columns(df)

        rows: list[UserImportRow] = []
        for index, raw_row in df.iterrows():
            row_num = cast(int, index) + 2
            parsed_row = self._parse_row(row_num, raw_row)
            rows.append(parsed_row)

        return rows

    def _read_content(self, content: bytes, filename: str | None) -> pd.DataFrame:
        """Reads raw bytes into a pandas DataFrame."""
        try:
            if filename and filename.lower().endswith(".csv"):
                try:
                    return pd.read_csv(
                        BytesIO(content), encoding="utf-8-sig", dtype=str
                    )
                except Exception:
                    return pd.read_csv(BytesIO(content), dtype=str)
            return pd.read_excel(BytesIO(content), dtype=str)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid file format: {str(e)}"
            ) from e

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans and standardizes column names."""
        df.columns = [
            str(col).strip().lower().replace("\ufeff", "") for col in df.columns
        ]

        rename_dict = {}
        for std_col, aliases in self.COLUMN_MAPPING.items():
            for col in df.columns:
                if col in aliases and col != std_col:
                    rename_dict[col] = std_col
                    break

        if rename_dict:
            df = df.rename(columns=rename_dict)

        return df

    def _validate_required_columns(self, df: pd.DataFrame) -> None:
        """Ensures all required columns exist."""
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise HTTPException(
                status_code=400, detail=f"Missing columns: {', '.join(missing)}"
            )

    def _parse_row(self, row_num: int, raw_row: pd.Series) -> UserImportRow:
        """Parses a single row and applies domain validation."""
        raw_name = raw_row.get("name", "")
        raw_email = raw_row.get("email", "")
        raw_phone = raw_row.get("phone_number", None)

        name = str(raw_name).strip() if pd.notna(raw_name) else ""
        email = NormalizedEmail.normalize(raw_email)
        phone = PhoneNumber.normalize(raw_phone)

        validation_error: str | None = None
        if not name:
            validation_error = "Missing user name"
        elif not email:
            validation_error = "Missing email address"
        elif not NormalizedEmail.is_valid(email):
            validation_error = f"Invalid email format ({email})"

        return UserImportRow(
            row_num=row_num,
            name=name,
            email=email,
            phone_number=phone,
            validation_error=validation_error,
            raw_data=raw_row.to_dict(),
        )
