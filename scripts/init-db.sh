#!/bin/bash
set -e

echo "🔧 Initializing PostgreSQL databases and users..."

# ================================================
# Create Development Database
# ================================================
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE ${POSTGRES_DEV_DB}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${POSTGRES_DEV_DB}')\gexec
EOSQL

# ================================================
# Create Admin User (Production access only)
# ================================================
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${POSTGRES_USER_ADMIN}') THEN
            CREATE USER ${POSTGRES_USER_ADMIN} WITH PASSWORD '${POSTGRES_PASSWORD_ADMIN}';
        END IF;
    END
    \$\$;
    
    -- Grant full access to production database
    GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER_ADMIN};
    
    -- Grant schema permissions
    GRANT ALL PRIVILEGES ON SCHEMA public TO ${POSTGRES_USER_ADMIN};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO ${POSTGRES_USER_ADMIN};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO ${POSTGRES_USER_ADMIN};
EOSQL

# ================================================
# Create Dev User (Development access only)
# ================================================
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${POSTGRES_DEV_DB}" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${POSTGRES_USER_DEV}') THEN
            CREATE USER ${POSTGRES_USER_DEV} WITH PASSWORD '${POSTGRES_PASSWORD_DEV}';
        END IF;
    END
    \$\$;
    
    -- Grant full access to dev database
    GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DEV_DB} TO ${POSTGRES_USER_DEV};
    
    -- Grant schema permissions
    GRANT ALL PRIVILEGES ON SCHEMA public TO ${POSTGRES_USER_DEV};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO ${POSTGRES_USER_DEV};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO ${POSTGRES_USER_DEV};
EOSQL

# ================================================
# Revoke cross-database access
# ================================================
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    -- Admin cannot access dev database
    REVOKE ALL PRIVILEGES ON DATABASE ${POSTGRES_DEV_DB} FROM ${POSTGRES_USER_ADMIN};
    
    -- Dev user cannot access production database
    REVOKE ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} FROM ${POSTGRES_USER_DEV};
EOSQL

echo ""
echo "✅ Database initialization complete!"
echo "================================================"
echo "📦 Databases:"
echo "   - Production: ${POSTGRES_DB}"
echo "   - Development: ${POSTGRES_DEV_DB}"
echo ""
echo "👤 Users:"
echo "   - ${POSTGRES_USER_ADMIN} → ${POSTGRES_DB} only"
echo "   - ${POSTGRES_USER_DEV} → ${POSTGRES_DEV_DB} only"
echo "   - ${POSTGRES_USER} → Superuser (all access)"
echo "================================================"
