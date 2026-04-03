from dishka import Provider, Scope, provide
from sqlmodel import Session
from app.team.infrastructure.repository import TeamRepository
from app.team.application.use_cases import TeamUseCases

class TeamModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_team_repo(self, session: Session) -> TeamRepository:
        return TeamRepository(session)

    @provide
    def get_team_uc(self, repo: TeamRepository) -> TeamUseCases:
        return TeamUseCases(repo)
