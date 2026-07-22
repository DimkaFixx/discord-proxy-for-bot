import httpx
from fastapi import FastAPI, Request, Response, HTTPException
import os
import logging
import time
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

# Получаем токен и проверяем, что он вообще задан
AUTH_TOKEN = os.getenv('AUTH_TOKEN')
if not AUTH_TOKEN:
    logger.warning("AUTH_TOKEN is not set! Proxy will block all requests.")
else:
    logger.info("AUTH_TOKEN loaded successfully")

DISCORD_BASE_URL = "https://discord.com/api"

@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Discord relay application started successfully")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.exception(
            "Request failed: method=%s path=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise

    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "Request completed: method=%s path=%s status=%s duration_ms=%.1f",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_discord(path: str, request: Request):
    # 1. Проверка токена (Защита от ботнета)
    incoming_token = request.headers.get("X-Relay-Token")
    
    if not incoming_token or incoming_token != AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info("Forwarding request to Discord: %s", path)

    url = f"{DISCORD_BASE_URL}/{path}"
    body = await request.body()
    
    # Копируем заголовки, фильтруя лишнее
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("x-relay-token", None)
    headers.pop("content-length", None) # httpx сам вычислит длину

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                content=body,
                headers=headers,
                params=request.query_params,
                timeout=20.0 # Дискорд иногда тормозит
            )
            
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers)
            )
        except httpx.ConnectError:
            raise HTTPException(status_code=502, detail="Could not connect to Discord API")
        except Exception:
            logger.exception("Proxy error")
            # Не раскрываем клиенту URL, заголовки и внутренний текст исключения.
            raise HTTPException(status_code=502, detail="Upstream request failed")
