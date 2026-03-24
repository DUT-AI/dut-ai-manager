from app.auth.infrastructure.di import AuthProvider
from app.infrastructure.provider.database import DatabaseProvider
from app.infrastructure.provider.shared import SharedProvider
from app.rbac.infrastructure.di import RbacProvider
from app.user.infrastructure.di import UserProvider
from dishka import make_async_container


def setup_provider():
    return make_async_container(
        SharedProvider(),
        UserProvider(),
        DatabaseProvider(),
        AuthProvider(),
        RbacProvider(),
    )
