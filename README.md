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