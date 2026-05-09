from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import cases, conversations, drafts, fact_versions, materials, tasks


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(conversations.router)
app.include_router(drafts.router)
app.include_router(fact_versions.router)
app.include_router(materials.router)
app.include_router(tasks.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
