import hashlib
import secrets

from routers.datamodels.login_datamodels import UserResponse
from repositorys.user_repository import UserRepository
from repositorys.session_repository import SessionRepository
from config import SESSION_HOURS


class UserService:
    def __init__(self):
        self.user_repository = UserRepository()
        self.session_repository = SessionRepository()

    async def login(self, login_id, password):
        user = await self.user_repository.find_by_login_id(login_id)
        if user is None or user["password"] != hashlib.sha256(password.encode()).hexdigest():
            return None
        return UserResponse(**user)

    async def is_vet(self, uid, branch):
        return await self.user_repository.is_vet(uid, branch)

    async def vets(self, branch):
        return [UserResponse(**user) for user in await self.user_repository.find_vets(branch)]

    # 세션은 DB(Session 테이블)에 저장 → WAS 재시작에도 유지, 같은 DB를 쓰는 WAS끼리 공유
    # SESSION_HOURS가 지난 세션은 만료 (로그인할 때 만료된 세션 정리)
    async def create_session(self, user):
        await self.session_repository.delete_expired(SESSION_HOURS)
        session_id = secrets.token_hex(16)
        await self.session_repository.insert(session_id, user.uid)
        return session_id

    async def session_user(self, session_id):
        user = await self.session_repository.find_user(session_id, SESSION_HOURS)
        return UserResponse(**user) if user else None

    async def delete_session(self, session_id):
        await self.session_repository.delete(session_id)
