"""wf_v4.1 dry-run model: Google Gemini over its REST API (no SDK), for prompt and code tests before the Nov 16 Qwen batch.

DRY RUN ONLY: answers from this module test prompts and code; they are never results (diary 6 Nov, rules). The user chose Gemini instead of
ChatGPT for the dry runs and the judge (2026-11-07).

- Key: env var GEMINI_API_KEY (never logged, never written to a file).
- Guided JSON: `responseMimeType: application/json` plus the job's JSON schema as `responseJsonSchema`. If the API rejects the schema
  (HTTP 400 that names the schema), the call is retried once without it and the answer is marked guided=False.
- Cache: one JSON file per call under `cache_dir`, keyed by sha256(model, temperature, max_tokens, schema, prompt, tag); a rerun reads it.
- Temperature: the job's "temperature" (default 0); the judge jobs use 1.0, like a fresh chat in the app.
- Retries: 5 tries with backoff 2, 4, 8, 16 s on HTTP 429/5xx and network errors; no retry on other 4xx.
"""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://generativelanguage.googleapis.com/v1beta"
RETRY_CODES = {429, 500, 502, 503, 504}


class GeminiError(RuntimeError):
    pass


def _user_env(name):
    """A user environment variable set after this process started (Windows: HKCU\\Environment, as `setx` writes it), else ""."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            return str(winreg.QueryValueEx(k, name)[0])
    except (ImportError, OSError):
        return ""


def _key():
    k = os.environ.get("GEMINI_API_KEY", "") or _user_env("GEMINI_API_KEY")
    if not k:
        raise GeminiError("GEMINI_API_KEY is not set (set it as an environment variable; never paste it in chat or files)")
    return k


def _post(url, body, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": _key()})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _call(url, body, timeout=600, tries=5, sleep=time.sleep):
    for i in range(tries):
        try:
            return _post(url, body, timeout)
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:500]
            if e.code not in RETRY_CODES or i == tries - 1:
                raise GeminiError(f"HTTP {e.code}: {msg}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if i == tries - 1:
                raise GeminiError(f"network: {e}") from None
        sleep(2 ** (i + 1))


def list_models(timeout=60):
    """Names of the models that support generateContent."""
    req = urllib.request.Request(f"{API}/models?pageSize=200", headers={"x-goog-api-key": _key()})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [m["name"].split("/", 1)[1] for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]


def strip_schema(schema):
    """Copy of a JSON schema without the keywords the Gemini schema subset may reject (`pattern`)."""
    if isinstance(schema, dict):
        return {k: strip_schema(v) for k, v in schema.items() if k != "pattern"}
    if isinstance(schema, list):
        return [strip_schema(v) for v in schema]
    return schema


def cache_key(model, prompt, schema, temperature, max_tokens, tag=""):
    blob = json.dumps([model, temperature, max_tokens, schema, prompt, tag], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def generate(prompt, schema, model, cache_dir, temperature=0.0, max_tokens=8192, call=_call, tag=""):
    """{"raw", "guided", "model", "finish_reason", "prompt_tokens", "output_tokens", "cached"}; `call` is injectable for tests. `tag` only
    enters the cache key (a repeat of the same prompt, e.g. a judge's second answer, gets its own call)."""
    cache_dir = Path(cache_dir)
    k = cache_key(model, prompt, schema, temperature, max_tokens, tag)
    f = cache_dir / f"{k}.json"
    if f.exists():
        return {**json.loads(f.read_text(encoding="utf-8")), "cached": True}
    cfg = {"temperature": temperature, "maxOutputTokens": max_tokens, "responseMimeType": "application/json"}
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": cfg}
    guided = schema is not None
    if guided:
        cfg["responseJsonSchema"] = strip_schema(schema)
    url = f"{API}/models/{model}:generateContent"
    try:
        resp = call(url, body)
    except GeminiError as e:
        if not (guided and "400" in str(e) and "chema" in str(e)):
            raise
        cfg.pop("responseJsonSchema")
        guided = False
        resp = call(url, body)
    cand = (resp.get("candidates") or [{}])[0]
    raw = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts", []) if not p.get("thought"))
    use = resp.get("usageMetadata", {})
    row = {"raw": raw, "guided": guided, "model": resp.get("modelVersion", model), "finish_reason": cand.get("finishReason", ""),
           "prompt_tokens": use.get("promptTokenCount"), "output_tokens": use.get("candidatesTokenCount"),
           "thinking_tokens": use.get("thoughtsTokenCount")}
    cache_dir.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
    return {**row, "cached": False}


def responder(model, cache_dir, max_tokens=None, **kw):
    """A `respond(job, prompt, schema) -> raw` function for batch_v4_fake.run_jobs; the last call's metadata is in `.last`."""
    def respond(job, prompt, schema):
        r = generate(prompt, schema, model, cache_dir, max_tokens=max_tokens or job.get("max_tokens") or 8192,
                     temperature=job.get("temperature", 0.0), tag=job.get("run_tag", ""), **kw)
        respond.last = r
        return r["raw"]
    respond.last = None
    respond.model = model
    return respond
