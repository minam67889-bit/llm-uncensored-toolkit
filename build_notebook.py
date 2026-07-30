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
- مدل روی **Google Drive کش می‌شود** → ریست سریع، بدون دانلود مجدد.
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
MODEL_FILE = "Qwen3-14B-abliterated-Q4_K_M.gguf"
MODEL_NAME = "qwen3-14b-abliterated"      # این نام را بعداً در صفحه‌ی چت وارد می‌کنی

CONTEXT_SIZE = 8192
GPU_LAYERS   = -1     # -1 = همه‌ی لایه‌ها روی GPU
PORT         = 8000

# --- مدل‌های جایگزین (فقط MODEL_REPO و MODEL_FILE را عوض کن) ---
# کیفیت بالاتر (سنگین‌تر): MODEL_REPO = bartowski/huihui-ai_Qwen3-14B-abliterated-GGUF | MODEL_FILE = Qwen3-14B-abliterated-Q5_K_M.gguf
# مدل دیگر ۱۴B:            MODEL_REPO = bartowski/mlabonne_Qwen3-14B-abliterated-GGUF | MODEL_FILE = Qwen3-14B-abliterated-Q4_K_M.gguf
# برای مدل دلخواه: در huggingface.co عبارت abliterated GGUF را جستجو کن."""))

cells.append(code("""# ۳) نصب پیش‌نیازها. بار اول llama-cpp-python با پشتیبانی CUDA کامپایل می‌شود (چند دقیقه).
%env CMAKE_ARGS=-DGGML_CUDA=on
%env FORCE_CMAKE=1
!pip -q install "llama-cpp-python" fastapi uvicorn huggingface_hub --upgrade
print('✅ نصب انجام شد')"""))

cells.append(code("""# ۴) مونت Google Drive + دانلود/کش مدل
from google.colab import drive
drive.mount('/content/drive')

import os
from huggingface_hub import hf_hub_download

CACHE_DIR = '/content/drive/MyDrive/llm_models'
os.makedirs(CACHE_DIR, exist_ok=True)
local_path = os.path.join(CACHE_DIR, MODEL_FILE)

if os.path.exists(local_path):
    print('✅ مدل از کش Google Drive لود شد (سریع، بدون دانلود)')
else:
    print('⏬ اولین دانلود — بسته به سرعت چند دقیقه طول می‌کشد. بعدش برای همیشه کش می‌ماند.')
    hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE, local_dir=CACHE_DIR)
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
open("/content/chat.html", "wb").write(base64.b64decode(CHAT_HTML_B64))
print("✅ رابط چت نوشته شد")

# ۶-۲) بارگذاری مدل و ساخت سرور FastAPI
import threading, time, json, subprocess, re, urllib.request
from llama_cpp import Llama
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

print("⏳ بارگذاری مدل روی GPU (چند دقیقه)...")
llm = Llama(model_path=local_path, n_gpu_layers=GPU_LAYERS, n_ctx=CONTEXT_SIZE, verbose=False)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def _index(): return FileResponse("/content/chat.html")

@app.get("/health")
def _health(): return {"status": "ok"}

@app.get("/v1/models")
def _models(): return {"object": "list", "data": [{"id": MODEL_NAME, "object": "model"}]}

@app.post("/v1/chat/completions")
async def _chat(req: Request):
    body = await req.json()
    messages = body.get("messages", [])
    params = dict(max_tokens=int(body.get("max_tokens", 1024)),
                  temperature=float(body.get("temperature", 0.7)),
                  top_p=float(body.get("top_p", 0.95)))
    if body.get("stream"):
        def gen():
            for chunk in llm.create_chat_completion(messages=messages, stream=True, **params):
                yield "data: " + json.dumps(chunk) + "\\n\\n"
            yield "data: [DONE]\\n\\n"
        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
    return llm.create_chat_completion(messages=messages, **params)

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
