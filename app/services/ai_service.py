import os
from typing import Any, List, Optional

import httpx

from app.core.config import settings
from app.schemas.ai import AIRequest
from app.schemas.chat import ChatMessage, ChatResponse, SourceReference
from app.schemas.search import SearchResult
from openai import OpenAI


class AIServiceError(Exception):
    pass


class AIService:
    SYSTEM_PROMPT = "You are a senior Python engineer."

    def __init__(self) -> None:
        self.api_key = (
            settings.GROQ_API_KEY
            or settings.XAI_API_KEY
            or settings.OPENAI_API_KEY
            or os.getenv("GROQ_API_KEY")
            or os.getenv("XAI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        if not self.api_key:
            raise AIServiceError("AI API key is not configured")

        # Determine base URL and model based on the key/provider
        if (
            settings.GROQ_API_KEY
            or os.getenv("GROQ_API_KEY")
            or (self.api_key and self.api_key.startswith("gsk_"))
        ):
            self.base_url = (settings.GROQ_BASE_URL or "https://api.groq.com/openai/v1").rstrip("/")
            
            # Use Groq model if configured; fallback to XAI/OpenAI models if they aren't defaults
            model_candidate = settings.GROQ_MODEL or settings.XAI_MODEL or settings.OPENAI_MODEL
            if model_candidate == "grok-4" or model_candidate.startswith("gpt-"):
                self.model = "llama-3.3-70b-versatile"
            else:
                self.model = model_candidate
        elif settings.XAI_API_KEY or os.getenv("XAI_API_KEY"):
            self.base_url = (settings.XAI_BASE_URL or "https://api.x.ai/v1").rstrip("/")
            self.model = settings.XAI_MODEL
        else:
            self.base_url = (settings.OPENAI_API_BASE or "https://api.openai.com/v1").rstrip("/")
            self.model = settings.OPENAI_MODEL

        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.http_client = httpx.Client(base_url=self.base_url)
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, http_client=self.http_client)

    # ── Original method (kept for backward compat) ─────────────────────────
    def generate_response(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as exc:
            raise AIServiceError("AI provider request failed") from exc

        return self._extract_output(response)

    # ── RAG-aware answer generation ────────────────────────────────────────
    def answer_question(
        self,
        question: str,
        context: str,
        history: Optional[List[ChatMessage]] = None,
    ) -> str:
        """Call the LLM with a pre-built context and conversation history."""
        from app.prompts.system_prompt import build_system_prompt

        system_content = build_system_prompt(context)
        messages: list = [{"role": "system", "content": system_content}]

        # Inject last 10 conversation turns for memory
        if history:
            for msg in history[-10:]:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": question})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=2048,
            )
        except Exception as exc:
            raise AIServiceError(f"LLM request failed: {exc}") from exc

        raw = self._extract_output(response)
        return raw.strip() if raw else "The model returned an empty response."

    def stream_answer(
        self,
        question: str,
        context: str,
        history: Optional[List[ChatMessage]] = None,
    ):
        """Stream the LLM response token by token using SSE-compatible generator."""
        from app.prompts.system_prompt import build_system_prompt

        system_content = build_system_prompt(context)
        messages: list = [{"role": "system", "content": system_content}]

        if history:
            for msg in history[-10:]:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": question})

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=2048,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except Exception as exc:
            raise AIServiceError(f"LLM streaming failed: {exc}") from exc

    # ── Internal helpers ───────────────────────────────────────────────────
    def _extract_output(self, response: Any) -> str:
        if response is None:
            raise AIServiceError("No response returned from AI provider")

        choices = getattr(response, "choices", None)
        if choices and len(choices) > 0:
            first_choice = choices[0]
            message = getattr(first_choice, "message", None)
            if message is not None:
                return getattr(message, "content", "") or ""

            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict):
                    return str(message.get("content", ""))

        if isinstance(response, dict):
            if "choices" in response and isinstance(response["choices"], list):
                first_choice = response["choices"][0]
                if isinstance(first_choice, dict):
                    return str(first_choice.get("message", {}).get("content", ""))

        raise AIServiceError("Unable to parse AI response output")
