#!/usr/bin/env python3
"""
client.py - Open-Weight Model Harness Client for IssuePilot.

Communicates with OpenAI-compatible inference servers hosting open-weight models
(e.g., Ollama, vLLM, SGLang, LM Studio) running Qwen 2.5 Coder or Llama 3.1.
Includes resilience with configurable timeouts and intelligent fallback handling.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

def load_dotenv(filepath: str = ".env") -> None:
    if not os.path.exists(filepath):
        parent_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
        if os.path.exists(parent_env):
            filepath = parent_env
        else:
            return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key, val = key.strip(), val.strip()
                if key and key not in os.environ:
                    os.environ[key] = val.strip("\"'")
    except Exception:
        pass

load_dotenv()


class OpenWeightClient:
    """
    OpenAI-compatible client for local or remote open-weight inference backends.
    """

    def __init__(
        self,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 45,
    ):
        self.api_base = (
            api_base
            or os.environ.get("OPEN_WEIGHT_API_BASE")
            or "http://localhost:11434/v1"
        ).rstrip("/")
        self.model = (
            model
            or os.environ.get("OPEN_WEIGHT_MODEL")
            or "qwen2.5-coder:7b"
        )
        self.api_key = api_key or os.environ.get("OPEN_WEIGHT_API_KEY", "EMPTY")
        self.timeout = timeout

    def is_server_available(self) -> bool:
        """Checks if the OpenAI-compatible inference server is responding."""
        models_url = f"{self.api_base}/models"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            req = urllib.request.Request(models_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Sends a chat completion request to the open-weight model endpoint.
        Returns a dict containing 'content', 'model', and 'provider'.
        """
        endpoint = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                response_json = json.loads(resp.read().decode("utf-8"))
                choices = response_json.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return {
                        "content": content,
                        "model": response_json.get("model", self.model),
                        "provider": "open-weight-live",
                        "usage": response_json.get("usage", {}),
                    }
                else:
                    raise ValueError("Empty choices list received from inference endpoint.")

        except urllib.error.URLError as e:
            # Connection refused (e.g. Ollama daemon not running) or timeout
            sys.stderr.write(
                f"[WARN] Open-weight inference endpoint at {self.api_base} unreachable: {e.reason}\n"
            )
            return {
                "content": "",
                "model": self.model,
                "provider": "offline",
                "error": str(e.reason),
            }
        except Exception as e:
            sys.stderr.write(f"[WARN] Error invoking open-weight model: {e}\n")
            return {
                "content": "",
                "model": self.model,
                "provider": "error",
                "error": str(e),
            }


if __name__ == "__main__":
    client = OpenWeightClient()
    print(f"IssuePilot Open-Weight Client initialized.")
    print(f"Target Endpoint: {client.api_base}")
    print(f"Target Model:    {client.model}")
    available = client.is_server_available()
    print(f"Backend Server Health: {'ONLINE' if available else 'OFFLINE (Fallback mode active)'}")
