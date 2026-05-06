"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api import aoi as aoi_api
from .api import jobs as jobs_api
from .api import results as results_api
from .api import sources as sources_api
from .core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(aoi_api.router)
    app.include_router(sources_api.router)
    app.include_router(jobs_api.router)
    app.include_router(results_api.router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
