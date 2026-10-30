# Build and run

```
docker build -t natasha-server .
docker run -d -p 127.0.0.1:10101:8080 --restart unless-stopped natasha-server
```

# Dev server

```
docker run --rm -it -p 8080:8080 -v $(pwd)/src/natasha_json_server.py:/app/natasha_json_server.py natasha-server
```

# Test requests

```
POST http://localhost:8080/natasha
Content-Type: application/json

{
  "data": "Простите, еще несколько цитат из приговора. «…Отрицал существование Иисуса и пророка Мухаммеда», «наделял Иисуса Христа качествами ожившего мертвеца — зомби» [и] «качествами покемонов — представителей бестиария японской мифологии, тем самым совершил преступление, предусмотренное статьей 148 УК РФ"
}
```

```
POST http://localhost:8080/natasha
Content-Type: application/json

{
  "data": "Сергей Собянин поручил разработать проект стимулирования к бесплатному донорству - Вечерняя Москва"
}
```

Pass `"tokens": true` to also get lemmas, POS tags, morphology and the syntax tree for every token.

Swagger UI: http://localhost:8080/docs

# Response

```
{
  "original_data": {"data": "...", "tokens": false},
  "names": [
    {"first": "Сергей", "last": "Кириенко", "middle": "Владиленович"},
    {"first": "Андрей", "last": "Шевченко", "middle": null}
  ],
  "spans": [{"type": "PER", "start": 0, "stop": 14, "text": "...", "normal": "...", "fact": {...}}],
  "addresses": [...],
  "dates": [...],
  "money": [...]
}
```
