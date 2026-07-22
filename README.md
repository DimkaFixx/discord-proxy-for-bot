For nginx cont add 

```
server {
    listen 80;
    server_name ds.yourdomain.com; # Твой домен

    location / {
        proxy_pass http://127.0.0.1:5050; # Порт из docker-compose
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

using:
rewrite 
```
DISCORD_API_URL = "https://discord.com/api/v10"
```
to your domain

## Запуск в Docker

Создайте файл `.env` по примеру `.env.example` и задайте секретный токен:

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f discord-relay
```

Токен в логах не выводится вообще. В приложении нет публичного health-check маршрута: любой запрос сначала проходит проверку relay-токена, поэтому прокси не генерирует постоянные публичные ответы `200`.
