from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine
from app.routes import ai, auth, itinerary, trips

Base.metadata.create_all(bind=engine)


class RevalidateStaticFiles(StaticFiles):
    """Serves static files with Cache-Control: no-cache.

    This does NOT disable caching — the browser still caches the file, but
    is required to revalidate with the server (via ETag/Last-Modified,
    already sent automatically) on every load rather than assuming it's
    still fresh. Without this, browsers apply heuristic caching to static
    assets with no Cache-Control header at all, silently serving a stale
    style.css/JS file after a deploy with no visible error — exactly what
    happened during frontend testing.
    """

    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


app = FastAPI(title="Travel Planner")
app.include_router(ai.router)

app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(itinerary.router)

app.mount("/static", RevalidateStaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
