import json
import re
import time
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings


class OllamaException(Exception):
    """Base exception for Ollama-related issues."""
    pass


class OllamaConnectionError(OllamaException):
    """Raised when Ollama daemon is unreachable or connection refused."""
    pass


class OllamaModelNotFoundError(OllamaException):
    """Raised when the specified model is not available locally."""
    pass


class OllamaTimeoutError(OllamaException):
    """Raised when local inference or connection exceeds timeout."""
    pass


class OllamaResponseError(OllamaException):
    """Raised when Ollama returns an unexpected HTTP code or unparseable response."""
    pass


class OllamaService:
    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        model: str = settings.OLLAMA_MODEL,
        default_timeout: float = settings.OLLAMA_TIMEOUT_SECONDS,
        default_num_predict: int = settings.OLLAMA_NUM_PREDICT,
        default_temperature: float = settings.OLLAMA_TEMPERATURE,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.default_timeout = default_timeout
        self.default_num_predict = default_num_predict
        self.default_temperature = default_temperature

    async def check_health(self) -> Dict[str, Any]:
        """
        Check connectivity to the local Ollama daemon and verify model availability.
        Uses a short 2.5s timeout for health checks so status requests are instantaneous.
        """
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    model_found = any(
                        self.model == m
                        or m.startswith(f"{self.model}:")
                        or (":" in self.model and m.startswith(self.model.split(":")[0]))
                        for m in models
                    )
                    return {
                        "status": "online",
                        "base_url": self.base_url,
                        "target_model": self.model,
                        "model_ready": model_found,
                        "installed_models": models,
                        "guidance": None if model_found else f"Model '{self.model}' not found. Run 'ollama pull {self.model}'",
                    }
                return {
                    "status": "error",
                    "base_url": self.base_url,
                    "target_model": self.model,
                    "model_ready": False,
                    "installed_models": [],
                    "error": f"Ollama returned HTTP status {response.status_code}",
                }
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            return {
                "status": "offline",
                "base_url": self.base_url,
                "target_model": self.model,
                "model_ready": False,
                "installed_models": [],
                "error": f"Connection refused to {self.base_url}: {str(e)}",
                "guidance": "Ensure Ollama is running locally via 'ollama serve' in PowerShell.",
            }
        except httpx.TimeoutException as e:
            return {
                "status": "offline",
                "base_url": self.base_url,
                "target_model": self.model,
                "model_ready": False,
                "installed_models": [],
                "error": f"Timeout connecting to {self.base_url}: {str(e)}",
                "guidance": "Ollama service may be overwhelmed or starting up.",
            }
        except Exception as e:
            return {
                "status": "error",
                "base_url": self.base_url,
                "target_model": self.model,
                "model_ready": False,
                "installed_models": [],
                "error": str(e),
                "guidance": "Check local Ollama process and permissions.",
            }

    async def verify_model_available(self) -> None:
        """
        Verify that Ollama is online and the required model is ready.
        Raises OllamaConnectionError or OllamaModelNotFoundError if not.
        """
        health = await self.check_health()
        if health["status"] != "online":
            raise OllamaConnectionError(
                f"Ollama daemon is offline at {self.base_url}. Error: {health.get('error')}. "
                f"Guidance: {health.get('guidance', 'Start Ollama locally.')}"
            )
        if not health["model_ready"]:
            raise OllamaModelNotFoundError(
                f"Required model '{self.model}' is not installed in local Ollama. "
                f"Installed: {health.get('installed_models', [])}. Run 'ollama pull {self.model}'."
            )

    async def generate_text(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        num_predict: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute raw generation against /api/generate.
        Returns dictionary with 'response' text and timing metadata.
        """
        await self.verify_model_available()

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.default_temperature,
                "num_predict": num_predict if num_predict is not None else self.default_num_predict,
            },
        }
        if system:
            payload["system"] = system

        call_timeout = timeout if timeout is not None else self.default_timeout

        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=call_timeout) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                elapsed_ms = round((time.time() - t0) * 1000, 2)

                if res.status_code == 200:
                    data = res.json()
                    return {
                        "response": data.get("response", "").strip(),
                        "total_duration_ms": elapsed_ms,
                        "model": self.model,
                        "eval_count": data.get("eval_count"),
                    }
                elif res.status_code == 404:
                    raise OllamaModelNotFoundError(f"Model '{self.model}' not found on server.")
                else:
                    raise OllamaResponseError(
                        f"Ollama returned HTTP status {res.status_code}: {res.text}"
                    )
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise OllamaConnectionError(f"Lost connection to Ollama at {self.base_url}: {str(e)}")
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(
                f"Ollama inference timed out after {call_timeout}s. "
                f"Ensure CPU has available resources for local {self.model} inference."
            )
        except (OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError, OllamaResponseError):
            raise
        except Exception as e:
            raise OllamaResponseError(f"Unexpected error communicating with Ollama: {str(e)}")

    async def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        num_predict: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute generation with Ollama JSON enforcement (format='json').
        Parses and returns valid dictionary, with fallback sanitization for code fences.
        """
        await self.verify_model_available()

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature if temperature is not None else self.default_temperature,
                "num_predict": num_predict if num_predict is not None else self.default_num_predict,
            },
        }
        if system:
            payload["system"] = system

        call_timeout = timeout if timeout is not None else self.default_timeout

        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=call_timeout) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                elapsed_ms = round((time.time() - t0) * 1000, 2)

                if res.status_code == 200:
                    raw_text = res.json().get("response", "").strip()
                    parsed = self._extract_json_dict(raw_text)
                    return {
                        "data": parsed,
                        "raw_response": raw_text,
                        "total_duration_ms": elapsed_ms,
                        "model": self.model,
                    }
                elif res.status_code == 404:
                    raise OllamaModelNotFoundError(f"Model '{self.model}' not found on server.")
                else:
                    raise OllamaResponseError(
                        f"Ollama returned HTTP status {res.status_code}: {res.text}"
                    )
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise OllamaConnectionError(f"Lost connection to Ollama at {self.base_url}: {str(e)}")
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(
                f"Ollama JSON inference timed out after {call_timeout}s on model {self.model}."
            )
        except (OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError, OllamaResponseError):
            raise
        except Exception as e:
            raise OllamaResponseError(f"Unexpected error in JSON inference: {str(e)}")

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        num_predict: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute multi-turn chat generation against /api/chat.
        Accepts list of {'role': 'user'|'assistant'|'system', 'content': '...'}.
        """
        await self.verify_model_available()

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else 0.4,
                "num_predict": num_predict if num_predict is not None else 600,
            },
        }

        call_timeout = timeout if timeout is not None else self.default_timeout

        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=call_timeout) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                elapsed_ms = round((time.time() - t0) * 1000, 2)

                if res.status_code == 200:
                    data = res.json()
                    msg = data.get("message", {})
                    return {
                        "response": msg.get("content", "").strip(),
                        "role": msg.get("role", "assistant"),
                        "total_duration_ms": elapsed_ms,
                        "model": self.model,
                    }
                elif res.status_code == 404:
                    raise OllamaModelNotFoundError(f"Model '{self.model}' not found on server.")
                else:
                    raise OllamaResponseError(
                        f"Ollama chat returned HTTP status {res.status_code}: {res.text}"
                    )
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise OllamaConnectionError(f"Lost connection to Ollama at {self.base_url}: {str(e)}")
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(
                f"Ollama chat inference timed out after {call_timeout}s on model {self.model}."
            )
        except (OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError, OllamaResponseError):
            raise
        except Exception as e:
            raise OllamaResponseError(f"Unexpected error in chat inference: {str(e)}")

    def _extract_json_dict(self, raw_text: str) -> Dict[str, Any]:
        """
        Sanitize and parse JSON string from Ollama output.
        Handles markdown ```json ... ``` wrappers or text prefixes.
        """
        if not raw_text:
            raise OllamaResponseError("Empty response returned by Ollama.")

        # 1. Direct parse attempt
        try:
            return json.loads(raw_text)
        except Exception:
            pass

        # 2. Markdown fence removal
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except Exception:
                pass

        # 3. Outer bracket extraction
        first_brace = raw_text.find("{")
        last_brace = raw_text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            snippet = raw_text[first_brace : last_brace + 1]
            try:
                return json.loads(snippet)
            except Exception:
                pass

        raise OllamaResponseError(
            f"Failed to parse valid JSON from Ollama output: {raw_text[:200]}..."
        )


ollama_service = OllamaService()
