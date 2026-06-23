from sqlalchemy import create_engine, inspect
from app.core.config import settings

def test_db(env):
    settings.ENVIRONMENT = env
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    inspector = inspect(engine)
    print(f"[{env}] Tables:", inspector.get_table_names())

test_db("local")
test_db("production")
