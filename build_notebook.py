import json, base64

with open('/home/user/chat.html', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('ascii')

def code(src):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}

def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}

cells = []

cells.append(md("""# 🚀 Colab → مدل LLM بدون محدودیت (نسخه‌ی پایدار)

این نوت‌بوک روی **Google Colab (GPU رایگان T4)** یک مدل **uncensored** بالا می‌آورد، یک تونل عمومی می‌سازد و یک رابط چت کامل در مرورگرت می‌دهد.

### چرا «پایدار»؟
- **تاریخچه‌ی گفتگو در مرورگر تو ذخیره می‌شود** (نه در Colab). پس قطعی/ریست Colab به گفتگوی تو دست نمی‌زند.
- مدل روی **دیسک محلی Colab (/content)** دانلود می‌شود — بدون نیاز به Drive و بدون مصرف فضای Drive شما.
- از **cloudflared tunnel** استفاده می‌کنیم (رایگان، بدون نیاز به اکانت، بدون صفحه‌ی مزاحم مثل ngrok).

### حدود صادقانه (دست گوگل است):
- Idle-disconnect (~۹۰ دقیقه بی‌فعالیتی) → با کد پایین کم می‌شود.
- حداکثر سشن رایگان ~۱۲ ساعت → قابل حذف **نیست**. (برای ۲۴/۷ واقعی: Colab Pro+ یا RunPod ساعتی.)

---

**روش اجرا:** از بالا به پایین هر سلول را به ترتیب Run کن (Shift+Enter)."""))

cells.append(code("""# ۱) بررسی GPU — باید T4 (یا بهتر) ببینی
!nvidia-smi || echo '❌ GPU پیدا نشد. به Runtime > Change runtime type برو و GPU را انتخاب کن.'"""))

cells.append(code("""# ۲) تنظیمات — فقط این قسمت را (در صورت نیاز) تغییر بده

# مدل: Qwen3-14B Abliterated (uncensored) با کوانت Q4_K_M (~9GB) -> روی T4 جا می‌شود
MODEL_REPO = "bartowski/huihui-ai_Qwen3-14B-abliterated-GGUF"
MODEL_FILE = "huihui-ai_Qwen3-14B-abliterated-Q4_K_M.gguf"
MODEL_NAME = "qwen3-14b-abliterated"      # این نام را بعداً در صفحه‌ی چت وارد می‌کنی

CONTEXT_SIZE = 8192
GPU_LAYERS   = -1     # -1 = همه‌ی لایه‌ها روی GPU
PORT         = 8000
EXPECTED_BYTES = 9001749568   # سایز دقیق فایل Q4_K_M — برای تشخیص فایل ناقص

# --- مدل‌های جایگزین (فقط MODEL_REPO و MODEL_FILE را عوض کن؛ پیشوند فایل مهم است) ---
# کیفیت بالاتر (سنگین‌تر): bartowski/huihui-ai_Qwen3-14B-abliterated-GGUF | huihui-ai_Qwen3-14B-abliterated-Q5_K_M.gguf
# مدل دیگر ۱۴B:            bartowski/mlabonne_Qwen3-14B-abliterated-GGUF  | mlabonne_Qwen3-14B-abliterated-Q4_K_M.gguf
# برای مدل دلخواه: در huggingface.co عبارت abliterated GGUF را جستجو کن."""))

cells.append(code("""# ۳) نصب — wheel از پیش‌کامپایل‌شده با CUDA (سریع، ~۱ دقیقه، بدون کامپایل محلی)
!pip -q install llama-cpp-python==0.3.34 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
!pip -q install fastapi uvicorn huggingface_hub --upgrade
import llama_cpp; print('✅ نصب شد، نسخه llama-cpp-python:', llama_cpp.__version__)"""))

cells.append(code("""# ۴) دانلود مدل به /content (دیسک محلی Colab — بدون Drive، بدون محدودیت فضا)
import os
from huggingface_hub import hf_hub_download
MODEL_DIR = '/content/models'
os.makedirs(MODEL_DIR, exist_ok=True)
local_path = os.path.join(MODEL_DIR, MODEL_FILE)
if os.path.exists(local_path) and os.path.getsize(local_path) == EXPECTED_BYTES:
    print('✅ مدل کامل روی /content هست')
else:
    print('⏬ (دوباره)دانلود کامل مدل به /content ...')
    hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE, local_dir=MODEL_DIR, force_download=True)
    sz = os.path.getsize(local_path)
    print('سایز:', sz, '| انتظار:', EXPECTED_BYTES, '| تطبیق:', sz == EXPECTED_BYTES)
print('مسیر مدل:', local_path)"""))

cells.append(code("""# ۵) heartbeat — runtime را بیدار نگه می‌دارد (کمکی برای جلوگیری از idle-disconnect)
import threading, time, urllib.request
def _beat():
    while True:
        try: urllib.request.urlopen(f'http://localhost:{PORT}/health', timeout=10)
        except Exception: pass
        time.sleep(45)
threading.Thread(target=_beat, daemon=True).start()
print('✅ heartbeat فعال')"""))

# --- سلول سرور بزرگ (شامل HTML به‌صورت base64) ---
server_src = '''# ۶) راه‌اندازی رابط چت + موتور مدل + سرور + تونل عمومی
# ۶-۱) رابط چت را روی دیسک بنویس
import base64
CHAT_HTML_B64 = "''' + b64 + '''"
_html = base64.b64decode(CHAT_HTML_B64)
open("/content/chat.html", "wb").write(_html)
assert len(_html) > 5000, "chat.html decode/write failed"
print("✅ رابط چت نوشته شد", len(_html), "بایت")

# ۶-۲) بارگذاری مدل و ساخت سرور FastAPI
import threading, time, json, subprocess, re, urllib.request
from llama_cpp import Llama
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# بررسی صحت فایل GGUF (magic = b"GGUF") — اگه خراب/ناقص بود، خودکار دوباره دانلود کن
import os as _o
def _gguf_ok(p):
    if not (_o.path.exists(p) and _o.path.getsize(p) == EXPECTED_BYTES):
        return False
    try:
        with open(p, "rb") as _f:
            return _f.read(4) == b"GGUF"
    except Exception:
        return False
if not _gguf_ok(local_path):
    print("⚠️ فایل مدل ناقص/خراب است — دانلود مجدد به /content ...")
    from huggingface_hub import hf_hub_download as _dl
    _dl(repo_id=MODEL_REPO, filename=MODEL_FILE, local_dir=_o.path.dirname(local_path), force_download=True)
print("⏳ بارگذاری مدل روی GPU (چند دقیقه)...")
llm = Llama(model_path=local_path, n_gpu_layers=GPU_LAYERS, n_ctx=CONTEXT_SIZE, chat_format="chatml", verbose=False)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def _index():
    _p = "/content/chat.html"
    if _o.path.exists(_p):
        return FileResponse(_p, media_type="text/html", headers={"Cache-Control": "no-store"})
    return HTMLResponse("<html><body dir='rtl'><h3>⚠️ chat.html پیدا نشد — سلول ۶ را دوباره اجرا کن.</h3></body></html>", media_type="text/html")

@app.get("/health")
def _health(): return {"status": "ok"}

@app.get("/v1/models")
def _models(): return {"object": "list", "data": [{"id": MODEL_NAME, "object": "model"}]}

def _call_llm(messages, stream, **params):
    try:
        return llm.create_chat_completion(messages=messages, stream=stream, chat_template_kwargs={"enable_thinking": False}, **params)
    except TypeError:
        return llm.create_chat_completion(messages=messages, stream=stream, **params)

@app.post("/v1/chat/completions")
async def _chat(req: Request):
    body = await req.json()
    messages = body.get("messages", [])
    params = dict(max_tokens=int(body.get("max_tokens", 1024)),
                  temperature=float(body.get("temperature", 0.7)),
                  top_p=float(body.get("top_p", 0.95)))
    if body.get("stream"):
        def gen():
            try:
                for chunk in _call_llm(messages, stream=True, **params):
                    yield "data: " + json.dumps(chunk) + chr(10) + chr(10)
            except Exception as e:
                print("INFERENCE ERROR:", repr(e), flush=True)
                yield "data: " + json.dumps({"choices":[{"index":0,"delta":{"content":"[ERR " + str(e)[:300] + "]"}}]}) + chr(10) + chr(10)
            yield "data: [DONE]" + chr(10) + chr(10)
        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
    try:
        return _call_llm(messages, stream=False, **params)
    except Exception as e:
        print("INFERENCE ERROR:", repr(e), flush=True)
        return {"error": {"message": str(e)}}

# ۶-۲.۵) ابزارهای ایجنت (اجرا روی /content/workspace) — برای حالت ایجنتِ چت
import os as _os
AGENT_WS = "/content/workspace"
_os.makedirs(AGENT_WS, exist_ok=True)
def _ws_resolve(path):
    p = _os.path.realpath(_os.path.join(AGENT_WS, path))
    if not (p == AGENT_WS or p.startswith(AGENT_WS + "/")):
        raise PermissionError("outside workspace")
    return p
@app.post("/v1/tools/bash")
async def _t_bash(req: Request):
    cmd = (await req.json()).get("cmd", "")
    try:
        r = subprocess.run(cmd, shell=True, cwd=AGENT_WS, capture_output=True, text=True, timeout=600)
        out = (r.stdout or "") + ((chr(10) + r.stderr) if r.stderr else "")
        return {"result": out.strip()[:12000] + ((chr(10) + "[exit " + str(r.returncode) + "]") if r.returncode else "")}
    except subprocess.TimeoutExpired:
        return {"result": "[timeout 600s]"}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]"}
@app.post("/v1/tools/read_file")
async def _t_read(req: Request):
    try:
        p = _ws_resolve((await req.json()).get("path", ""))
        return {"result": open(p, encoding="utf-8", errors="replace").read()[:12000]}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]"}
@app.post("/v1/tools/write_file")
async def _t_write(req: Request):
    try:
        b = await req.json(); p = _ws_resolve(b.get("path", ""))
        _os.makedirs(_os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(b.get("content", ""))
        return {"result": "[written] " + b.get("path", "")}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]"}
@app.post("/v1/tools/edit_file")
async def _t_edit(req: Request):
    try:
        b = await req.json(); p = _ws_resolve(b.get("path", ""))
        txt = open(p, encoding="utf-8").read(); old = b.get("old_text", ""); new = b.get("new_text", "")
        if old not in txt: return {"result": "[error: old_text not found]"}
        open(p, "w", encoding="utf-8").write(txt.replace(old, new, 1))
        return {"result": "[edited] " + b.get("path", "")}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]"}
@app.post("/v1/tools/list_dir")
async def _t_list(req: Request):
    try:
        b = await req.json(); p = _ws_resolve(b.get("path", ".")); rows = []
        for root, dirs, files in _os.walk(p):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
            rel = _os.path.relpath(root, AGENT_WS)
            for f in files: rows.append(_os.path.join(rel, f) if rel != "." else f)
            if not b.get("recursive"): dirs[:] = []
        return {"result": chr(10).join(sorted(rows)[:300]) or "[empty]"}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]"}
@app.get("/v1/workspace")
async def _ws_info(): return {"workspace": AGENT_WS}

@app.post("/v1/upload")
async def _upload(req: Request):
    try:
        b = await req.json()
        fn = "".join(ch for ch in _o.path.basename(b.get("filename", "upload.bin")) if ch.isalnum() or ch in "._-")
        dest = _ws_resolve(fn)
        _os.makedirs(_o.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh: fh.write(base64.b64decode(b.get("content", "")))
        return {"result": "[uploaded] " + fn, "path": dest}
    except Exception as e:
        return {"result": "[error: " + str(e) + "]", "path": ""}

# ۶-۳) سرور را در پس‌زمینه بالا بیاور
cfg = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="warning")
srv = uvicorn.Server(cfg)
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try:
        urllib.request.urlopen(f"http://localhost:{PORT}/health", timeout=3); break
    except Exception:
        time.sleep(1)

# ۶-۴) نصب cloudflared و ساخت تونل عمومی (رایگان، بدون اکانت)
subprocess.run(["wget", "-q", "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64", "-O", "/usr/local/bin/cloudflared"])
subprocess.run(["chmod", "+x", "/usr/local/bin/cloudflared"])
cf = subprocess.Popen(["cloudflared", "tunnel", "--url", f"http://localhost:{PORT}"],
                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
TUNNEL_URL = None
def _rd():
    global TUNNEL_URL
    for line in cf.stdout:
        m = re.search(r"https://[a-z0-9-]+\\.trycloudflare\\.com", line)
        if m: TUNNEL_URL = m.group(0); break
threading.Thread(target=_rd, daemon=True).start()
for _ in range(90):
    if TUNNEL_URL: break
    time.sleep(1)

print("\\n" + "=" * 58)
if TUNNEL_URL:
    print("✅ آماده! این آدرس را در مرورگر باز کن:")
    print("   ", TUNNEL_URL)
    print("=" * 58)
    print("در صفحه‌ی چت: ⚙️ تنظیمات -> نام مدل را این بگذار:", MODEL_NAME)
    print("(آدرس API همان آدرس + /v1 است.)")
else:
    print("❌ تونل ساخته نشد. cloudflared را دستی بررسی کن.")'''
cells.append(code(server_src))

cells.append(md("""## 📖 روش استفاده و ترفندهای پایداری

### مراحل
1. سلول آخر یک **آدرس اینترنتی** چاپ می‌کند (چیزی شبیه `https://...trycloudflare.com`).
2. آن را در مرورگر باز کن → رابط چت باز می‌شود.
3. دکمه‌ی ⚙️ تنظیمات را بزن: **نام مدل** را `qwen3-14b-abliterated` بگذار و **آدرس API** را همان آدرس به‌علاوه‌ی `/v1` وارد کن.
4. گفتگو را شروع کن. ✅

### اگه Colab قطع/ریست شد (طبیعی است)
- آدرس تونل عوض می‌شود. **ولی تاریخچه‌ی گفتگو در مرورگرت سر جایش است.**
- فقط سلول آخر را دوباره Run کن، آدرس جدید را بگیر، در مرورگر باز کن و همان گفتگو را ادامه بده.

### جلوگیری از idle-disconnect (اختیاری)
این کد را در **Console مرورگر** (دکمه‌ی F12) صفحه‌ی Colab بچسبان تا تب بیهوده قطع نشود:
```js
function ClickConnect(){
  document.querySelector("colab-connect-button")?.click?.() ||
  document.querySelector("colab-toolbar-button")?.click?.();
  console.log("keep-alive " + new Date().toLocaleTimeString());
}
setInterval(ClickConnect, 60000);
```
*(این فقط idle-disconnect را کم می‌کند؛ محدودیت ۱۲ ساعت رایگان را از بین نمی‌برد.)*

### ذخیره‌ی پشتیبان
در صفحه‌ی چت، دکمه‌ی **⬆️ خروجی** همه‌ی گفتگوها را به‌صورت فایل JSON ذخیره می‌کند.

---
**یادآوری:** یک مدل ۱۴B روی T4 برای چت آزاد و کارهای سبک عالی است، ولی برای کار سنگین/ایجنت واقعی، DeepSeek API ارزون‌تر و قوی‌تر است."""))

cells.append(code("""# (اختیاری) توقف سرور و تونل
try:
    cf.terminate(); srv.should_exit = True
    print("متوقف شد.")
except Exception as e:
    print(e)"""))

nb = {
    "nbformat": 4, "nbformat_minor": 5,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "T4", "toc_visible": True},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"}
    },
    "cells": cells
}

with open('/home/user/colab_setup.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("OK colab_setup.ipynb built, cells:", len(cells))
