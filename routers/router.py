from fastapi import APIRouter, FastAPI
from routers import login_router, desk_router, vet_router

router = APIRouter()
router.include_router(login_router.router)
router.include_router(desk_router.router)
router.include_router(vet_router.router)

app = FastAPI()
app.include_router(router)


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}

