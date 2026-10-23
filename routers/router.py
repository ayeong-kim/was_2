import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, FastAPI
from routers import login_router, desk_router, vet_router
from config import DB_POOL_SIZE

router = APIRouter()
router.include_router(login_router.router)
router.include_router(desk_router.router)
router.include_router(vet_router.router)

app = FastAPI()
app.include_router(router)


@app.on_event("startup")
async def set_db_threads():
    # main 프로세스 DB 스레드 수 = 연결 수 (uvicorn이 이벤트 루프를 새로 만들어서 여기서 설정)
    asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(DB_POOL_SIZE))


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}

