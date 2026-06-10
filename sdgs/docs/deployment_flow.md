# Deployment Flow

## 전체 구조

```text
사용자 브라우저
-> 공개 웹 백엔드
-> 이미지분류기
-> 내 노트북 local_llm_api
-> GrooveLLM 또는 Ollama
-> 공개 웹 백엔드
-> 사용자 브라우저
```

## 권장 배포

- GitHub: `sdgs/` 코드 저장
- 공개 웹 백엔드: Render 또는 Railway
- 로컬 LLM: 내 노트북
- 외부 연결: Cloudflare Tunnel 또는 ngrok

## 실행 순서

1. 노트북에서 GrooveLLM 또는 Ollama 실행
2. `sdgs/local_llm_api` 실행
3. 로컬 API를 터널링해서 외부 접근 주소 확보
4. 공개 백엔드 환경변수에 `LOCAL_LLM_API_URL` 설정
5. 공개 백엔드 실행
6. 프론트엔드에서 `/chat-with-image` 호출

## 무료 GitHub만으로 안 되는 것

- Python 서버 상시 실행
- 이미지 업로드 처리
- 노트북 LLM 직접 호스팅

즉, GitHub는 코드 저장용이고 실행은 별도 런타임이 필요합니다.
