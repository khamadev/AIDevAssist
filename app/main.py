from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine
from app.routes import auth, itinerary, trips

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Travel Planner")

app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(itinerary.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
