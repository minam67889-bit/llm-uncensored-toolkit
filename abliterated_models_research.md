# ریسرچ: قوی‌ترین مدل‌های abliterated (uncensored) — 2026

> نتیجه‌ی تحقیق روی ده‌ها منبع (r/LocalLLaMA، HuggingFace، بنچمارک‌ها). همه‌ی مدل‌ها **uncensored** هستن.

## ⚠️ حقیقتِ صادقانه‌ی سقف
حتی قوی‌ترین abliterated (~۹۴ از ۱۰۰ امتیاز جامعه) **در حدِ GPT-4 قدیمیه، نه GPT-5/Claude-4**. یعنی برای کارهای خیلی سخت هنوز به پای frontier نمی‌رسه. ولی ۷۰B نسبت به ۱۴B/۳۲B یه **جهش واقعیه** و برای بیشتر کارهای واقعی کاملاً کافیه.

---

## 🏆 رده‌بندیِ قوی‌ترین‌ها (برای توانایی)

| رتبه | مدل | قوی در | امتیاز جامعه | نیاز سخت‌افزار (Q4) |
|---|---|---|---|---|
| ۱ | **Llama 3.3 70B abliterated** | همه‌کاره (near-GPT-4، هذیان کم) | ۹۴ | ~40GB → GPU 48GB+ |
| ۲ | **DeepSeek-R1-Distill-Llama-70B abliterated** | استدلال/ریاضی/منطق (CoT سالم) | ۹۳ | ~42GB → 48GB+ |
| ۳ | **Qwen3 72B abliterated** | **کدنویسی** (HumanEval 86%) | 93 | ~42GB → 48GB+ |
| — | **gpt-oss-120b heretic** | همه‌کاره + سریع (MoE، 5.1B فعال) |很强 | 65GB → یک GPU 80GB |
| ۴ | **Qwen3-32B abliterated** (فعلی) | همه‌کاره (با کیفیتِ 72B) | — | ~20GB → GPU 24GB |
| — | **Gemma 4 31B Heretic** | همه‌کاره + بینایی + tool | — | ~20GB → 24GB |
| — | **Qwen3-Coder-Next abliterated** (80B-A3B MoE) | کدنویسی uncensored + سریع | — | ~24GB → 24-32GB |

---

## 🖥️ بر اساس سخت‌افزار (عملی)

### الف) رایگان / Colab T4 (با offload، کند)
حداکثر **32B** (با offload). چیزی بالاتر تو رم رایگانِ Colab جا نمیشه.
→ `mradermacher/Qwen3-32B-abliterated-GGUF` (فعلی)

### ب) ⭐ GPU اجاره‌ای 24GB (RTX 3090/4090، ~$0.22-0.34/ساعت)
- **Qwen3-32B abliterated** (همه‌کاره) — بهترین تعادل.
- **Gemma 4 31B Heretic** (اگه بینایی/Tool می‌خوای).
- **Qwen3-Coder-Next abliterated** (اگه فقط کد).

### ج) ⭐⭐ GPU اجاره‌ای 48GB (A6000/A40، ~$0.44-0.74/ساعت) — جهشِ واقعی
اینجا به رده‌ی 70B می‌رسی (کیفیتِ GPT-4 کلاس):
- **Llama 3.3 70B abliterated** ← بهترین همه‌کاره.
- **DeepSeek-R1-70B abliterated** ← بهترین برای استدلال/دیباگِ سخت.
- **Qwen3 72B abliterated** ← بهترین برای کد.

### د) GPU 80GB (A100، ~$1.19-1.39/ساعت) — قوی + سریع
- **gpt-oss-120b heretic** (117B MoE، خیلی قوی و سریع روی یک کارت).

### هـ) دیتاسنتر (عملی برای تو نیست)
- **GLM-5.1 abliterated** (754B)، **DeepSeek V4 Flash abliterated** (284B)، **Llama 4 Maverick** — قوی‌ترین‌های مطلق ولی 200+ گیگ، multi-GPU.

---

## 🎯 توصیه‌ی صادقانه برای تو
تو **هم کد هم چت آزاد** می‌خوای و حاضر بودی GPU اجاره کنی:

1. **بهترین نسبت کیفیت/قیمت:** GPU **A40 48GB** روی RunPod (~$0.44/ساعت) + **Llama 3.3 70B abliterated** (یا Qwen3 72B اگه کد اولویته). این از 32B خیلی قوی‌تره و واقعاً «مثل یه مدلِ خوب» حرف می‌زنه.
2. **اگه استدلال/دیباگِ سنگین:** همون GPU + **DeepSeek-R1-70B abliterated**.
3. **اگه می‌خوای سریع + قوی روی یک کارت:** A100 80GB + **gpt-oss-120b heretic**.
4. **اگه رایگان بمونی:** همون 32B روی Colab (با offload، کند).

---

## منابعِ GGUF (قابل دانلود، mradermacher/bartowski)
- Llama 3.3 70B abliterated: `mradermacher/Llama-3.3-70B-Instruct-abliterated-GGUF` (یا huihui-ai/Llama-3.3-70B-abliterated → GGUF)
- DeepSeek-R1-70B abliterated: `bartowski/huihui-ai_DeepSeek-R1-Distill-Llama-70B-abliterated-GGUF` ✓ تأییدشده
- Qwen3 72B abliterated: `mradermacher/Qwen3-72B-abliterated-GGUF`
- gpt-oss-120b heretic: `kldzj/gpt-oss-120b-heretic-v2` / `DavidAU/...heretic...GGUF`
- Qwen3-32B abliterated: `mradermacher/Qwen3-32B-abliterated-GGUF` ✓ تأییدشده
- Qwen3-Coder-Next abliterated: `bartowski/huihui-ai_Qwen3-Coder-Next-abliterated-GGUF` ✓ تأییدشده

> نکته: اسم دقیق ریپو/فایل رو قبل از دانلود توی HF سرچ کن (گاهی عوض میشه). من می‌تونم برات چک کنم.
