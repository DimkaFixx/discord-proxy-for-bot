import httpx
from fastapi import FastAPI, Request, Response, HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

AUTH_TOKEN = os.getenv('AUTH_TOKEN')

DISCORD_BASE_URL = "https://discord.com/api"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_discord(path: str, request: Request):
    # Проверка безопасности
    if request.headers.get("X-Relay-Token") != AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid Relay Token")

    # Формируем URL к реальному Дискорду
    url = f"{DISCORD_BASE_URL}/{path}"
    
    # Копируем тело запроса
    body = await request.body()
    
    # Копируем необходимые заголовки (особенно Authorization)
    headers = dict(request.headers)
    # Удаляем хост, чтобы не путать Дискорд
    headers.pop("host", None)
    headers.pop("x-relay-token", None)

    async with httpx.AsyncClient() as client:
        try:
            # Делаем дублирующий запрос в Дискорд
            resp = await client.request(
                method=request.method,
                url=url,
                content=body,
                headers=headers,
                params=request.query_params,
                timeout=15.0
            )
            
            # Возвращаем ответ от Дискорда обратно твоему боту
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers)
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")