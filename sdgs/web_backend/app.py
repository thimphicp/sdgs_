import json
import os
import tempfile
from pathlib import Path

import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from sdgs.web_backend.classifier_adapter import classify_image


LOCAL_LLM_API_URL = os.getenv("LOCAL_LLM_API_URL", "http://127.0.0.1:8090/chat").strip()
LOCAL_LLM_API_KEY = os.getenv("LOCAL_LLM_API_KEY", "").strip()
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))

app = FastAPI(title="SDGS Food Chat Backend", version="0.1.0")


@app.get("/health")
def health() -> dict[str, object]:
    return {"ok": True, "service": "sdgs-web-backend"}


@app.post("/chat-with-image")
async def chat_with_image(
    image: UploadFile = File(...),
    question: str = Form(...),
) -> dict[str, object]:
    if not question.strip():
        raise HTTPException(status_code=400, detail="question is required")

    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="image is empty")
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"image exceeds {MAX_UPLOAD_MB}MB")

    suffix = Path(image.filename or "upload.bin").suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        classification = classify_image(temp_path)
        llm_response = call_local_llm_api(
            food_name=classification.get("food_name", ""),
            question=question,
            classifier_source=classification.get("source", ""),
            image_path=str(temp_path),
            extra_context=classification.get("raw", ""),
        )
        return {
            "ok": True,
            "classification": classification,
            "llm": llm_response,
        }
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


def call_local_llm_api(
    *,
    food_name: str,
    question: str,
    classifier_source: str,
    image_path: str,
    extra_context: str,
) -> dict[str, object]:
    headers = {"Content-Type": "application/json"}
    if LOCAL_LLM_API_KEY:
        headers["X-API-Key"] = LOCAL_LLM_API_KEY

    payload = {
        "food_name": food_name,
        "question": question,
        "classifier_source": classifier_source,
        "image_path": image_path,
        "extra_context": extra_context,
    }

    try:
        response = requests.post(
            LOCAL_LLM_API_URL,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=120,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"local llm api request failed: {exc}") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"local llm api error: {response.text}")
    return response.json()
