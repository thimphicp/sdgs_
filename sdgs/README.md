# SDGS

이미지 업로드 기반 음식 챗 서비스를 위한 독립 프로젝트입니다.

이 폴더는 GitHub 공개 저장소에 바로 올릴 수 있게 정리되어 있습니다.

## 구조

```text
sdgs/
├─ local_llm_api/
│  ├─ __init__.py
│  ├─ server.py
│  ├─ requirements.txt
│  └─ start_local_llm_api.ps1
├─ web_backend/
│  ├─ __init__.py
│  ├─ app.py
│  ├─ classifier_adapter.py
│  └─ requirements.txt
├─ docs/
│  ├─ github_ready.md
│  └─ deployment_flow.md
├─ .env.example
├─ .gitignore
└─ README.md
```

## 역할 분리

- `local_llm_api/`
  내 노트북에서 실행하는 LLM API 서버
- `web_backend/`
  이미지 업로드를 받아 분류기 호출 후 로컬 LLM API를 호출하는 공개용 백엔드

## 왜 GitHub에 올려도 되나

- 모델 파일이 없음
- 체크포인트 경로를 강제하지 않음
- 비밀키를 코드에 넣지 않음
- 환경변수로만 민감정보를 받음

## 빠른 시작

### 1. 로컬 LLM API 실행

```powershell
pip install -r sdgs\local_llm_api\requirements.txt
.\sdgs\local_llm_api\start_local_llm_api.ps1 -Provider groovellm -Port 8090 -ApiKey "change-me"
```

### 2. 공개용 백엔드 실행

```powershell
pip install -r sdgs\web_backend\requirements.txt
uvicorn sdgs.web_backend.app:app --reload --port 8000
```

### 3. 테스트 흐름

1. 브라우저에서 이미지 업로드
2. `web_backend`가 이미지분류기 호출
3. 분류된 음식명을 `local_llm_api`로 전송
4. 노트북 LLM 답변을 웹사이트에 반환

## 중요

GitHub 저장소만으로는 백엔드가 상시 실행되지 않습니다.

- 코드 저장: GitHub
- 웹 백엔드 실행: Render / Railway / Fly.io 같은 서비스
- 로컬 LLM 실행: 내 노트북
- 외부 연결: Cloudflare Tunnel 또는 ngrok
