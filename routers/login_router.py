from fastapi import APIRouter, Cookie, HTTPException, Response

from controllers.login_controllers import LoginControllers
from routers.datamodels import login_datamodels
from config import COOKIE_SECURE, SESSION_HOURS

router = APIRouter(prefix="/login", tags=["login"])

controller = LoginControllers()


def login_user(role):
    # 세션 확인(DB sessions 테이블) + 권한(desk / vet) 확인
    async def check(session_id: str | None = Cookie(None)):
        user = await controller.session_user(session_id) if session_id else None
        if user is None or user.role != role:
            raise HTTPException(status_code=401)
        return user
    return check


@router.post("", response_model=login_datamodels.UserResponse)
async def login(body: login_datamodels.LoginRequest, response: Response):
    result = await controller.login(body)
    if result is None:
        raise HTTPException(status_code=401)
    user, session_id = result
    response.set_cookie("session_id", session_id, httponly=True, secure=COOKIE_SECURE, max_age=SESSION_HOURS * 3600)
    return user


@router.delete("")
async def logout(response: Response, session_id: str | None = Cookie(None)):
    if session_id:
        await controller.logout(session_id)
    response.delete_cookie("session_id")
