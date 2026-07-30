#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mini-Arena — یک ایجنت کدنویس با دسترسی واقعی به bash و فایل‌ها
================================================================
مثل همین سیستمی که الان باهاش حرف می‌زنی: می‌تونه فایل بخونه/بنویسه/ویرایش کنه،
دستور bash اجرا کنه (build, run, grep, unzip, pip install, git ...) و گام‌به‌گام مسأله حل کنه.

به هر بک‌اند سازگار با OpenAI وصل میشه:
  • قوی‌ترین برای ایجنت کد  : OpenRouter → Kimi K2.7 Code  (پولی/ارزون)
  • رایگان + قوی برای کد    : OpenRouter → Qwen3-Coder:free  یا GLM:free
  • رایگان + uncensored     : تونل Colab      (از colab_setup.ipynb)

نصب:   pip install openai
اجرا:  python coding_agent.py            (حالت تعاملی)
       python coding_agent.py "یک اسکریپت..."  (یک‌بار)
"""

import os, sys, re, json, argparse, subprocess, textwrap
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    sys.exit("ابتدا نصب کن:  pip install openai")

# ====================== تنظیمات (بخش مهم) ======================
# پیش‌فرض: OpenRouter (با یک کلید رایگان به ده‌ها مدل دسترسی داری)
BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
MODEL    = os.environ.get("LLM_MODEL",    "qwen/qwen3-coder:free")  # رایگان+قوی برای کد
API_KEY  = os.environ.get("LLM_API_KEY",  "")                       # از openrouter.ai/keys (رایگان)
WORKDIR  = Path(os.environ.get("AGENT_WORKDIR", ".")).resolve()     # پوشه‌ی کاری (sandbox فایل)

MAX_STEPS   = 40        # حداکثر گام ابزار در هر تسک
TEMPERATURE = 0.2       # برای کد پایین = خروجی باثبات‌تر
MAX_TOKENS  = 8192
APPROVE_BASH = True     # قبل از اجرای هر دستور bash تایید بگیر (امنیت)
BASH_TIMEOUT = 600      # ثانیه

# مدل‌های پیشنهادی روی OpenRouter (همگی متن‌باز/کم‌محدودیت):
#   رایگان:   qwen/qwen3-coder:free  |  z-ai/glm-4.5-air:free  |  nvidia/nemotron-3-ultra-550b-a55b:free
#   پولی/قوی: moonshotai/kimi-k2.7-code (بهترین ایجنت)  |  qwen/qwen3.6-plus  |  z-ai/glm-5.2
# مدل رایگان محلی (uncensored کامل) — از colab_setup.ipynb:
#   export LLM_BASE_URL="https://xxxx.trycloudflare.com/v1"
#   export LLM_MODEL="qwen3-14b-abliterated"
#   export LLM_API_KEY="sk-none"
# ===============================================================

WORKDIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = f"""You are an elite autonomous software engineer (an AI coding agent) operating directly in the user's real workspace.

WORKSPACE (root for all relative paths): {WORKDIR}
Today's date: see the user's timezone context.

You solve tasks by acting step-by-step with REAL tools. Each turn you EITHER ask/report in normal text OR call tools.

## TOOL-CALL FORMAT
Emit one or more tool calls. Each MUST be exactly:
<tool_call>
{{"name": "bash", "arguments": {{"cmd": "ls -la"}}}}
</tool_call>
You may put them inside or outside a ```block``` — only the <tool_call>...</tool_call> markers matter.

## TOOLS
- bash {{"cmd"}} : run a shell command. For building, running, testing, grep, unzip, pip install, git, etc. Output is returned to you.
- read_file {{"path"}} : read a file's full content.
- write_file {{"path","content"}} : create or overwrite a file.
- edit_file {{"path","old_text","new_text"}} : replace the FIRST occurrence of old_text with new_text (fuzzy on whitespace).
- list_dir {{"path","recursive"?}} : list directory contents.

## RULES
1. EXPLORE FIRST: list_dir / read_file / bash before editing anything. Understand the repo.
2. Make small, verifiable changes. After edits, compile/run/test when possible.
3. Prefer edit_file (surgical) over write_file (whole-file rewrite).
4. You may call MULTIPLE tools in one turn; you receive all results.
5. When fully done, give a concise final summary in the user's language (Persian) with NO tool_call.
6. Be efficient — don't over-explain. Show key decisions and results only.

All relative paths are resolved under {WORKDIR}. You cannot write outside it."""


# --------------------------- رنگ ---------------------------
def c(t, code):
    return f"\033[{code}m{t}\033[0m" if sys.stdout.isatty() else t
def G(t): return c(t, "32")   # سبز
def Y(t): return c(t, "33")   # زرد
def C(t): return c(t, "36")   # فیروزه‌ای
def R(t): return c(t, "31")   # قرمز
def D(t): return c(t, "90")   # خاکستری


# --------------------------- ابزارها ---------------------------
def _resolve(path: str) -> Path:
    p = (WORKDIR / path).resolve()
    try:
        p.relative_to(WORKDIR)
    except ValueError:
        raise PermissionError(f"مسیر خارج از workspace مجاز نیست: {path}")
    return p

def t_bash(args):
    cmd = args.get("cmd", "")
    if not isinstance(cmd, str) or not cmd.strip():
        return "خطا: cmd خالی است"
    if APPROVE_BASH:
        print(Y("  ? اجرا بشه؟") + f" {cmd}   [Y/n] ", end="", flush=True)
        ans = sys.stdin.readline().strip().lower()
        if ans not in ("", "y", "yes"):
            return "[skip] کاربر اجرا را رد کرد."
    try:
        r = subprocess.run(cmd, shell=True, cwd=WORKDIR, capture_output=True,
                           text=True, timeout=BASH_TIMEOUT)
        out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
        out = out.strip()
        if len(out) > 12000:
            out = out[:12000] + f"\n... [بریده شد، {len(out)-12000} کاراکتر بیشتر]"
        return out + (f"\n[exit {r.returncode}]" if r.returncode else "") or "[خروجی خالی]"
    except subprocess.TimeoutExpired:
        return f"[timeout بعد از {BASH_TIMEOUT}s]"
    except Exception as e:
        return f"[خطا: {e}]"

def t_read_file(args):
    try:
        p = _resolve(args.get("path", ""))
        txt = p.read_text(encoding="utf-8", errors="replace")
        return txt if len(txt) <= 12000 else txt[:12000] + f"\n... [+{len(txt)-12000} کاراکتر]"
    except Exception as e:
        return f"[خطا: {e}]"

def t_write_file(args):
    try:
        p = _resolve(args.get("path", ""))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(args.get("content", ""), encoding="utf-8")
        return f"[نوشته شد] {args.get('path')} ({p.stat().st_size} بایت)"
    except Exception as e:
        return f"[خطا: {e}]"

def t_edit_file(args):
    try:
        p = _resolve(args.get("path", ""))
        txt = p.read_text(encoding="utf-8")
        old, new = args.get("old_text", ""), args.get("new_text", "")
        # تطبیق نسبت‌ به فاصله‌ها
        norm = lambda s: re.sub(r"\s+", " ", s).strip()
        idx, best = -1, None
        lines = txt.splitlines(keepends=True)
        joined = "".join(lines)
        # اول تطبیق دقیق
        if old in txt:
            txt = txt.replace(old, new, 1)
        else:
            # تطبیق fuzzy مبتنی‌بر خط
            nold = norm(old)
            hay = ""
            start = None
            for i, ln in enumerate(lines):
                if start is None:
                    hay = ln
                    if norm(hay) == nold:
                        start = i
                    elif nold in norm(hay):
                        hay_accum = ln
                        # امتحان چند خط
                        j = i
                        while j+1 < len(lines) and norm(hay_accum) != nold and len(hay_accum) < len(old)*4:
                            j += 1
                            hay_accum += lines[j]
                            if norm(hay_accum) == nold:
                                txt = txt.replace(hay_accum, new, 1)
                                start = -2
                                break
                        if start == -2:
                            break
                else:
                    break
            if start != -2:
                return "[خطا: old_text پیدا نشد (نه دقیق نه fuzzy)]"
        p.write_text(txt, encoding="utf-8")
        return f"[ویرایش شد] {args.get('path')}"
    except Exception as e:
        return f"[خطا: {e}]"

def t_list_dir(args):
    try:
        p = _resolve(args.get("path", "."))
        recursive = args.get("recursive", False)
        if recursive:
            rows = []
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", ".venv")]
                rel = os.path.relpath(root, WORKDIR)
                for f in files:
                    rows.append(os.path.join(rel, f) if rel != "." else f)
            return "\n".join(sorted(rows)[:500]) or "[خالی]"
        else:
            return "\n".join(sorted(x.name + ("/" if x.is_dir() else "") for x in p.iterdir())) or "[خالی]"
    except Exception as e:
        return f"[خطا: {e}]"

TOOLS = {
    "bash": t_bash, "read_file": t_read_file, "write_file": t_write_file,
    "edit_file": t_edit_file, "list_dir": t_list_dir,
}


# --------------------------- پارس tool-call ---------------------------
def parse_tool_calls(text):
    calls = []
    for m in re.finditer(r"<tool_call>\s*(.*?)\s*</tool_call>", text, re.DOTALL):
        raw = m.group(1).strip().strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
        try:
            obj = json.loads(raw)
        except Exception:
            mm = re.search(r"\{.*\}", raw, re.DOTALL)
            try:
                obj = json.loads(mm.group(0)) if mm else {}
            except Exception:
                continue
        name = obj.get("name")
        args = obj.get("arguments") or obj.get("args") or obj.get("parameters") or {}
        if name in TOOLS:
            calls.append((name, args))
    # پشتیبان: فرمت مارک‌داون ```json با name/arguments
    if not calls:
        for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL):
            try:
                obj = json.loads(m.group(1))
                name = obj.get("name")
                args = obj.get("arguments") or obj.get("args") or {}
                if name in TOOLS:
                    calls.append((name, args))
            except Exception:
                pass
    return calls


# --------------------------- حلقه‌ی ایجنت ---------------------------
def run_task(client, messages, task):
    messages.append({"role": "user", "content": task})
    for step in range(1, MAX_STEPS + 1):
        print(D(f"\n── گام {step} ──────────────────────────────"))
        try:
            resp = client.chat.completions.create(
                model=MODEL, messages=messages,
                temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
            )
        except Exception as e:
            print(R(f"خطای API: {e}"))
            return
        content = resp.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": content})

        # متن عادی مدل را چاپ کن (بدون بلوک‌های tool_call)
        shown = re.sub(r"<tool_call>.*?</tool_call>", "", content, flags=re.DOTALL).strip()
        # و متن قبل از اولین tool_call
        first = re.split(r"<tool_call>", content, maxsplit=1)[0].strip()
        to_show = first if first else shown
        if to_show:
            print(C("🤖 ") + to_show)

        calls = parse_tool_calls(content)
        if not calls:
            print(G("\n✅ انجام شد.") if "خطا" not in to_show else "")
            return

        for name, args in calls:
            print(Y(f"\n🔧 {name}") + f"  {json.dumps(args, ensure_ascii=False)[:160]}")
            result = TOOLS[name](args)
            preview = result if len(result) <= 2000 else result[:2000] + "\n..."
            for line in preview.splitlines():
                print(D("   ") + line)
            messages.append({"role": "user", "content": f'<tool_result tool="{name}">\n{result}\n</tool_result>'})
    print(R("به حداکثر گام رسید."))


# --------------------------- main ---------------------------
def main():
    global APPROVE_BASH, WORKDIR
    ap = argparse.ArgumentParser(description="mini-Arena: ایجنت کدنویس با bash")
    ap.add_argument("task", nargs="*", help="تسک (اگه خالی، حالت تعاملی)")
    ap.add_argument("--auto", action="store_true", help="بدون تایید دستورات bash (با احتیاط)")
    ap.add_argument("--workdir", default=str(WORKDIR))
    args = ap.parse_args()

    if args.workdir:
        WORKDIR = Path(args.workdir).resolve()
        WORKDIR.mkdir(parents=True, exist_ok=True)
    if args.auto:
        APPROVE_BASH = False

    if not API_KEY:
        sys.exit(R("LLM_API_KEY ست نیست.") + "\nمثال:\n  export LLM_API_KEY='sk-...'   (یا sk-none برای تونل Colab)")

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    print(G("mini-Arena") + f" | مدل: {C(MODEL)} | پوشه: {D(str(WORKDIR))}")
    print(D("  — برای خروج:  exit | خالی = ادامه روی همون context —\n"))

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    one_shot = " ".join(args.task).strip()
    if one_shot:
        run_task(client, messages, one_shot)
        return

    while True:
        try:
            line = input(C("you» ") if sys.stdin.isatty() else "").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nخداحافظ.")
            break
        if not line:
            continue
        if line.lower() in ("exit", "quit", "/exit", "/q"):
            break
        run_task(client, messages, line)


if __name__ == "__main__":
    main()
