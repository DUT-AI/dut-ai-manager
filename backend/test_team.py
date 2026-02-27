import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.team import Team

try:
    engine = create_engine(
        "sqlite:///app.db"
    )  # Or whatever the DB URL is. What is the URL?
    # Actually wait. Let's just import the config.
    from app.core.config import settings

    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    teams = db.query(Team).limit(1).all()
    if teams:
        print("Team attributes:", dir(teams[0]))
        print("team_name:", getattr(teams[0], "team_name", None))
        print("name:", getattr(teams[0], "name", None))
    else:
        print("No teams found")
except Exception as e:
    print(e)
