# 🚀 راه‌اندازی روی RunPod (مدل ۳۲B — قدرتمند + uncensored)

این مسیر مدل **Qwen3-32B abliterated** رو روی یه GPU اجاره‌ای اجرا می‌کنه: همون چت + ایجنت، ولی با کیفیتی **خیلی بالاتر از ۱۴B** (با کیفیتِ ۷۲B) و کاملاً بدون سانسور.

> هزینه: **RTX 3090 (24GB) ≈ ۰.۲۲ دلار/ساعت** — فقط حین استفاده. یه نشستِ چند ساعته = چند ده‌سنت.

## مراحل

### ۱) اکانت RunPod
- برو به **runpod.io** → ثبت‌نام → **Settings → Billing** → یه کارت اعتباری + حداقل **۱۰ دلار** شارژ کن. (برای شروع کافیه.)

### ۲) ساخت پاد (Pod)
- **Deploy → GPU Pods** → GPU رو **RTX 3090 (24GB)** انتخاب کن (ارزون‌ترین).
- Template: **PyTorch** (یا هر ایمیج CUDA، مثلاً `runpod/pytorch:2.x-cuda`).
- **Disk: حداقل ۵۰ گیگ** (برای مدل ۲۰ گیگابی).
- **Expose HTTP Ports**: `8000` رو اضافه کن (مهم — برای دسترسی به چت).
- **Deploy On-Demand** بزن (اگه ارزون‌تر خواستی Spot، ولی ممکنه قطع کنه).

### ۳) اجرای اسکریپت
- توی داشبورد، روی پاد کلیک کن → **Connect → Start Web Terminal** (یا SSH).
- این دو دستور رو بزن:
```bash
wget https://raw.githubusercontent.com/minam67889-bit/llm-uncensored-toolkit/main/runpod_server.py
python3 runpod_server.py
```
- چند دقیقه صبر کن (نصب + دانلود مدل بار اول). وقتی گفت `✅ آماده!` یعنی سرور بالاست.

### ۴) باز کردن چت
- توی داشبورد پاد، بخش **Connect → HTTP Service [Port 8000]** رو باز کن.
- یا آدرس رو دستی بساز: `https://<POD_ID>-8000.proxy.runpod.net`
- صفحه‌ی چت باز میشه — **خودکار وصل میشه** (هیچ تنظیمی لازم نیست).
- استریم زنده، بدون thinking، حالت ایجنت (bash/فایل)، آپلود zip — همه فعال.

## نکته‌ها
- **/workspace ماندگاره**: اگه پاد رو stop کنی و دوباره start، مدل سرجاش می‌مونه (دوباره دانلود نمیشه).
- وقتی کارت تموم شد، پاد رو **Stop** کن تا هزینه نگیره. (پاد رو Delete نکن اگه می‌خوای مدل بمونه.)
- برای مدلِ حتی قوی‌تر (۷۰B): GPU رو **A40 (48GB) یا A6000** بگیر و تو `runpod_server.py` مدل رو عوض کن.

## عوض‌کردن مدل
بالای `runpod_server.py`، `MODEL_REPO` و `MODEL_FILE` رو تغییر بده. مدل‌های پیشنهادی (GGUF):
- `mradermacher/Qwen3-32B-abliterated-GGUF` → `Qwen3-32B-abliterated.Q4_K_M.gguf` (پیش‌فرض)
- کدر تخصصی: `bartowski/Qwen2.5-Coder-32B-Instruct-GGUF` → `Qwen2.5-Coder-32B-Instruct-Q4_K_M.gguf`
