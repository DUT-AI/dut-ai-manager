from app.core.database import engine
from sqlalchemy.orm import Session
from app.user.infrastructure.repository import UserRepository
from app.report.infrastructure.repository import MonthlyUserStatsRepository
from app.report.application.participation_use_cases import GetParticipationAnalysisUseCase, GetParticipationLeaderboardUseCase

def test():
    db = Session(engine)
    user_repo = UserRepository(db)
    stats_repo = MonthlyUserStatsRepository(db)
    analysis_uc = GetParticipationAnalysisUseCase(user_repo)
    uc = GetParticipationLeaderboardUseCase(user_repo, stats_repo, analysis_uc)
    res = uc.execute(6, 2026)
    for r in res:
        print(f"Rank: User={r.user}, ID={r.user_id}, Sessions={r.total_sessions}")

if __name__ == "__main__":
    test()
