from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler as default_http_exception_handler
from fastapi.exception_handlers import request_validation_exception_handler as default_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import Base, engine
from app.database import SessionLocal
from app.routes.admin import router as admin_router
from app.routes.api_keys import router as api_keys_router
from app.routes.auth import router as auth_router
from app.routes.batch import router as batch_router
from app.routes.billing import router as billing_router
from app.routes.contact import router as contact_router
from app.routes.database import router as database_router
from app.routes.developers import router as developers_router
from app.routes.documents import router as documents_router
from app.routes.exports import router as exports_router
from app.routes.jobs import router as jobs_router
from app.routes.internal import router as internal_router
from app.routes.projects import router as projects_router
from app.routes.records import router as records_router
from app.routes.review_items import router as review_items_router
from app.routes.search import router as search_router
from app.routes.settings import router as settings_router
from app.routes.usage import router as usage_router
from app.routes.v1 import router as v1_router
from app.routes.webhook_settings import router as webhook_settings_router
from app.routes.webhooks import router as webhooks_router
from app.routes.workspaces import router as workspaces_router
from app.models import ApiRequestLog

# Import models so SQLAlchemy registers metadata before create_all.
from app import models  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


settings = get_settings()
app = FastAPI(
    title="ChemVault Extract API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.enable_api_docs else None,
    redoc_url="/redoc" if settings.enable_api_docs else None,
    openapi_url="/openapi.json" if settings.enable_api_docs else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_request_log_middleware(request: Request, call_next):
    if not request.url.path.startswith("/v1"):
        return await call_next(request)

    started = time.perf_counter()
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        actor = getattr(request.state, "actor", None)
        status_code = response.status_code if response is not None else 500
        if response is not None:
            response.headers["x-request-id"] = request_id
        if actor is not None:
            with SessionLocal() as db:
                db.add(
                    ApiRequestLog(
                        user_id=actor.user_id,
                        api_key_id=actor.api_key_id,
                        workspace_id=actor.workspace_id,
                        method=request.method,
                        path=request.url.path,
                        status_code=status_code,
                        latency_ms=latency_ms,
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                        request_id=request_id,
                    )
                )
                db.commit()


@app.exception_handler(HTTPException)
async def api_http_exception_handler(request: Request, exc: HTTPException):
    if not request.url.path.startswith("/v1"):
        return await default_http_exception_handler(request, exc)
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        payload = {
            "code": detail.get("code", "invalid_request"),
            "message": detail.get("message", "Request failed."),
            "details": detail.get("details", {}),
        }
    else:
        payload = {
            "code": _code_for_status(exc.status_code),
            "message": str(detail),
            "details": {},
        }
    return JSONResponse(status_code=exc.status_code, content={"error": payload})


@app.exception_handler(RequestValidationError)
async def api_validation_exception_handler(request: Request, exc: RequestValidationError):
    if not request.url.path.startswith("/v1"):
        return await default_validation_exception_handler(request, exc)
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed.",
                "details": {"errors": exc.errors()},
            }
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    database = "ok"
    try:
        with SessionLocal() as db:
            db.execute(text("select 1"))
    except Exception:
        database = "error"

    status_value = "ok" if database == "ok" else "degraded"
    return {
        "status": status_value,
        "database": database,
        "storage": "ok",
        "queue": "ok",
    }


app.include_router(documents_router)
app.include_router(jobs_router)
app.include_router(review_items_router)
app.include_router(records_router)
app.include_router(contact_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(settings_router)
app.include_router(api_keys_router)
app.include_router(webhook_settings_router)
app.include_router(developers_router)
app.include_router(usage_router)
app.include_router(exports_router)
app.include_router(database_router)
app.include_router(search_router)
app.include_router(batch_router)
app.include_router(billing_router)
app.include_router(webhooks_router)
app.include_router(workspaces_router)
app.include_router(v1_router)
app.include_router(internal_router)
app.include_router(admin_router, include_in_schema=False)


def _code_for_status(status_code: int) -> str:
    if status_code == 401:
        return "unauthorized"
    if status_code == 403:
        return "forbidden"
    if status_code == 404:
        return "not_found"
    if status_code == 429:
        return "rate_limit_exceeded"
    return "invalid_request"
