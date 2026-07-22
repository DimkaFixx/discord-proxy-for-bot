import httpx
from fastapi import FastAPI, Request, Response, HTTPException
import os
import logging
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

# Получаем токен и проверяем, что он вообще задан
AUTH_TOKEN = os.getenv('AUTH_TOKEN')
if not AUTH_TOKEN:
    logger.warning("AUTH_TOKEN is not set! Proxy will block all requests.")
else:
    # Никогда не пишем полный секрет в логах контейнера.
    masked_token = f"{AUTH_TOKEN[:4]}…{AUTH_TOKEN[-4:]}" if len(AUTH_TOKEN) > 8 else "***"
    logger.info("AUTH_TOKEN loaded: %s", masked_token)

DISCORD_BASE_URL = "https://discord.com/api"

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_discord(path: str, request: Request):
    # 1. Проверка токена (Защита от ботнета)
    incoming_token = request.headers.get("X-Relay-Token")
    
    if not incoming_token or incoming_token != AUTH_TOKEN:
        # Не логируем каждую атаку, чтобы не забивать диск
        raise HTTPException(status_code=403, detail="Forbidden")

    # 2. Логируем только успешные попытки проксирования
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
        except Exception as e:
            logger.exception("Proxy error")
            raise HTTPException(status_code=502, detail=str(e))
