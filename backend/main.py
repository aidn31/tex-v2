from fastapi import FastAPI

app = FastAPI(title="TEX API")


@app.get("/health")
async def health():
    return {"status": "ok"}
