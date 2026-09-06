import json
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database import AsyncSessionLocal
from app.models.models import AuditRun

_SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        body_bytes = await request.body()
        request_body = None
        if body_bytes:
            try:
                request_body = json.loads(body_bytes)
            except Exception:
                pass

        start = time.monotonic()
        status_code = 500
        error_text = None
        response_summary = None

        try:
            response = await call_next(request)
            status_code = response.status_code

            # Capture response body for JSON responses
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                chunks = []
                async for chunk in response.body_iterator:
                    chunks.append(chunk)
                body = b"".join(chunks)
                try:
                    response_summary = body.decode("utf-8")[:2000]
                except Exception:
                    pass
                # Reconstruct response so it can still be read by the client
                response = Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )

            return response
        except Exception as exc:
            error_text = str(exc)
            raise
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            try:
                async with AsyncSessionLocal() as session:
                    session.add(
                        AuditRun(
                            endpoint=request.url.path,
                            method=request.method,
                            status_code=status_code,
                            duration_ms=duration_ms,
                            request_body=request_body,
                            response_summary=response_summary,
                            error=error_text,
                        )
                    )
                    await session.commit()
            except Exception:
                pass
