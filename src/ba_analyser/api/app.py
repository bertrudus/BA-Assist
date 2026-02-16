"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import Response

from ba_analyser.api.routers import analyse, compare, config, export, iterate, stories, upload

# Locate the React build directory
DIST_DIR = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    app = FastAPI(
        title="BA Analyser",
        description="Business Analysis artifact analysis tool",
        version="0.1.0",
    )

    # CORS for local dev (Vite on :5173)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(analyse.router)
    app.include_router(iterate.router)
    app.include_router(stories.router)
    app.include_router(export.router)
    app.include_router(compare.router)
    app.include_router(config.router)
    app.include_router(upload.router)

    # Serve React build in production
    if DIST_DIR.is_dir():
        # Mount /assets for hashed static files (JS, CSS)
        assets_dir = DIST_DIR / "assets"
        if assets_dir.is_dir():
            app.mount(
                "/assets",
                StaticFiles(directory=str(assets_dir)),
                name="static-assets",
            )

        # SPA fallback: serve index.html for non-API GET requests that 404
        index_html = DIST_DIR / "index.html"

        @app.middleware("http")
        async def spa_fallback(request: Request, call_next) -> Response:
            response = await call_next(request)
            # If the response is 404 and it's a non-API GET, serve index.html
            if (
                response.status_code == 404
                and request.method == "GET"
                and not request.url.path.startswith("/api/")
                and not request.url.path.startswith("/docs")
                and not request.url.path.startswith("/openapi")
                and index_html.is_file()
            ):
                return FileResponse(index_html)
            return response

    return app


app = create_app()
