from app.auth.presentation.router import router as auth_router
from app.rbac.presentation.router_api_key import router as rbac_api_key_router
from app.rbac.presentation.router_rbac import router as rbac_router
from app.user.presentation.router import router as user_router
from fastapi import FastAPI


def setup_router(app: FastAPI):
    app.include_router(user_router)
    app.include_router(auth_router)
    app.include_router(rbac_router)
    app.include_router(rbac_api_key_router)
