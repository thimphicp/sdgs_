# Cloudflare Worker Proxy

이 Worker는 프론트와 Python FastAPI 서버 사이의 중간 서버입니다.

```text
Frontend
  -> Cloudflare Worker /analyze, /ask
  -> Python FastAPI /analyze, /ask
```

## 로컬 개발

Python 서버를 먼저 켭니다.

```bat
C:\Users\thimp\PycharmProjects\PythonProject\run_server.bat
```

그 다음 Worker 폴더에서 실행합니다.

```bat
npx wrangler dev
```

## 배포할 때

Cloudflare Worker는 내 컴퓨터의 `127.0.0.1`에 접근할 수 없습니다.
그래서 Python 서버를 외부에서 접근 가능한 주소로 열어야 합니다.

가능한 방법:

- Cloudflare Tunnel
- Render, Railway, Fly.io 같은 Python 서버 배포 서비스
- 개인 서버/VPS

배포 후에는 `AI_SERVER_URL`을 그 공개 주소로 바꿉니다.

```toml
AI_SERVER_URL = "https://your-python-api.example.com"
```

그리고 프론트의 `API_BASE_URL`을 Worker 주소로 바꿉니다.

```js
const API_BASE_URL = "https://sdgs-food-lens-api.your-name.workers.dev";
```
