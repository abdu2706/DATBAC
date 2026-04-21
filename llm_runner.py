from __future__ import annotations

from typing import Optional

import requests

from config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_SEED,
    DEFAULT_TEMPERATURE,
    MODELS,
    OLLAMA_BASE_URL,
)


class OllamaRunner:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url

    def generate(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        seed: int = DEFAULT_SEED,
    ) -> str:
        """Call Ollama /api/chat endpoint."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "seed": seed,
            },
        }

        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()
        except Exception as e:
            return f"[ERROR] {model}: {e}"

    def generate_all_models(
        self,
        system_prompt: str,
        user_prompt: str,
        models: Optional[list[str]] = None,
    ) -> dict[str, str]:
        models = models or MODELS
        results: dict[str, str] = {}
        for model in models:
            print(f"  -> Running {model}...")
            results[model] = self.generate(model, system_prompt, user_prompt)
        return results
