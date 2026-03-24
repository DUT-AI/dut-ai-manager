from app.auth.domain.interfaces import IAccountCreator
from app.shared.event_bus import IEventBus
from app.user.application.use_cases.create_user import CreateUserUseCase
from app.user.application.use_cases.delete_user import DeleteUserUseCase
from app.user.application.use_cases.get_users import (GetUserByIdUseCase,
                                                      GetUsersUseCase)
from app.user.application.use_cases.import_users import ImportUsersUseCase
from app.user.application.use_cases.update_user import (
  UpdateUserAvatarUseCase, UpdateUserSettingsUseCase, UpdateUserUseCase)
from app.user.domain.repository import IUserRepository
from app.user.infrastructure.user_repository import SQLAlchemyUserRepository
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession


class UserProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def user_repository(self, session: AsyncSession) -> IUserRepository:
        return SQLAlchemyUserRepository(session)

    @provide(scope=Scope.REQUEST)
    def create_user_uc(
        self,
        user_repo: IUserRepository,
        account_creator: IAccountCreator,
        event_bus: IEventBus,
    ) -> CreateUserUseCase:
        return CreateUserUseCase(user_repo, account_creator, event_bus)

    get_users_uc = provide(GetUsersUseCase, scope=Scope.REQUEST)
    get_user_by_id_uc = provide(GetUserByIdUseCase, scope=Scope.REQUEST)
    update_user_uc = provide(UpdateUserUseCase, scope=Scope.REQUEST)
    update_user_settings_uc = provide(UpdateUserSettingsUseCase, scope=Scope.REQUEST)
    update_user_avatar_uc = provide(UpdateUserAvatarUseCase, scope=Scope.REQUEST)
    delete_user_uc = provide(DeleteUserUseCase, scope=Scope.REQUEST)
    import_users_uc = provide(ImportUsersUseCase, scope=Scope.REQUEST)
