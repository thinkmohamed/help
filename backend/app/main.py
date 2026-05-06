"""Main FastAPI application for the Geospatial Analysis System."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .config import STATIC_DIR, FRONTEND_DIR, OUTPUTS_DIR

app = FastAPI(
    title="نظام التحليل الجيومكاني",
    description="Geospatial Analysis System for Archaeological & Geological Exploration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

app.include_router(router)


@app.get("/")
async def root():
    """Redirect to frontend."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/frontend/index.html")


@app.get("/health")
async def health():
    return {"status": "healthy", "app": "geospatial-analysis-system"}
