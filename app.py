import httpx
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

AUTH_TOKEN = os.getenv('AUTH_TOKEN')

class DiscordPayload(BaseModel):
    webhook_url: str  # Куда шлем в дискорд
    content: Optional[str] = None
    embeds: Optional[list] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None

@app.post("/relay")
async def relay_to_discord(payload: DiscordPayload, x_token: str = Header(None)):
    if x_token != AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Token")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                payload.webhook_url,
                json=payload.dict(exclude={'webhook_url'}, exclude_none=True)
            )
            return {"status": "sent", "discord_code": response.status_code, "body": response.text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)