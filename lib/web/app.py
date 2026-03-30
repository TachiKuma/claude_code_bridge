"""CCB Web Controller - FastAPI Application."""

import secrets
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from i18n_runtime import get_translator
from web.routes import daemons, providers, mail, ws

# Application info
APP_NAME = "CCB Web Controller"
APP_VERSION = "1.0.0"

# Paths
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"


def _build_template_context(request: Request, title_key: str, active_page: str) -> dict:
    """Build a template context with a fresh translator."""
    translate, lang = get_translator("ccb")
    return {
        "request": request,
        "title": translate(title_key),
        "active_page": active_page,
        "lang": lang,
        "t": translate,
    }


def create_app(
    local_only: bool = True,
    auth_token: Optional[str] = None,
) -> FastAPI:
    """Create the FastAPI application."""

    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        docs_url="/api/docs" if not local_only else None,
        redoc_url=None,
    )

    # Store config in app state
    app.state.local_only = local_only
    app.state.auth_token = auth_token

    # Mount static files
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # Setup templates
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    app.state.templates = templates

    # Include routers
    app.include_router(daemons.router, prefix="/api/daemons", tags=["daemons"])
    app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
    app.include_router(mail.router, prefix="/api/mail", tags=["mail"])
    app.include_router(ws.router, prefix="/ws", tags=["websocket"])

    # Root route - Dashboard
    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        return templates.TemplateResponse(
            "dashboard.html",
            _build_template_context(request, "ccb.web.app.dashboard_title", "dashboard"),
        )

    # Mail configuration page
    @app.get("/mail", response_class=HTMLResponse)
    async def mail_page(request: Request):
        return templates.TemplateResponse(
            "mail.html",
            _build_template_context(request, "ccb.web.app.mail_title", "mail"),
        )

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": APP_VERSION}

    return app


def generate_token() -> str:
    """Generate a secure access token."""
    return secrets.token_urlsafe(32)
