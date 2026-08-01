import base64

with open('/home/user/chat.html', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('ascii')

TEMPLATE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RunPod server — Qwen3-32B abliterated (uncensored) + chat UI + agent tools.
RunPod exposes port 8000 automatically at:  https://<POD_ID>-8000.proxy.runpod.net

روش اجرا (توی پاد RunPod):
    python3 runpod_server.py
"""
import os, sys, json, base64, subprocess

# ===== CONFIG =====
MODEL_REPO  = "mradermacher/Llama-3.3-70B-Instruct-abliterated-GGUF"
MODEL_FILE  = "Llama-3.3-70B-Instruct-abliterated.Q4_K_M.gguf"
MODEL_NAME  = "llama3.3-70b-abliterated"
CONTEXT_SIZE = 16384
GPU_LAYERS  = -1
PORT        = 8000
WORKSPACE   = "/workspace"
# ==================

def _sh(c):
    print("$ " + c, flush=True)
    subprocess.run(c, shell=True, check=False)

# 1) پیش‌نیازها (اگه نصب نباشن)
import importlib
_need = False
for _m in ("llama_cpp", "fastapi", "uvicorn", "huggingface_hub"):
    try:
        importlib.import_module(_m)
    except Exception:
        _need = True
if _need:
    _sh(sys.executable + " -m pip install -q llama-cpp-python==0.3.34 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124")
    _sh(sys.executable + " -m pip install -q fastapi uvicorn huggingface_hub")

# 2) دانلود مدل به /workspace (ماندگار روی پاد)
from huggingface_hub import hf_hub_download
MODEL_DIR = os.path.join(WORKSPACE, "models")
os.makedirs(MODEL_DIR, exist_ok=True)
local_path = os.path.join(MODEL_DIR, MODEL_FILE)
if not (os.path.exists(local_path) and os.path.getsize(local_path) > 35e9):
    print("⏬ دانلود مدل (~20GB، بار اول)...", flush=True)
    hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE, local_dir=MODEL_DIR)
print("مدل:", local_path, flush=True)

# 3) رابط چت
os.makedirs(WORKSPACE, exist_ok=True)
CHAT_HTML_B64 = "__B64__"
HTML_PATH = os.path.join(WORKSPACE, "chat.html")
open(HTML_PATH, "wb").write(base64.b64decode(CHAT_HTML_B64))

# 4) بارگذاری مدل
from llama_cpp import Llama
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
print("⏳ بارگذاری مدل روی GPU (چند دقیقه)...", flush=True)
llm = Llama(model_path=local_path, n_gpu_layers=GPU_LAYERS, n_ctx=CONTEXT_SIZE, chat_format="llama-3", verbose=False)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def _index():
    return FileResponse(HTML_PATH, media_type="text/html", headers={"Cache-Control": "no-store"})

@app.get("/health")
def _health(): return {"status": "ok"}

@app.get("/v1/models")
def _models(): return {"object": "list", "data": [{"id": MODEL_NAME, "object": "model"}]}

def _call(messages, stream, **p):
    return llm.create_chat_completion(messages=messages, stream=stream, **p)

@app.post("/v1/chat/completions")
async def _chat(req: Request):
    body = await req.json()
    msgs = body.get("messages", [])
    p = dict(max_tokens=int(body.get("max_tokens", 2048)), temperature=float(body.get("temperature", 0.3)), top_p=0.95)
    if body.get("stream"):
        def gen():
            try:
                for ch in _call(msgs, stream=True, **p):
                    yield "data: " + json.dumps(ch) + "\n\n"
            except Exception as e:
                print("ERR", repr(e), flush=True)
                yield "data: " + json.dumps({"choices": [{"index": 0, "delta": {"content": "[ERR " + str(e)[:300] + "]"}}]}) + "\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-store"})
    try:
        return _call(msgs, stream=False, **p)
    except Exception as e:
        return {"error": {"message": str(e)}}

# 5) ابزارهای ایجنت روی /workspace/workspace
AWS = os.path.join(WORKSPACE, "workspace")
os.makedirs(AWS, exist_ok=True)
def _res(path):
    p = os.path.realpath(os.path.join(AWS, path))
    if not (p == AWS or p.startswith(AWS + os.sep)):
        raise PermissionError("outside workspace")
    return p
@app.post("/v1/tools/bash")
async def _bash(req: Request):
    cmd = (await req.json()).get("cmd", "")
    try:
        r = subprocess.run(cmd, shell=True, cwd=AWS, capture_output=True, text=True, timeout=600)
        out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
        return {"result": out.strip()[:12000] + (("\n[exit " + str(r.returncode) + "]") if r.returncode else "")}
    except subprocess.TimeoutExpired:
        return {"result": "[timeout 600s]"}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]"}
@app.post("/v1/tools/read_file")
async def _rd(req: Request):
    try:
        return {"result": open(_res((await req.json()).get("path", "")), encoding="utf-8", errors="replace").read()[:12000]}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]"}
@app.post("/v1/tools/write_file")
async def _wf(req: Request):
    try:
        b = await req.json(); p = _res(b.get("path", "")); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(b.get("content", "")); return {"result": "[written] " + b.get("path", "")}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]"}
@app.post("/v1/tools/edit_file")
async def _ef(req: Request):
    try:
        b = await req.json(); p = _res(b.get("path", "")); t = open(p, encoding="utf-8").read()
        old = b.get("old_text", ""); new = b.get("new_text", "")
        if old not in t: return {"result": "[error: old_text not found]"}
        open(p, "w", encoding="utf-8").write(t.replace(old, new, 1)); return {"result": "[edited] " + b.get("path", "")}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]"}
@app.post("/v1/tools/list_dir")
async def _ls(req: Request):
    try:
        b = await req.json(); root = _res(b.get("path", ".")); rows = []
        for r, ds, fs in os.walk(root):
            ds[:] = [d for d in ds if d not in (".git", "node_modules", "__pycache__")]
            rel = os.path.relpath(r, AWS)
            for f in fs: rows.append(os.path.join(rel, f) if rel != "." else f)
            if not b.get("recursive"): ds[:] = []
        return {"result": "\n".join(sorted(rows)[:300]) or "[empty]"}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]"}
@app.post("/v1/upload")
async def _up(req: Request):
    try:
        b = await req.json(); fn = "".join(c for c in os.path.basename(b.get("filename", "u.bin")) if c.isalnum() or c in "._-")
        p = _res(fn); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "wb").write(base64.b64decode(b.get("content", "")))
        return {"result": "[uploaded] " + fn, "path": p}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]", "path": ""}

if __name__ == "__main__":
    print("\n" + "=" * 52)
    print("✅ آماده! آدرس چت در پنل RunPod (port %d):" % PORT)
    print("   https://<POD_ID>-%d.proxy.runpod.net" % PORT)
    print("=" * 52 + "\n", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
'''

out = TEMPLATE.replace('"__B64__"', '"' + b64 + '"')
with open('/home/user/runpod_server.py', 'w', encoding='utf-8') as f:
    f.write(out)
print("runpod_server.py written, size:", len(out))
