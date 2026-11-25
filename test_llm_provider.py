"""
test_llm_provider.py - tests for llm_provider.py (JalMitra 4.0 Phase 2).

No internet and no real model are needed: a small mock server (http.server on
127.0.0.1, random port) plays both an Ollama /api/chat endpoint and an
OpenAI-compatible /v1/chat/completions endpoint. The behaviour of the mock is
chosen by the model name in the request.

Run:  python test_llm_provider.py      (exit code 0 when every test passes)
"""

import json
import os
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import llm_provider as lp  # noqa: E402

SCHEMA = {"type": "object", "properties": {"language": {"type": "string"}, "intent": {"type": "string"}},
          "required": ["language", "intent"]}
GOOD = {"language": "en", "intent": "status"}
FAKE_KEY = "test-key-not-real-123"
LAST = {}          # last request seen by the mock: path, body, headers


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, payload, raw=False):
        data = payload if raw else json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        LAST.clear()
        LAST.update(path=self.path, body=body, headers={k.lower(): v for k, v in self.headers.items()})
        model = body.get("model", "")
        content = {"ok": json.dumps(GOOD), "text": "Hello farmer", "badjson": "not json {", "empty": "",
                   "missing": json.dumps({"intent": "status"}), "fenced": "```json\n" + json.dumps(GOOD) + "\n```",
                   "think": "<think>reasoning here</think>" + json.dumps(GOOD),
                   "array": json.dumps([1, 2])}.get(model, json.dumps(GOOD))
        if model == "slow":
            time.sleep(1.5)
        if model == "http500":
            return self._send(500, {"error": "boom " + self.headers.get("Authorization", "")})
        if model == "garbage":
            return self._send(200, b"<html>not json</html>", raw=True)
        if model == "srverror":
            return self._send(200, {"error": "model 'srverror' not found"})
        if self.path == "/api/chat":
            return self._send(200, {"model": model, "message": {"role": "assistant", "content": content},
                                    "done": True, "done_reason": "stop", "prompt_eval_count": 11, "eval_count": 7,
                                    "total_duration": 9_000_000, "load_duration": 1_000_000,
                                    "prompt_eval_duration": 2_000_000, "eval_duration": 5_000_000})
        if self.path == "/v1/chat/completions":
            if model == "noshape":
                return self._send(200, {"choices": []})
            return self._send(200, {"choices": [{"message": {"role": "assistant", "content": content},
                                                 "finish_reason": "stop"}],
                                    "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20}})
        return self._send(404, {"error": "not found"})


class QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        pass        # the client hung up on purpose in the timeout tests; nothing to report


SERVER = QuietServer(("127.0.0.1", 0), Mock)
PORT = SERVER.server_address[1]
URL = f"http://127.0.0.1:{PORT}"
threading.Thread(target=SERVER.serve_forever, daemon=True).start()


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def oll(model, **kw):
    return lp.LLMProvider("ollama", model=model, ollama_url=URL, **kw)


def oai(model, key=None, base=None, **kw):
    return lp.LLMProvider("openai_compatible", model=model, base_url=base or URL, api_key=key, **kw)


MSG = [{"role": "user", "content": "Is Phagi safe?"}]
TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


# ------------------------------------------------------------------ none backend and factory
@test
def none_default_disabled():
    saved = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("JALMITRA_LLM")}
    try:
        p = lp.get_provider()
        r = p.chat(MSG)
        assert p.provider == "none" and not p.is_enabled() and not lp.is_enabled()
        assert r.ok is False and "disabled" in r.error and r.text == "" and r.json is None
    finally:
        os.environ.update(saved)


@test
def factory_reads_env():
    keys = ["JALMITRA_LLM_PROVIDER", "JALMITRA_LLM_MODEL", "JALMITRA_OLLAMA_URL", "JALMITRA_LLM_TIMEOUT"]
    saved = {k: os.environ.get(k) for k in keys}
    try:
        os.environ.update(JALMITRA_LLM_PROVIDER="ollama", JALMITRA_LLM_MODEL="ok", JALMITRA_OLLAMA_URL=URL,
                          JALMITRA_LLM_TIMEOUT="7")
        p = lp.get_provider()
        assert p.provider == "ollama" and p.model == "ok" and p.timeout == 7.0 and lp.is_enabled()
        assert p.chat(MSG, json_schema=SCHEMA).ok
        os.environ["JALMITRA_LLM_TIMEOUT"] = "abc"
        assert lp.get_provider().timeout == lp.DEFAULT_TIMEOUT
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


@test
def unknown_provider_is_disabled():
    p = lp.LLMProvider("gpt-magic")
    r = p.chat(MSG)
    assert not p.is_enabled() and not r.ok and "unknown provider" in r.error


@test
def empty_messages_rejected():
    r = oll("ok").chat([])
    assert not r.ok and "messages" in r.error


# ------------------------------------------------------------------ ollama backend
@test
def ollama_json_ok_and_request_shape():
    r = oll("ok").chat(MSG, json_schema=SCHEMA, temperature=0, max_tokens=64)
    assert r.ok and r.json == GOOD and r.provider == "ollama" and r.model == "ok", r
    b = LAST["body"]
    assert LAST["path"] == "/api/chat" and b["format"] == SCHEMA and b["think"] is False and b["stream"] is False
    assert b["options"]["num_ctx"] == 4096 and b["options"]["temperature"] == 0 and b["options"]["num_predict"] == 64
    assert r.tokens == {"prompt": 11, "completion": 7, "total": 18}
    assert r.meta["eval_duration_ms"] == 5.0 and r.latency_ms > 0


@test
def ollama_text_without_schema():
    r = oll("text").chat(MSG)
    assert r.ok and r.text == "Hello farmer" and r.json is None and "format" not in LAST["body"]


@test
def ollama_think_flag_passed():
    oll("ok").chat(MSG, think=True)
    assert LAST["body"]["think"] is True


@test
def ollama_bad_json():
    r = oll("badjson").chat(MSG, json_schema=SCHEMA)
    assert not r.ok and "invalid JSON" in r.error


@test
def ollama_missing_required_key():
    r = oll("missing").chat(MSG, json_schema=SCHEMA)
    assert not r.ok and "language" in r.error and r.json == {"intent": "status"}


@test
def ollama_array_not_object():
    r = oll("array").chat(MSG, json_schema=SCHEMA)
    assert not r.ok and "not a JSON object" in r.error


@test
def ollama_fenced_and_think_tags_tolerated():
    assert oll("fenced").chat(MSG, json_schema=SCHEMA).json == GOOD
    r = oll("think").chat(MSG, json_schema=SCHEMA)
    assert r.ok and r.json == GOOD


@test
def ollama_empty_text():
    r = oll("empty").chat(MSG)
    assert not r.ok and r.error == "empty response"


@test
def ollama_timeout():
    t0 = time.perf_counter()
    r = oll("slow").chat(MSG, json_schema=SCHEMA, timeout=0.3)
    assert not r.ok and "timeout" in r.error and time.perf_counter() - t0 < 1.4, r.error


@test
def ollama_connection_refused():
    r = lp.LLMProvider("ollama", model="ok", ollama_url=f"http://127.0.0.1:{free_port()}").chat(MSG, timeout=3)
    assert not r.ok and ("refused" in r.error or "connection" in r.error), r.error


@test
def ollama_http_error():
    r = oll("http500").chat(MSG)
    assert not r.ok and r.error.startswith("HTTP 500")


@test
def ollama_server_error_field():
    r = oll("srverror").chat(MSG)
    assert not r.ok and "not found" in r.error


@test
def ollama_garbage_body():
    r = oll("garbage").chat(MSG)
    assert not r.ok and r.error == "server returned invalid JSON"


# ------------------------------------------------------------------ openai-compatible backend
@test
def openai_json_ok_and_request_shape():
    r = oai("ok", key=FAKE_KEY).chat(MSG, json_schema=SCHEMA, max_tokens=50)
    assert r.ok and r.json == GOOD and r.provider == "openai_compatible"
    b = LAST["body"]
    assert LAST["path"] == "/v1/chat/completions" and b["max_tokens"] == 50 and b["temperature"] == 0
    assert b["response_format"]["type"] == "json_schema" and b["response_format"]["json_schema"]["schema"] == SCHEMA
    assert LAST["headers"]["authorization"] == "Bearer " + FAKE_KEY
    assert r.tokens == {"prompt": 12, "completion": 8, "total": 20}


@test
def openai_base_url_with_v1():
    r = oai("text", base=URL + "/v1").chat(MSG)
    assert r.ok and LAST["path"] == "/v1/chat/completions" and "authorization" not in LAST["headers"]


@test
def openai_missing_base_url():
    r = lp.LLMProvider("openai_compatible", model="ok").chat(MSG)
    assert not r.ok and "BASE_URL" in r.error


@test
def openai_bad_json_and_missing_key():
    assert "invalid JSON" in oai("badjson").chat(MSG, json_schema=SCHEMA).error
    assert "missing required keys" in oai("missing").chat(MSG, json_schema=SCHEMA).error


@test
def openai_unexpected_shape():
    r = oai("noshape").chat(MSG)
    assert not r.ok and "unexpected response shape" in r.error


@test
def openai_timeout():
    r = oai("slow").chat(MSG, timeout=0.3)
    assert not r.ok and "timeout" in r.error


@test
def openai_connection_refused():
    r = oai("ok", base=f"http://127.0.0.1:{free_port()}").chat(MSG, timeout=3)
    assert not r.ok and r.error


@test
def api_key_never_leaks():
    p = oai("http500", key=FAKE_KEY)
    r = p.chat(MSG)          # the mock echoes the Authorization header in its error body
    assert not r.ok and FAKE_KEY not in r.error and "***" in r.error, r.error
    assert FAKE_KEY not in repr(p)


# ------------------------------------------------------------------ helpers and isolation
@test
def parse_and_validate_helpers():
    assert lp.parse_json_text('x {"a": 1} y') == ({"a": 1}, None)
    assert lp.parse_json_text(None)[1] == "empty response"
    assert lp.validate_json({"language": "en"}, SCHEMA) == "missing required keys: intent"
    assert lp.validate_json(GOOD, SCHEMA) is None and lp.validate_json([], None) is None


@test
def not_imported_by_existing_modules():
    # Phase 3: only the new LLM modules may use the provider; the 3.0 modules (engine.py included) must not
    allowed = {"llm_provider.py", "test_llm_provider.py", "llm_compose.py", "test_v4_llm.py",
               "ui_chat_v4.py", "test_v4_semantic.py", "test_v4_ui.py",      # Phase 4 (dev-mode AI only)
               "test_v5.py",                                                 # Phase 5 tests
               "jalmitra_ai.py", "test_v6.py", "fake_ai_for_tests.py"}        # Phase 6: AI-first replies + test fake
    users = [p.name for p in BASE.glob("*.py")
             if p.name not in allowed and "llm_provider" in p.read_text(encoding="utf-8", errors="replace")]
    assert users == [], users


@test
def stdlib_only():
    src = (BASE / "llm_provider.py").read_text(encoding="utf-8")
    imported = {line.split()[1].split(".")[0] for line in src.splitlines()
                if line.startswith(("import ", "from "))}
    assert imported <= {"json", "os", "re", "socket", "time", "urllib", "dataclasses"}, imported


def main():
    passed, failed = 0, []
    t0 = time.perf_counter()
    for fn in TESTS:
        try:
            fn()
            passed += 1
            print(f"PASSED  {fn.__name__}")
        except Exception as e:
            failed.append(fn.__name__)
            print(f"FAILED  {fn.__name__}: {type(e).__name__}: {e}")
    SERVER.shutdown()
    print(f"\nllm_provider tests: {passed} passed, {len(failed)} failed of {len(TESTS)} "
          f"({(time.perf_counter() - t0):.1f} s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
