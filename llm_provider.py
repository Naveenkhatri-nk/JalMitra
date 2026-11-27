"""
llm_provider.py - optional LLM access for JalMitra 4.0 (Phase 2, standard library only).

Nothing in the existing app imports this module. With the default settings the
provider is "none" and every call returns ok=False, so JalMitra behaves exactly
as the rule-based 3.0 version.

Settings (environment variables only, never hard-coded):

  JALMITRA_LLM_PROVIDER   ollama | openai_compatible | none      (default: none)
  JALMITRA_LLM_MODEL      model name          (default: qwen3:4b-instruct-2507-q4_K_M)
  JALMITRA_OLLAMA_URL     default http://localhost:11434
  JALMITRA_LLM_BASE_URL   base URL of an OpenAI-compatible server (with or without /v1)
  JALMITRA_LLM_API_KEY    API key for the OpenAI-compatible server (read from env, never logged)
  JALMITRA_LLM_TIMEOUT    seconds per request                     (default: 60)

Usage:

  from llm_provider import get_provider
  llm = get_provider()
  res = llm.chat([{"role": "user", "content": "..."}], json_schema=SCHEMA)
  if res.ok: use(res.json or res.text)        # otherwise fall back to the rules

chat() never raises: connection errors, timeouts, HTTP errors, invalid JSON and
missing required keys all come back as ok=False with a short error message.
"""

import json
import os
import re
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

PROVIDERS = ("ollama", "openai_compatible", "none")
DEFAULT_MODEL = "qwen3:4b-instruct-2507-q4_K_M"   # Phase 2: the plain qwen3:4b tag is the Thinking build
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_TIMEOUT = 60.0
DEFAULT_NUM_CTX = 4096
DEFAULT_MAX_TOKENS = 512

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.S)
_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.S | re.I)


@dataclass
class LLMResult:
    text: str = ""
    json: object = None
    ok: bool = False
    error: str = None
    latency_ms: float = 0.0
    provider: str = "none"
    model: str = ""
    tokens: dict = field(default_factory=dict)   # prompt, completion, total (when the server reports them)
    meta: dict = field(default_factory=dict)     # backend timings (Ollama: load/prompt_eval/eval durations in ms)


def _env(name, default=None):
    v = os.environ.get(name)
    return v.strip() if v and v.strip() else default


def _timeout_from_env():
    try:
        t = float(_env("JALMITRA_LLM_TIMEOUT", DEFAULT_TIMEOUT))
        return t if t > 0 else DEFAULT_TIMEOUT
    except ValueError:
        return DEFAULT_TIMEOUT


def parse_json_text(text):
    """Parse a JSON object from model text (tolerates ```json fences and <think> blocks). Returns (obj, error)."""
    if text is None:
        return None, "empty response"
    t = _THINK_BLOCK.sub("", text).strip()
    m = _FENCE.match(t)
    if m:
        t = m.group(1)
    try:
        return json.loads(t), None
    except (ValueError, TypeError):
        pass
    a, b = t.find("{"), t.rfind("}")
    if a != -1 and b > a:
        try:
            return json.loads(t[a:b + 1]), None
        except ValueError:
            pass
    return None, "invalid JSON in model output"


def validate_json(obj, schema):
    """Light check against a JSON schema: object type and required keys. Returns an error string or None."""
    if not schema:
        return None
    if schema.get("type") == "object" and not isinstance(obj, dict):
        return "model output is not a JSON object"
    if isinstance(obj, dict):
        missing = [k for k in schema.get("required", []) if k not in obj]
        if missing:
            return "missing required keys: " + ", ".join(missing)
    return None


class LLMProvider:
    """One configured backend. Use get_provider() to build it from the environment."""

    def __init__(self, provider="none", model=None, ollama_url=None, base_url=None, api_key=None, timeout=None,
                 num_ctx=DEFAULT_NUM_CTX):
        provider = (provider or "none").strip().lower()
        self.provider = provider if provider in PROVIDERS else "none"
        self.config_error = None if provider in PROVIDERS else f"unknown provider '{provider}'"
        self.model = model or DEFAULT_MODEL
        self.ollama_url = (ollama_url or DEFAULT_OLLAMA_URL).rstrip("/")
        self.base_url = (base_url or "").rstrip("/")
        self._api_key = api_key or None
        self.timeout = float(timeout) if timeout else DEFAULT_TIMEOUT
        # 27 Nov 2026 (cloud AI): optional "reasoning_effort" (Gemini: low / medium / high) and a lowest max_tokens,
        # because thinking models count their thinking in max_tokens (an 8-token self-check would come back empty)
        self.reasoning_effort = _env("JALMITRA_LLM_REASONING_EFFORT")
        try:
            self.min_max_tokens = int(_env("JALMITRA_LLM_MIN_MAX_TOKENS", "0"))
        except ValueError:
            self.min_max_tokens = 0
        self.num_ctx = num_ctx

    def __repr__(self):     # never shows the key
        return f"LLMProvider(provider={self.provider!r}, model={self.model!r}, key={'set' if self._api_key else 'unset'})"

    def is_enabled(self):
        return self.provider != "none"

    # ------------------------------------------------------------------ public
    def chat(self, messages, json_schema=None, temperature=0, max_tokens=DEFAULT_MAX_TOKENS, timeout=None,
             think=False):
        """Send a chat request. Never raises; check result.ok."""
        t0 = time.perf_counter()
        res = LLMResult(provider=self.provider, model=self.model if self.is_enabled() else "")
        try:
            if not self.is_enabled():
                res.error = self.config_error or "LLM disabled (JALMITRA_LLM_PROVIDER is none)"
                return res
            if not isinstance(messages, list) or not messages:
                res.error = "messages must be a non-empty list"
                return res
            t = float(timeout) if timeout else self.timeout
            if self.provider == "ollama":
                self._ollama(res, messages, json_schema, temperature, max_tokens, t, think)
            else:
                self._openai(res, messages, json_schema, temperature, max_tokens, t)
            if res.error is None:
                self._finish_json(res, json_schema)
        except Exception as e:      # last resort: the caller must never see an exception
            res.ok, res.error = False, f"unexpected error: {type(e).__name__}: {self._safe(str(e))}"
        finally:
            res.latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        return res

    # ------------------------------------------------------------------ backends
    def _ollama(self, res, messages, schema, temperature, max_tokens, timeout, think):
        body = {"model": self.model, "messages": messages, "stream": False, "think": bool(think),
                "keep_alive": keep_alive(),
                "options": {"temperature": temperature, "num_ctx": self.num_ctx, "num_predict": max_tokens}}
        if schema:
            body["format"] = schema
        data = self._post(res, self.ollama_url + "/api/chat", body, {}, timeout)
        if data is None and res.error and "think" in res.error.lower() and not think:
            res.error = None                       # a model without a thinking mode may reject the field
            body.pop("think")
            data = self._post(res, self.ollama_url + "/api/chat", body, {}, timeout)
        if data is None:
            return
        if data.get("error"):
            res.error = "server error: " + self._safe(str(data["error"]))[:300]
            return
        msg = data.get("message") or {}
        res.text = _THINK_BLOCK.sub("", msg.get("content") or "").strip()
        if msg.get("thinking"):
            res.meta["thinking_chars"] = len(msg["thinking"])
        pe, ev = data.get("prompt_eval_count"), data.get("eval_count")
        res.tokens = {k: v for k, v in (("prompt", pe), ("completion", ev),
                                        ("total", (pe or 0) + (ev or 0) if pe is not None or ev is not None else None))
                      if v is not None}
        for k in ("total_duration", "load_duration", "prompt_eval_duration", "eval_duration"):
            if isinstance(data.get(k), (int, float)):
                res.meta[k + "_ms"] = round(data[k] / 1e6, 1)
        res.meta["done_reason"] = data.get("done_reason")

    def _openai(self, res, messages, schema, temperature, max_tokens, timeout):
        if not self.base_url:
            res.error = "JALMITRA_LLM_BASE_URL is not set"
            return
        # ".../v1" (OpenAI, Groq) and ".../v1beta/openai" (Google Gemini) already end in the API version
        versioned = self.base_url.endswith("/v1") or self.base_url.endswith("/openai")
        url = self.base_url + ("/chat/completions" if versioned else "/v1/chat/completions")
        body = {"model": self.model, "messages": messages, "temperature": temperature,
                "max_tokens": max(int(max_tokens or 0), self.min_max_tokens) or max_tokens}
        if self.reasoning_effort:
            body["reasoning_effort"] = self.reasoning_effort
        if schema:
            body["response_format"] = {"type": "json_schema",
                                       "json_schema": {"name": "jalmitra_response", "schema": schema}}
        headers = {"Authorization": "Bearer " + self._api_key} if self._api_key else {}
        data = self._post(res, url, body, headers, timeout)
        if data is None:
            return
        if data.get("error"):
            err = data["error"]
            res.error = "server error: " + self._safe(str(err.get("message") if isinstance(err, dict) else err))[:300]
            return
        try:
            choice = data["choices"][0]
            res.text = _THINK_BLOCK.sub("", choice["message"].get("content") or "").strip()
            res.meta["finish_reason"] = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError, AttributeError):
            res.error = "unexpected response shape (no choices[0].message)"
            return
        u = data.get("usage") or {}
        res.tokens = {k2: u[k1] for k1, k2 in (("prompt_tokens", "prompt"), ("completion_tokens", "completion"),
                                               ("total_tokens", "total")) if isinstance(u.get(k1), int)}

    # ------------------------------------------------------------------ helpers
    def _post(self, res, url, body, headers, timeout):
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json", "Accept": "application/json",
                                              **headers})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            res.error = f"HTTP {e.code} from server" + (": " + self._safe(detail) if detail else "")
            return None
        except urllib.error.URLError as e:
            reason = e.reason
            if isinstance(reason, (socket.timeout, TimeoutError)):
                res.error = f"timeout after {timeout:g}s"
            elif isinstance(reason, ConnectionRefusedError):
                res.error = "connection refused (is the LLM server running?)"
            else:
                res.error = "connection error: " + self._safe(str(reason))[:200]
            return None
        except (socket.timeout, TimeoutError):
            res.error = f"timeout after {timeout:g}s"
            return None
        except ConnectionError as e:
            res.error = "connection error: " + type(e).__name__
            return None
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            res.error = "server returned invalid JSON"
            return None
        if not isinstance(data, dict):
            res.error = "server returned a non-object JSON body"
            return None
        return data

    def _finish_json(self, res, schema):
        if not schema:
            res.ok = bool(res.text)
            if not res.ok:
                res.error = "empty response"
            return
        obj, err = parse_json_text(res.text)
        if err:
            res.error = err
            return
        err = validate_json(obj, schema)
        if err:
            res.json, res.error = obj, err
            return
        res.json, res.ok = obj, True

    def _safe(self, s):
        """Remove the API key from any text that could reach a log or the UI."""
        return s.replace(self._api_key, "***") if self._api_key and s else s


def keep_alive():
    """How long Ollama keeps the model in GPU memory after a request (Phase 6: avoid reloads). Env JALMITRA_KEEP_ALIVE."""
    return _env("JALMITRA_KEEP_ALIVE", "30m")


def get_provider():
    """Build the provider from the environment (read on every call, so tests can change it)."""
    return LLMProvider(provider=_env("JALMITRA_LLM_PROVIDER", "none"),
                       model=_env("JALMITRA_LLM_MODEL", DEFAULT_MODEL),
                       ollama_url=_env("JALMITRA_OLLAMA_URL", DEFAULT_OLLAMA_URL),
                       base_url=_env("JALMITRA_LLM_BASE_URL", ""),
                       api_key=_env("JALMITRA_LLM_API_KEY"),
                       timeout=_timeout_from_env())


def is_enabled():
    return get_provider().is_enabled()
