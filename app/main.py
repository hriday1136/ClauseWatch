import uuid
import logging

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from starlette.middleware.base import BaseHTTPMiddleware

from app.deps import get_current_tenant
from app.models import Tenant
from app.storage import ensure_bucket_exists
from app.routers import webhooks, cron
from app import metrics  # noqa: F401
from app.routers import contracts
from app.logging_config import configure_logging, request_id_var

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bucket_exists()
    yield

configure_logging()

app = FastAPI(title="ClauseWatch", version="0.1.0", lifespan=lifespan)

app.include_router(contracts.router)
app.include_router(webhooks.router)
app.include_router(cron.router)

@app.get("/health")
def health():
    logger.info("health check hit")
    return {"status": "ok"}

@app.get("/me")
def me(tenant: Tenant = Depends(get_current_tenant)):
    return {"tenant_id": str(tenant.id), "name": tenant.name}

class RequestIdMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        token = request_id_var.set(request_id)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.append((b"x-request-id", request_id.encode()))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_var.reset(token)

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.add_middleware(RequestIdMiddleware) 