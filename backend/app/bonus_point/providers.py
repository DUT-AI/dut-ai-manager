from dishka import Provider, Scope, provide
from sqlmodel import Session
from app.bonus_point.infrastructure.repository import BonusPointRepository

class BonusPointModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_bonus_point_repo(self, session: Session) -> BonusPointRepository:
        return BonusPointRepository(session)
