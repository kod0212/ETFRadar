from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import DATA_DIR
from app.api.v1 import funds, shares, collect


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.init_data import init_seed_data
    from app.core.database import init_db

    main_db = DATA_DIR / "etf.db"
    seed_db = DATA_DIR / "seed.db"
    had_db = main_db.exists()

    # 先尝试从seed恢复，再建表
    init_seed_data()
    init_db()

    # 只有既没有旧库也没有seed时才回补
    if not had_db and not seed_db.exists():
        from app.services.collector import backfill_history
        backfill_history()
    yield


app = FastAPI(title="ETF雷达", version="0.1.0", docs_url="/api/docs", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(funds.router, prefix="/api/v1")
app.include_router(shares.router, prefix="/api/v1")
app.include_router(collect.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "ETF雷达 API", "docs": "/api/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
