"""Проверка X-Api-Key."""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from gateway.config import Settings, get_settings


def parse_api_keys(raw: str) -> frozenset[str]:
    return frozenset(k.strip() for k in raw.split(",") if k.strip())


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Пропускает /health и /docs без ключа; остальные пути — X-Api-Key."""

    def __init__(
        self,
        app: Any,
        settings: Settings | None = None,
    ) -> None:
        super().__init__(app)
        self._settings = settings

    def _get_settings(self) -> Settings:
        return self._settings or get_settings()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[..., Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        if path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)
        if path.startswith("/api/"):
            settings = self._get_settings()
            keys = parse_api_keys(settings.api_keys)
            if not keys:
                return JSONResponse(
                    {"detail": "API keys not configured (GATEWAY_API_KEYS)"},
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            key = request.headers.get("X-Api-Key", "")
            if key not in keys:
                return JSONResponse(
                    {"detail": "Invalid or missing X-Api-Key"},
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )
        return await call_next(request)
