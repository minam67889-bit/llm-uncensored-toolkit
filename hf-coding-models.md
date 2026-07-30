# بهترین مدل‌های کدنویسی + ایجنت + کم‌محدودیت روی Hugging Face (2026)

> منبع: اطلاعات گردآوری‌شده از جولای ۲۰۲۶. لینک‌های دقیق هر مدل در انتها.

## کلید ماجرا: تکنیک «abliteration»
مدل‌های متن‌باز (Qwen, Llama, Gemma, Mistral) مثل ChatGPT/Claude به‌صورت پیش‌فرض محدودیت دارن. جامعه متن‌باز روشی به نام **abliteration** ساخته که «جهت امتناع» (refusal direction) مدل رو حذف می‌کنه **بدون کاهش چشمگیر توانایی**. نسخه‌هایی که در اسمشون کلماتی مثل `abliterated` / `heretic` / `uncensored` / `derestricted` دارن، همگی همین روش‌اند.

نتیجه: همون مدل قوی ولی دیگه از بحث دینی، +18، exploit و... امتناع نمی‌کنه.

---

## 🏆 پیشنهاد اول (ترکیب کدنویسی + ایجنت + بدون محدودیت)

**`huihui-ai/Huihui-Qwen3-Coder-Next-abliterated`**
- پایه‌اش **Qwen3-Coder** (یکی از قوی‌ترین کدرهای متن‌باز) + نسخه abliterated.
- از **tool calling** پشتیبانی می‌کنه ← برای کار ایجنت (تحلیل چند فایل، نوشتن فایل جدید، اجرای دستور) لازمه.
- این ترکیب نقطه عطفه: هم کدنویس درجه‌یک، هم ایجنت، هم بی‌محدودیت.

---

## سایر گزینه‌های محکم

| مدل | مناسب برای | نکته |
|---|---|---|
| **Dolphin 3.0 / DolphinCoder** (Eric Hartford) | همه‌کاره بی‌محدودیت | قدیمی‌ترین و معتبرترین uncensored؛ کد + reasoning + creative |
| **gpt-oss-20b abliterated** (DavidAU / huihui) | سبک، 16GB VRAM | نسخه سنبل‌شده‌ی OpenAI متن‌باز |
| **DeepSeek V4 Flash abliterated** | سخت‌افزار قوی | یکی از بهترین‌ها اگر GPU دیتاسنتری داری |
| **GLM-5.1** (zai-org) | ایجنت مهندسی نرم‌افزار بلندمدت | سنگین؛ به‌صورت API واقعی‌تر از local |

---

## انتخاب بر اساس سخت‌افزار (VRAM کارت گرافیک)

**8GB (لپ‌تاپ/کارت ارزون):**
- `huihui-ai/Huihui-Qwen3-8B-abliterated-v2`
- Dolphin 3.0 Llama 3.1 8B

**16GB (نقطه عادلانه):**
- Dolphin 3.0 Mistral 24B
- Gemma 4 26B-A4B Heretic

**24GB (RTX 3090/4090):**
- `huihui-ai/Huihui-Qwen3.6-27B-abliterated` ← پیک اصلی این کلاس
- Dolphin 3.0 Mistral 24B

**48GB+ (دو کارت / pro):**
- DeepSeek-R1-Distill-Llama 70B abliterated
- DeepSeek V4 Flash abliterated

---

## چطور اجرا کنی
- **Ollama** (ساده‌ترین): `ollama run <model-name>`
- **LM Studio** (رابط گرافیکی، مرور کاتالوگ HF)
- **vLLM / llama.cpp** (حرفه‌ای‌تر، با API سازگار با OpenAI)

تمام این‌ها **رایگان، open-weight و روی سیستم خودت** اجرا میشن ← هیچ‌چیز سرور نمی‌ره، هیچ فیلتری نیست.

---

## ⚠️ نکات مهم (صادقانه)

1. **تریدآف وجود داره:** abliteration خیلی سنگین می‌تونه مدل رو کمی ضعیف‌تر کنه (جامعه بهش میگه «lobotomized»). برای کدنویس بهتره نسخه‌ای با abliteration سبک‌تر انتخاب کنی. روش‌های **Derestricted / Heretic** معمولاً توانایی رو بهتر از نسخه‌های huihui حفظ می‌کنن.
2. **tool calling حساسه:** بعضی abliterationها قابلیت tool calling رو خراب می‌کنن. برای کار ایجنت حتماً مدلی بگیر که tool-calling support داره (مثل نسخه Qwen3-Coder-Next بالا).
3. **اول پایه رو امتحان کن:** خودِ Qwen3-Coder هم نسبت به Claude/GPT خیلی کمتر امتناع می‌کنه. اگر فقط گاهی رد می‌کنه، اول پایه‌اش رو تست کن، بعداً نسخه uncensored.
4. **هالوسینیشن:** بی‌محدودیت بودن = دقت بیشتر نیست. خروجی مهم رو همیشه چک کن.

---

## منابع و لینک‌ها
- راهنمای best uncensored by VRAM tier: https://insiderllm.com/guides/best-uncensored-local-llms/
- مدل Qwen3-Coder-Next-abliterated: https://huggingface.co/huihui-ai/Huihui-Qwen3-Coder-Next-abliterated
- مدل‌های Ollama تا جولای ۲۰۲۶: https://www.promptquorum.com/local-llms/top-open-source-models-ollama
- راهنمای پیدا/ارزیابی uncensoredها: https://docs.bswen.com/blog/2026-03-10-huggingface-uncensored-models-guide/
- مقایسه روش‌های abliteration (Reddit r/LocalLLaMA): https://www.reddit.com/r/LocalLLaMA/comments/1qsvgsh/some_uncensored_models/
- بهترین کدرهای متن‌باز ۲۰۲۶: https://huggingface.co/blog/daya-shankar/open-source-llms
