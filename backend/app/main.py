from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
from app.core.config import DATA_DIR
from app.api.v1 import funds, shares, collect

# 静态文件目录（前端 build 产物）
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import init_db
    from app.core.init_data import init_seed_data
    init_seed_data()
    init_db()
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

# 托管前端静态文件
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback: 非API请求都返回 index.html"""
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/")
    def root():
        return {"message": "ETF雷达 API (前端未构建，请访问 /api/docs)", "docs": "/api/docs"}


if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading

    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000")

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
