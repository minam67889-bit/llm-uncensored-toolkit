# Colab → LLM بدون محدودیت (نسخه پایدار) — راهنمای سریع

سه فایل:
- **`colab_setup.ipynb`** ← نوت‌بوک اصلی. این رو روی Google Colab آپلود/اجرا کن.
- **`chat.html`** ← رابط چت (توی نوت‌بوک خودکار سرو می‌شود؛ این فایل فقط نسخه‌ی مستقل برای مرجع/استفاده‌ی جداگانه‌ست).
- **`hf-coding-models.md`** ← لیست مدل‌های uncensored روی Hugging Face.

## مراحل (۳ دقیقه بعد از اجرای سلول‌ها)
1. برو به **colab.research.google.com** → **File > Upload notebook** → `colab_setup.ipynb`.
2. **Runtime > Change runtime type > GPU (T4)**.
3. از بالا به پایین هر سلول را **Shift+Enter**.
   - سلول ۳ (نصب): بار اول چند دقیقه طول می‌کشد (کامپایل llama.cpp با CUDA).
   - سلول ۴: اکانت گوگل درایو را اجازه می‌دهد (برای کش مدل).
   - سلول ۶: مدل لود می‌شود، سپس یک **آدرس this...trycloudflare.com** چاپ می‌کند.
4. آن آدرس را در مرورگر باز کن → دکمه‌ی ⚙️ → نام مدل: `qwen3-14b-abliterated`، آدرس API: همان آدرس + `/v1`.
5. چت کن. ✅

## پایداری: چه کار می‌کند، چه کار نه
| مشکل | راه‌حل در این پکیج |
|---|---|
| idle-disconnect (~۹۰د) | heartbeat + اسکریپت کنسول (در نوت‌بوک) |
| خراب شدن کانتکس پس از ریست | ✅ تاریخچه در **مرورگر** است، نه در Colab → حفظ می‌شود |
| دانلود مجدد مدل پس از ریست | ✅ کش روی **Google Drive** → بدون دانلود |
| حداکثر سشن ۱۲ ساعت رایگان | ❌ دست گوگل است. فقط سلول ۶ را دوباره Run کن (آدرس عوض می‌شود، گفتگو می‌ماند) |

## پس از قطعی Colab
- آدرس تونل عوض می‌شود → سلول ۶ را دوباره Run کن → آدرس جدید را در مرورگر باز کن → همان گفتگو را ادامه بده.
- پشتیبان: در صفحه‌ی چت دکمه‌ی **⬆️ خروجی**.

## عوض کردن مدل
در سلول ۲، `MODEL_REPO` و `MODEL_FILE` را عوض کن. مدل‌های پیشنهادی uncensored (با پسوند GGUF) را در `hf-coding-models.md` ببین.

## نکته‌ی صادقانه
این راه‌حل برای **چت آزاد/کاملاً بدون محدودیت + کار سبک** عالی است. برای کار **سنگین/ایجنت** واقعی، یک مدل ۱۴B روی T4 نمی‌رسد؛ آن موقع **DeepSeek API** (~۱–۵ دلار/ماه) ارزون‌تر و قوی‌تر است.

---

# 🧑‍💻 ایجنت کدنویس (مثل سیستم Arena): `coding_agent.py`

یه ایجنت کدنویس واقعی با دسترسی **bash + فایل** که مثل همین چت، گام‌به‌گام کار می‌کند: فایل می‌خواند، ویرایش می‌کند، دستور اجرا می‌کند (unzip, build, test, git...) و تسک را حل می‌کند.

به هر بک‌اند OpenAI-compatible وصل می‌شود → هم مدل قوی، هم مدل محلی رایگان.

## نصب
```bash
pip install openai
```

## حالت ۱ — قوی و ارزون (DeepSeek) — پیشنهادی برای کدنویسی جدی
```bash
export LLM_API_KEY="sk-deepseek-key"     # از platform.deepseek.com
python coding_agent.py                    # حالت تعاملی
python coding_agent.py "یک اسکریپت پایتون بنویس که فایل‌های csv رو ادغام کنه"
```
مدل پیش‌فرض `deepseek-chat` است. برای مسأله‌ی خیلی سخت: `export LLM_MODEL=deepseek-reasoner`.

## حالت ۲ — رایگان + uncensored (تونل Colab)
اول `colab_setup.ipynb` را اجرا کن تا آدرس تونل را بگیری، بعد:
```bash
export LLM_BASE_URL="https://xxxx-xxxx.trycloudflare.com/v1"
export LLM_MODEL="qwen3-14b-abliterated"
export LLM_API_KEY="sk-none"
python coding_agent.py
```

## تنظیمات کدنویسی (همون «بهترین حالت» که خواستی)
داخل `coding_agent.py` بخش CONFIG:
- `TEMPERATURE = 0.2` → خروجی باثبات برای کد
- `MAX_TOKENS = 8192` → جای کافی برای فایل‌های بزرگ
- `MAX_STEPS = 40` → عمق حل مسأله
- `APPROVE_BASH = True` → قبل از هر دستور ازت می‌پرسد (امنیت). با `--auto` خاموش می‌شود.
- `AGENT_WORKDIR` → پوشه‌ی پروژه‌ات (مثلاً `export AGENT_WORKDIR=/home/user/myproject`)

## ابزارها
`bash` · `read_file` · `write_file` · `edit_file` (ویرایش هدفمند/fuzzy) · `list_dir`

## امنیت
- فایل‌ops فقط داخل `WORKDIR` مجاز است (sandbox).
- bash در `WORKDIR` اجرا می‌شود و با `APPROVE_BASH` هر دستور تایید می‌خواهد.
- برای اجرای خودکار بدون پرسش: `python coding_agent.py --auto` (با احتیاط).
