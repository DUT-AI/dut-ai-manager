from app.auth.application.dtos import RefreshTokenRequestDTO, TokenResponseDTO
from app.auth.domain.exceptions import InvalidTokenException, UserInactiveException
from app.auth.domain.interfaces import IAuthUserRepository, ITokenService


class RefreshTokenUseCase:
    def __init__(
        self,
        auth_repo: IAuthUserRepository,
        token_service: ITokenService,
    ):
        self.auth_repo = auth_repo
        self.token_service = token_service

    async def execute(self, payload: RefreshTokenRequestDTO) -> TokenResponseDTO:
        token_data = self.token_service.decode_token(payload.refresh_token)
        user_id = token_data.get("sub")
        if not user_id:
            raise InvalidTokenException()

        user = await self.auth_repo.get_by_id(int(user_id))
        if not user:
            raise InvalidTokenException()

        if not user.is_active():
            raise UserInactiveException()

        access_token = self.token_service.create_access_token(token_data)
        new_refresh_token = self.token_service.create_refresh_token(token_data)

        return TokenResponseDTO(
            access_token=access_token, refresh_token=new_refresh_token
        )
