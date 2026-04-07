from fastapi import FastAPI

app = FastAPI(title="ETF雷达", version="0.1.0")


@app.get("/")
def root():
    return {"message": "ETF雷达 API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
