from fastapi import FastAPI

from app.routers.mailing import router as mailing_router

app = FastAPI(title="VK рассылка")
app.include_router(mailing_router)


@app.get("/")
def root():
    return {"ok": True, "send": "/send"}