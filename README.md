# 🦙 LLM بدون محدودیت + ایجنت کدنویس (Toolkit)

دو ابزار در یک ریپو:

1. **`colab_setup.ipynb`** — روی Google Colab (GPU رایگان T4) یک مدل **uncensored** بالا می‌آورد + تونل عمومی + رابط چت. طراحی‌شده برای **حداکثر پایداری** (تاریخچه گفتگو در مرورگر، کش مدل روی Drive).
2. **`coding_agent.py`** — یک ایجنت کدنویس واقعی با دسترسی **bash + فایل** (مثل سیستم‌های agentic): فایل می‌خواند/ویرایش می‌کند، دستور اجرا می‌کند (unzip, build, test, git...) و گام‌به‌گام تسک را حل می‌کند.

> مدل پیش‌فرض: **OpenRouter** (با یک کلید رایگان به ده‌ها مدل دسترسی داری) — نه DeepSeek.

---

## 📦 فایل‌ها
| فایل | کاربرد |
|---|---|
| `colab_setup.ipynb` | نوت‌بوک Colab (مدل + چت + تونل) |
| `chat.html` | رابط چت (توی نوت‌بوک سرو می‌شود؛ مستقل هم قابل استفاده) |
| `coding_agent.py` | ایجنت کدنویس با bash |
| `hf-coding-models.md` | لیست مدل‌های uncensored روی Hugging Face |
| `build_notebook.py` | اسکریپت بازسازی نوت‌بوک (مرجع) |

---

## ▶️ راه‌انداز سریع

### الف) چت روی Colab (رایگان، کاملاً بدون محدودیت)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/minam67889-bit/llm-uncensored-toolkit/blob/main/colab_setup.ipynb)

1. روی بَج بالا بزن (یا در Colab: **File > Open notebook > GitHub** و آدرس این ریپو).
2. **Runtime > Change runtime type > T4 GPU**.
3. سلول‌ها را به ترتیب **Shift+Enter**.
4. سلول آخر یک آدرس `...trycloudflare.com` می‌دهد → در مرورگر باز کن → چت.

### ب) ایجنت کدنویس (قوی‌ترین برای کد)
```bash
pip install openai
export LLM_API_KEY="sk-or-..."          # از openrouter.ai/keys (رایگان)
cd /path/to/your/project
python coding_agent.py "این پروژه رو تحلیل کن و باگ تابع X رو درست کن"
```

### مدل‌های پیشنهادی (OpenRouter) — همگی متن‌باز و کم‌محدودیت
| مدل | کیفیت | هزینه | تنظیم |
|---|---|---|---|
| **Qwen3-Coder** | SWE ~۷۸٪ | **رایگان** | `qwen/qwen3-coder:free` |
| **GLM-4.5 Air** | قوی | **رایگان** | `z-ai/glm-4.5-air:free` |
| **Kimi K2.7 Code** | بهترین ایجنت ~۸۰٪ | ارزون | `moonshotai/kimi-k2.7-code` |
| **Qwen3.6 Plus** | ~۷۹٪ | متوسط | `qwen/qwen3.6-plus` |

برای عوض کردن مدل: `export LLM_MODEL="moonshotai/kimi-k2.7-code"`.

### ایجنت با مدل محلی Colab (رایگان + uncensored کامل)
اول نوت‌بوک را اجرا کن و آدرس تونل را بگیر، بعد:
```bash
export LLM_BASE_URL="https://xxxx.trycloudflare.com/v1"
export LLM_MODEL="qwen3-14b-abliterated"
export LLM_API_KEY="sk-none"
python coding_agent.py
```

---

## 🛡️ پایداری و امنیت
- **تاریخچه چت در مرورگر** ذخیره می‌شود → قطعی Colab به آن دست نمی‌زند.
- **مدل روی Google Drive کش** می‌شود → ریست سریع.
- ایجنت: فایل‌ops فقط داخل پوشه‌ی پروژه (sandbox)؛ قبل از هر `bash` تایید می‌گیرد (`--auto` برای غیرفعال کردن).
- کلید API را در متغیر محیطی بگذار، نه در کد.

## ⚠️ نکته‌ی صادقانه
مدل ۱۴B روی T4 برای چت آزاد و کار سبک عالی است. برای کدنویسی **سنگین/ایجنت** جدی، مدل‌های ابری (Kimi K2.7 Code، Qwen3-Coder) از مدل محلی قوی‌ترند و تقریباً رایگان‌اند.

## لایسنس
MIT — آزاد برای استفاده‌ی تجاری.
