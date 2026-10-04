"""
Script to synchronize all PostgreSQL sequences with the maximum IDs in tables.
"""

from loguru import logger
from sqlalchemy import text

from app.shared.infrastructure.database import engine


def sync_all_sequences():
    """Finds all tables with integer primary keys/sequences and updates their sequence to MAX(id)."""
    query = """
    DO $$
    DECLARE
        seq_record RECORD;
        max_val BIGINT;
    BEGIN
        FOR seq_record IN
            SELECT
                s.relname AS seq_name,
                t.relname AS table_name,
                a.attname AS column_name
            FROM pg_class s
            JOIN pg_depend d ON d.objid = s.oid AND d.classid = 'pg_class'::regclass AND d.deptype = 'a'
            JOIN pg_class t ON t.oid = d.refobjid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
            WHERE s.relkind = 'S'
        LOOP
            EXECUTE format('SELECT COALESCE(MAX(%I), 0) FROM %I', seq_record.column_name, seq_record.table_name) INTO max_val;
            IF max_val > 0 THEN
                EXECUTE format('SELECT setval(%L, %s, true)', seq_record.seq_name, max_val);
                RAISE NOTICE 'Updated sequence % for %.% to %', seq_record.seq_name, seq_record.table_name, seq_record.column_name, max_val;
            END IF;
        END LOOP;
    END $$;
    """

    fallback_tables = [
        "accounts",
        "users",
        "roles",
        "permissions",
        "user_roles",
        "role_permissions",
        "homeworks",
        "submissions",
        "meetings",
        "meeting_participants",
        "violations",
        "permission_requests",
        "bonus_points",
        "invoices",
        "outgoing_invoices",
    ]

    with engine.begin() as conn:
        try:
            conn.execute(text(query))
            logger.info("Successfully synced all PostgreSQL sequences via pg_depend")
        except Exception as e:
            logger.warning(f"pg_depend query failed ({e}), trying per-table fallback...")

        for table in fallback_tables:
            try:
                sql = f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {table}), 1),
                    true
                );
                """
                res = conn.execute(text(sql)).scalar()
                logger.info(f"Synced sequence for table '{table}' -> {res}")
            except Exception:
                pass


if __name__ == "__main__":
    sync_all_sequences()
