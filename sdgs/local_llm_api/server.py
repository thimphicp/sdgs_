import argparse
import json
import os
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib import error, request


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


@dataclass
class ServerConfig:
    host: str
    port: int
    api_key: str
    provider: str
    ollama_url: str
    ollama_model: str
    ollama_timeout: int
    groovellm_url: str
    groovellm_health_url: str
    groovellm_timeout: int


class UpstreamClient:
    def __init__(self, config: ServerConfig) -> None:
        self.config = config

    def health(self) -> dict[str, Any]:
        provider = self.config.provider
        if provider == "ollama":
            return self._ollama_health()
        return self._groovellm_health()

    def chat(self, prompt: str) -> tuple[str, dict[str, Any]]:
        provider = self.config.provider
        if provider == "ollama":
            return self._ollama_chat(prompt)
        return self._groovellm_chat(prompt)

    def _groovellm_health(self) -> dict[str, Any]:
        started_at = time.perf_counter()
        status = {
            "provider": "groovellm",
            "server_connected": False,
            "url": self.config.groovellm_url,
            "health_url": self.config.groovellm_health_url,
            "error": None,
        }
        try:
            with request.urlopen(self.config.groovellm_health_url, timeout=self.config.groovellm_timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            status["server_connected"] = bool(payload.get("ok", True))
            status["payload"] = payload
        except Exception as exc:
            status["error"] = str(exc)
        status["response_time_seconds"] = round(time.perf_counter() - started_at, 3)
        return status

    def _ollama_health(self) -> dict[str, Any]:
        started_at = time.perf_counter()
        status = {
            "provider": "ollama",
            "server_connected": False,
            "url": self.config.ollama_url,
            "error": None,
        }
        base_url = self.config.ollama_url.replace("/api/chat", "/api/tags")
        try:
            with request.urlopen(base_url, timeout=self.config.ollama_timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            status["server_connected"] = True
            status["payload"] = payload
        except Exception as exc:
            status["error"] = str(exc)
        status["response_time_seconds"] = round(time.perf_counter() - started_at, 3)
        return status

    def _groovellm_chat(self, prompt: str) -> tuple[str, dict[str, Any]]:
        body = {
            "prompt": prompt,
            "tokens": 160,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
        }
        started_at = time.perf_counter()
        raw_text = ""
        error_text = None
        try:
            req = request.Request(
                self.config.groovellm_url,
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=self.config.groovellm_timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            raw_text = str(payload.get("text", "")).strip()
        except (error.URLError, TimeoutError) as exc:
            error_text = str(exc)
        except Exception as exc:
            error_text = str(exc)

        diagnostics = {
            "provider": "groovellm",
            "url": self.config.groovellm_url,
            "prompt_length": len(prompt),
            "response_time_seconds": round(time.perf_counter() - started_at, 3),
            "llm_used": bool(raw_text),
            "error": error_text,
        }
        return raw_text or "현재 GrooveLLM 응답을 받지 못했습니다.", diagnostics

    def _ollama_chat(self, prompt: str) -> tuple[str, dict[str, Any]]:
        body = {
            "model": self.config.ollama_model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
            "options": {
                "temperature": 0.7,
                "num_predict": 160,
                "num_ctx": 2048,
            },
        }
        started_at = time.perf_counter()
        raw_text = ""
        error_text = None
        try:
            req = request.Request(
                self.config.ollama_url,
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=self.config.ollama_timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            raw_text = str(((payload.get("message") or {}).get("content")) or "").strip()
        except (error.URLError, TimeoutError) as exc:
            error_text = str(exc)
        except Exception as exc:
            error_text = str(exc)

        diagnostics = {
            "provider": "ollama",
            "model": self.config.ollama_model,
            "url": self.config.ollama_url,
            "prompt_length": len(prompt),
            "response_time_seconds": round(time.perf_counter() - started_at, 3),
            "llm_used": bool(raw_text),
            "error": error_text,
        }
        return raw_text or "현재 Ollama 응답을 받지 못했습니다.", diagnostics


class LocalLLMService:
    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.upstream = UpstreamClient(config)

    def health(self) -> dict[str, Any]:
        return {
            "ok": True,
            "service": "sdgs-local-llm-api",
            "provider": self.config.provider,
            "upstream": self.upstream.health(),
        }

    def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        question = str(payload.get("question") or "").strip()
        if not question:
            raise ValueError("question is required")

        food_name = str(payload.get("food_name") or payload.get("classifier_label") or "").strip()
        image_path = str(payload.get("image_path") or "").strip()
        classifier_source = str(payload.get("classifier_source") or "").strip()
        extra_context = str(payload.get("extra_context") or "").strip()
        history = payload.get("history") or []

        prompt = self._build_prompt(
            question=question,
            food_name=food_name,
            image_path=image_path,
            classifier_source=classifier_source,
            extra_context=extra_context,
            history=history,
        )
        answer, diagnostics = self.upstream.chat(prompt)
        return {
            "ok": True,
            "provider": self.config.provider,
            "food_name": food_name or None,
            "answer": answer,
            "diagnostics": diagnostics,
        }

    def _build_prompt(
        self,
        *,
        question: str,
        food_name: str,
        image_path: str,
        classifier_source: str,
        extra_context: str,
        history: list[Any],
    ) -> str:
        lines = [
            "너는 음식 이미지 분류 결과를 바탕으로 답변하는 한국어 AI 도우미다.",
            "분류 결과를 우선 참고하되, 확실하지 않으면 추측이라고 밝혀라.",
            "답변은 짧고 정확하게 시작하고, 필요하면 설명을 덧붙여라.",
        ]
        if food_name:
            lines.append(f"분류된 음식명: {food_name}")
        if image_path:
            lines.append(f"이미지 경로: {image_path}")
        if classifier_source:
            lines.append(f"분류기 정보: {classifier_source}")
        if extra_context:
            lines.append(f"추가 문맥: {extra_context}")
        history_lines = []
        for item in history[-6:]:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip()
            content = str(item.get("content") or "").strip()
            if role and content:
                history_lines.append(f"{role}: {content}")
        if history_lines:
            lines.append("이전 대화:")
            lines.extend(history_lines)
        lines.append(f"사용자 질문: {question}")
        lines.append("답변:")
        return "\n".join(lines)


class LocalLLMHandler(BaseHTTPRequestHandler):
    server_version = "SDGSLocalLLM/0.1"

    def do_GET(self) -> None:
        if self.path == "/health":
            json_response(self, HTTPStatus.OK, self.server.service.health())
            return
        json_response(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:
        if not self.server.authorize(self.headers.get("X-API-Key")):
            json_response(self, HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "unauthorized"})
            return
        if self.path != "/chat":
            json_response(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            result = self.server.service.chat(payload)
            json_response(self, HTTPStatus.OK, result)
        except ValueError as exc:
            json_response(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
        except Exception as exc:
            json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        return


class LocalLLMHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], config: ServerConfig):
        super().__init__(server_address, LocalLLMHandler)
        self.config = config
        self.service = LocalLLMService(config)

    def authorize(self, api_key: str | None) -> bool:
        expected = self.config.api_key.strip()
        if not expected:
            return True
        return (api_key or "").strip() == expected


def build_config() -> ServerConfig:
    return ServerConfig(
        host=os.getenv("LOCAL_LLM_API_HOST", "127.0.0.1"),
        port=int(os.getenv("LOCAL_LLM_API_PORT", "8090")),
        api_key=os.getenv("LOCAL_LLM_API_KEY", ""),
        provider=os.getenv("LOCAL_LLM_PROVIDER", "groovellm").strip().lower(),
        ollama_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        ollama_timeout=int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60")),
        groovellm_url=os.getenv("GROOVELLM_URL", "http://127.0.0.1:8088/generate"),
        groovellm_health_url=os.getenv("GROOVELLM_HEALTH_URL", "http://127.0.0.1:8088/health"),
        groovellm_timeout=int(os.getenv("GROOVELLM_TIMEOUT_SECONDS", "45")),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the SDGS local LLM API server.")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--api-key", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.host:
        os.environ["LOCAL_LLM_API_HOST"] = args.host
    if args.port:
        os.environ["LOCAL_LLM_API_PORT"] = str(args.port)
    if args.provider:
        os.environ["LOCAL_LLM_PROVIDER"] = args.provider
    if args.api_key is not None:
        os.environ["LOCAL_LLM_API_KEY"] = args.api_key

    config = build_config()
    server = LocalLLMHTTPServer((config.host, config.port), config)
    print(f"SDGS local LLM API listening on http://{config.host}:{config.port}")
    print(f"Provider: {config.provider}")
    print(f"API key enabled: {'yes' if config.api_key else 'no'}")
    server.serve_forever()


if __name__ == "__main__":
    main()
