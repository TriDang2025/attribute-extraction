"""Minimal OpenAI-compatible chat and embedding client using the standard library."""

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class OpenAICompatibleClient:
    """Client for OpenAI-compatible endpoints such as vLLM, LM Studio, and Ollama."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: Optional[str] = None,
        embedding_model: Optional[str] = None,
        timeout: float = 120.0,
        temperature: float = 0.5,
        top_p: float = 0.5,
        reasoning_effort: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> None:
        if not base_url.strip():
            raise ValueError("base_url must not be empty")
        if not model.strip():
            raise ValueError("model must not be empty")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.embedding_model = embedding_model
        self.timeout = timeout
        if not 0.0 <= temperature <= 2.0:
            raise ValueError("temperature must be between 0 and 2")
        if not 0.0 < top_p <= 1.0:
            raise ValueError("top_p must be greater than 0 and at most 1")
        self.temperature = temperature
        self.top_p = top_p
        self.reasoning_effort = reasoning_effort
        self.seed = seed
        self.endpoint_attempts = 4
        self.endpoint_retry_seconds = 90.0

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            message = error.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(
                f"Model endpoint returned HTTP {error.code} for {path}: {message}"
            ) from error
        except urllib.error.URLError as error:
            raise RuntimeError(
                f"Could not reach model endpoint at {self.base_url}: {error.reason}"
            ) from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Model endpoint returned invalid JSON for {path}") from error
        if not isinstance(result, dict):
            raise RuntimeError(f"Model endpoint returned a non-object response for {path}")
        return result

    def chat(
        self,
        system: Optional[str],
        user: str,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        messages = [{"role": "system", "content": system}] if system else []
        payload = {
            "model": self.model,
            "messages": messages + [{"role": "user", "content": user}],
            "temperature": self.temperature if temperature is None else temperature,
            "top_p": self.top_p if top_p is None else top_p,
        }
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        if self.seed is not None:
            payload["seed"] = self.seed
        if max_tokens:
            payload["max_tokens"] = max_tokens
        # A crashed or reloading endpoint is not a model answer: wait and retry before failing.
        for attempt in range(1, self.endpoint_attempts + 1):
            try:
                response = self._post("/chat/completions", payload)
                break
            except RuntimeError:
                if attempt == self.endpoint_attempts:
                    raise
                time.sleep(self.endpoint_retry_seconds)
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError("Model response has no choices[0].message.content") from error
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Model returned an empty response")
        return content.strip()

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not self.embedding_model:
            raise RuntimeError("Set an embedding_model to enable semantic dense retrieval")
        response = self._post(
            "/embeddings",
            {"model": self.embedding_model, "input": texts},
        )
        try:
            data = response["data"]
            vectors = [None] * len(texts)
            for item in data:
                index = item["index"]
                vector = item["embedding"]
                if not isinstance(index, int) or not 0 <= index < len(texts):
                    raise ValueError("embedding index is outside the requested input range")
                if not isinstance(vector, list) or not vector:
                    raise ValueError("embedding vector must be a non-empty list")
                vectors[index] = [float(value) for value in vector]
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError(f"Invalid embedding response: {error}") from error
        if any(vector is None for vector in vectors):
            raise RuntimeError("Embedding response did not include every requested input")
        dimensions = {len(vector) for vector in vectors}
        if len(dimensions) > 1:
            raise RuntimeError("Embedding response vectors have inconsistent dimensions")
        return vectors


class CachedEmbedder:
    """Embeds each distinct text once and keeps the vectors in a JSON file.

    Semantic utility (Eq. 10) compares every input with the whole pool, so the pool would
    otherwise be re-embedded for every input text."""

    def __init__(self, client: OpenAICompatibleClient, path: Optional[str] = None, prefix: str = "") -> None:
        self.client = client
        self.path = path
        self.prefix = prefix  # e.g. an instruction for instruction-tuned embedders
        self.cache: Dict[str, List[float]] = {}
        if path:
            try:
                with open(path, "r", encoding="utf-8") as source:
                    self.cache = json.load(source)
            except FileNotFoundError:
                pass

    def embed(self, texts: List[str]) -> List[List[float]]:
        missing = [t for t in dict.fromkeys(texts) if t not in self.cache]
        for start in range(0, len(missing), 8):
            batch = missing[start:start + 8]
            for text, vector in zip(batch, self.client.embed([self.prefix + t for t in batch])):
                self.cache[text] = vector
            if self.path:  # save per batch so an interrupted run keeps its work
                with open(self.path, "w", encoding="utf-8") as target:
                    json.dump(self.cache, target)
        return [self.cache[t] for t in texts]


class LlamaCppEmbedder:
    """SFR-Embedding-Mistral served by llama.cpp (`--embedding --pooling last`).

    The model card's recipe: last-token pooling with the EOS token appended, so each input
    is sent as token ids [BOS] + tokens + [EOS]."""

    def __init__(self, base_url: str = "http://localhost:8082", timeout: float = 1800.0,
                 bos_id: int = 1, eos_id: int = 2) -> None:
        self.client = OpenAICompatibleClient(base_url + "/v1", "sfr-embedding-mistral", timeout=timeout)
        self.base_url = base_url.rstrip("/")
        self.bos_id, self.eos_id = bos_id, eos_id

    def embed(self, texts: List[str]) -> List[List[float]]:
        vectors = []
        for text in texts:
            request = urllib.request.Request(
                f"{self.base_url}/tokenize", data=json.dumps({"content": text, "parse_special": False}).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(request, timeout=self.client.timeout) as response:
                tokens = json.loads(response.read().decode("utf-8"))["tokens"]
            result = self.client._post("/embeddings", {"input": [[self.bos_id] + tokens + [self.eos_id]]})
            vectors.append([float(v) for v in result["data"][0]["embedding"]])
        return vectors
