"""Use case: Create a new user with an auth account."""

from app.auth.domain.interfaces import IAccountCreator
from app.shared.event_bus import IEventBus
from app.user.application.dtos import UserCreateDTO
from app.user.domain.events import UserCreatedEvent
from app.user.domain.exceptions import UserAlreadyExistsException
from app.user.domain.repository import IUserRepository
from app.user.domain.user_entity import User


class CreateUserUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        account_creator: IAccountCreator,
        event_bus: IEventBus,
    ) -> None:
        self.user_repo = user_repo
        self.account_creator = account_creator
        self.event_bus = event_bus

    async def execute(self, user_data: UserCreateDTO) -> User:
        # 1. Check if email already exists
        existing_user = await self.user_repo.get_by(email=user_data.email)
        if existing_user:
            raise UserAlreadyExistsException(user_data.email)

        # 2. Create auth account (returns account_id + plain password)
        account_id, plain_password = await self.account_creator.create_account()

        # 3. Create user entity linked to account
        user = User(**user_data.model_dump(), account_id=account_id)
        new_user = await self.user_repo.create(user)

        # 4. Publish domain event (email will be sent by handler)
        await self.event_bus.publish(
            UserCreatedEvent(
                user_id=new_user.id,  # type: ignore[arg-type]
                email=str(new_user.email),
                name=new_user.name,
                plain_password=plain_password,
            )
        )

        return new_user
