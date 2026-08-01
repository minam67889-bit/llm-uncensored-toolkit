import json

def code(src):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}

def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}

cells = []

cells.append(md("""# 🚀 Colab → Qwen3-32B abliterated با llama-server (رسمی)

این نسخه به‌جای سرورِ دست‌ساز، از **llama-server رسمی llama.cpp** استفاده می‌کنه:
- قالبِ بومیِ Qwen3 درست اعمال می‌شه (`--jinja`) → خروجی تمیز.
- **thinking روشنه** (مثل HuggingFace) → همون کیفیتِ خوب.
- رابط چتِ آماده‌ی خود llama-server.

مدل: **Qwen3-32B abliterated (uncensored)**.

---

**اجرا:** از بالا به پایین هر سلول را Shift+Enter."""))

cells.append(code("""# ۱) بررسی GPU
!nvidia-smi || echo '❌ GPU پیدا نشد. Runtime > Change runtime type > GPU.'"""))

cells.append(code("""# ۲) تنظیمات
MODEL_REPO = "mradermacher/Qwen3-32B-abliterated-GGUF"
MODEL_FILE = "Qwen3-32B-abliterated.Q4_K_M.gguf"
CONTEXT_SIZE = 8192
PORT = 8000
EXPECTED_BYTES = 19762149728   # ~19.8GB
# (روی T4 با offload اجرا می‌شود — کند ولی باکیفیت. روی GPU بزرگ‌تر سریع‌تر.)"""))

cells.append(code("""# ۳) ساخت llama.cpp (موتور رسمی) — یک‌بار ~۳-۵ دقیقه
!apt-get -y -qq install cmake >/dev/null 2>&1
![ -d /content/llama.cpp ] || git clone --depth 1 https://github.com/ggml-org/llama.cpp /content/llama.cpp
print("⏳ ساخت llama.cpp (فقط برای sm_75/89 = T4/L4، پس سریع‌تر)...")
!cmake -S /content/llama.cpp -B /content/llama.cpp/build -DGGML_CUDA=ON -DGGML_CUDA_ARCHITECTURES="75;89" -DLLAMA_CURL=OFF > /tmp/cm.log 2>&1 && echo "cmake ok"
!cmake --build /content/llama.cpp/build --config Release --target llama-server -j > /tmp/bd.log 2>&1 && echo "✅ llama-server ساخته شد"
!ls -la /content/llama.cpp/build/bin/llama-server 2>/dev/null || (echo "❌ build ناموفق — /tmp/bd.log:"; tail -20 /tmp/bd.log)"""))

cells.append(code("""# ۴) دانلود مدل به /content
import os
from huggingface_hub import hf_hub_download
MODEL_DIR = '/content/models'
os.makedirs(MODEL_DIR, exist_ok=True)
local_path = os.path.join(MODEL_DIR, MODEL_FILE)
if os.path.exists(local_path) and os.path.getsize(local_path) == EXPECTED_BYTES:
    print('✅ مدل کامل هست')
else:
    print('⏬ دانلود مدل (~20GB)...')
    hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE, local_dir=MODEL_DIR)
print('مسیر:', local_path)"""))

cells.append(code("""# ۵) اجرای llama-server (قالب بومی + thinking) + تونل عمومی
import subprocess, re, time, threading, urllib.request
try:
    _vram = int(subprocess.run(["nvidia-smi","--query-gpu=memory.total","--format=csv,noheader,nounits"], capture_output=True, text=True).stdout.strip().split()[0])
except Exception:
    _vram = 16000
_ngl = -1 if _vram >= 22000 else max(10, int((_vram - 4500) / 315))
print("VRAM ~" + str(_vram) + "MB -> -ngl " + str(_ngl) + " (offload)")
srv = subprocess.Popen(["/content/llama.cpp/build/bin/llama-server",
    "-m", local_path, "--host", "0.0.0.0", "--port", str(PORT),
    "-ngl", str(_ngl), "-c", str(CONTEXT_SIZE), "--jinja"],
    stdout=open("/content/llama-server.log", "w"), stderr=subprocess.STDOUT)
print("⏳ صبر تا سرور بالا بیاد (لود مدل)...")
_ok = False
for _ in range(150):
    try:
        urllib.request.urlopen("http://localhost:" + str(PORT) + "/health", timeout=3); _ok = True; break
    except Exception:
        time.sleep(2)
if not _ok:
    print("❌ سرور بالا نیومد. لاگ:"); print(open("/content/llama-server.log").read()[-3000:])
subprocess.run(["wget", "-q", "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64", "-O", "/usr/local/bin/cloudflared"])
subprocess.run(["chmod", "+x", "/usr/local/bin/cloudflared"])
cf = subprocess.Popen(["cloudflared", "tunnel", "--url", "http://localhost:" + str(PORT)],
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
print("=" * 52)
print("✅ آماده! آدرس رو در مرورگر باز کن (رابط چتِ llama-server):")
print("   ", TUNNEL_URL or "(تونل ساخته نشد)")
print("=" * 52)"""))

cells.append(md("""## استفاده
۱) آدرسِ `trycloudflare` رو باز کن → رابط چتِ llama-server.
۲) مدل از قبل انتخاب شده. مستقیم چت کن.

**نکته:** روی T4 رایگان، 32B با offload اجرا می‌شه → کند (~۱-۳ توکن/ثانیه) ولی خروجی باکیفیت (مثل HuggingFace، چون از قالب بومی + thinking استفاده می‌کنه).

اگه Colab قطع شد: سلول ۵ رو دوباره اجرا کن (آدرس عوض می‌شه)."""))

cells.append(code("""# (اختیاری) توقف
try:
    cf.terminate(); srv.terminate()
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
print("OK colab_setup.ipynb rebuilt with llama-server, cells:", len(cells))
