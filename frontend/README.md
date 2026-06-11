# SDGs Food Lens Frontend

음식 사진을 업로드하면 Cloudflare Worker의 `/analyze` API로 이미지를 보내고,
음식 분류 결과와 SDGs 설명을 화면에 보여주는 정적 프런트입니다.
분석이 끝난 뒤에는 `추가질문하기` 버튼으로 LLM용 `/ask` API에 질문을 보낼 수 있습니다.

## 실행

브라우저에서 `index.html`을 바로 열어도 됩니다.

```text
frontend/index.html
```

## API 연결

`app.js`의 `API_BASE_URL`을 API 주소로 바꾸면 됩니다.

```js
const API_BASE_URL = "http://127.0.0.1:8090";
```

로컬 개발 중에는 Python FastAPI 서버 주소를 사용합니다.

```js
const API_BASE_URL = "http://127.0.0.1:8090";
```

Cloudflare Worker 배포 후에는 Worker 주소로 바꿉니다.

```js
const API_BASE_URL = "https://sdgs-food-lens-api.your-name.workers.dev";
```

백엔드가 준비되기 전에는 `USE_MOCK_WHEN_API_NOT_READY`를 `true`로 바꾸면 예시 결과가 보입니다.

`/analyze`가 반환하면 좋은 JSON 형식은 아래와 같습니다.

```json
{
  "food": "김치볶음밥",
  "confidence": 0.91,
  "sdgs": ["SDG 3", "SDG 12", "SDG 13"],
  "message": "김치볶음밥은 남은 재료를 활용하면 음식물 쓰레기를 줄이는 SDG 12와 연결됩니다."
}
```

`/ask`는 분석 결과와 사용자의 추가 질문을 JSON으로 받습니다.

```json
{
  "question": "이 음식은 SDG 12와 어떻게 연결되나요?",
  "food": "김치볶음밥",
  "confidence": 0.91,
  "sdgs": ["SDG 3", "SDG 12", "SDG 13"],
  "message": "김치볶음밥은 남은 재료를 활용하면 음식물 쓰레기를 줄이는 SDG 12와 연결됩니다."
}
```

`/ask` 응답은 아래처럼 주면 됩니다.

```json
{
  "answer": "이 음식은 남은 재료를 활용할 수 있어 책임 있는 소비와 생산인 SDG 12와 연결됩니다."
}
```
