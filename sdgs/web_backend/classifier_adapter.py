import json
import os
import subprocess
from pathlib import Path
from typing import Any

import requests


CLASSIFIER_MODE = os.getenv("CLASSIFIER_MODE", "mock").strip().lower()
CLASSIFIER_MOCK_LABEL = os.getenv("CLASSIFIER_MOCK_LABEL", "bibimbap").strip()
CLASSIFIER_HTTP_URL = os.getenv("CLASSIFIER_HTTP_URL", "").strip()
CLASSIFIER_COMMAND = os.getenv("CLASSIFIER_COMMAND", "").strip()


def classify_image(image_path: Path) -> dict[str, Any]:
    if CLASSIFIER_MODE == "http":
        return classify_with_http(image_path)
    if CLASSIFIER_MODE == "command":
        return classify_with_command(image_path)
    return {
        "food_name": CLASSIFIER_MOCK_LABEL,
        "score": 0.0,
        "source": "mock",
        "raw": "mock classifier result",
    }


def classify_with_http(image_path: Path) -> dict[str, Any]:
    if not CLASSIFIER_HTTP_URL:
        raise RuntimeError("CLASSIFIER_HTTP_URL is required when CLASSIFIER_MODE=http")
    with image_path.open("rb") as image_file:
        files = {"image": (image_path.name, image_file, "application/octet-stream")}
        response = requests.post(CLASSIFIER_HTTP_URL, files=files, timeout=60)
    response.raise_for_status()
    payload = response.json()
    return {
        "food_name": str(payload.get("food_name") or payload.get("label") or "").strip(),
        "score": payload.get("score"),
        "source": "http",
        "raw": json.dumps(payload, ensure_ascii=False),
    }


def classify_with_command(image_path: Path) -> dict[str, Any]:
    if not CLASSIFIER_COMMAND:
        raise RuntimeError("CLASSIFIER_COMMAND is required when CLASSIFIER_MODE=command")
    completed = subprocess.run(
        f'{CLASSIFIER_COMMAND} "{image_path}"',
        shell=True,
        check=True,
        capture_output=True,
        text=True,
    )
    output = completed.stdout.strip()
    try:
        payload = json.loads(output)
        return {
            "food_name": str(payload.get("food_name") or payload.get("label") or "").strip(),
            "score": payload.get("score"),
            "source": "command",
            "raw": output,
        }
    except json.JSONDecodeError:
        return {
            "food_name": output,
            "score": None,
            "source": "command",
            "raw": output,
        }
