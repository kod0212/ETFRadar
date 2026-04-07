from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.core.init_data import init_seed_data
from app.api.v1 import funds, shares, collect

app = FastAPI(title="ETF雷达", version="0.1.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(funds.router, prefix="/api/v1")
app.include_router(shares.router, prefix="/api/v1")
app.include_router(collect.router, prefix="/api/v1")


@app.on_event("startup")
def startup():
    init_db()
    init_seed_data()


@app.get("/")
def root():
    return {"message": "ETF雷达 API", "docs": "/api/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
