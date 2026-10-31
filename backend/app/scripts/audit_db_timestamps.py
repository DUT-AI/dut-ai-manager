"""Audit tool to check all timestamp/datetime columns in PostgreSQL database."""

from sqlalchemy import text

from app.shared.infrastructure.database import get_session


def audit_timestamps() -> None:
    db = next(get_session())
    try:
        query = text("""
            SELECT
                table_name,
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND (
                  data_type LIKE '%timestamp%'
                  OR data_type = 'date'
                  OR data_type LIKE '%time%'
              )
            ORDER BY table_name, column_name;
        """)
        rows = db.execute(query).fetchall()

        timestamptz_cols: list[str] = []
        naive_cols: list[str] = []
        date_cols: list[str] = []

        for table, col, dtype, nullable in rows:
            info = f"{table}.{col} (nullable={nullable})"
            if dtype == "timestamp with time zone":
                timestamptz_cols.append(info)
            elif dtype == "timestamp without time zone":
                naive_cols.append(info)
            elif dtype == "date":
                date_cols.append(info)

        print("\n" + "=" * 65)
        print("📊 BÁO CÁO TOÀN DIỆN CÁC CỘT THỜI GIAN TRONG DATABASE (POSTGRESQL)")
        print("=" * 65)

        print(
            f"\n✅ 1. CỘT ĐẠT CHUẨN TIMESTAMPTZ (with time zone): "
            f"{len(timestamptz_cols)} cột"
        )
        for c in timestamptz_cols:
            print(f"   ✓ {c}")

        print(f"\n⚠️  2. CỘT CÒN LÀ NAIVE (without time zone): {len(naive_cols)} cột")
        if naive_cols:
            for c in naive_cols:
                print(f"   ✗ {c}")
        else:
            print("   (Không còn cột nào - 100% chuẩn TIMESTAMPTZ!)")

        print(f"\n📅 3. CỘT DATE THUẦN (chỉ lưu ngày YYYY-MM-DD): {len(date_cols)} cột")
        for c in date_cols:
            print(f"   • {c}")

        print("\n" + "=" * 65 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    audit_timestamps()
