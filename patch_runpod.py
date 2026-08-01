s = open('build_runpod.py', encoding='utf-8').read()

reps = []
reps.append(('MODEL_REPO  = "mradermacher/Qwen3-32B-abliterated-GGUF"',
             'MODEL_REPO  = "mradermacher/Llama-3.3-70B-Instruct-abliterated-GGUF"'))
reps.append(('MODEL_FILE  = "Qwen3-32B-abliterated.Q4_K_M.gguf"',
             'MODEL_FILE  = "Llama-3.3-70B-Instruct-abliterated.Q4_K_M.gguf"'))
reps.append(('MODEL_NAME  = "qwen3-32b-abliterated"',
             'MODEL_NAME  = "llama3.3-70b-abliterated"'))
reps.append(('chat_format="chatml"', 'chat_format="llama-3"'))
reps.append(('os.path.getsize(local_path) > 18e9', 'os.path.getsize(local_path) > 35e9'))
reps.append((
'def _call(messages, stream, **p):\n    try:\n        return llm.create_chat_completion(messages=messages, stream=stream, chat_template_kwargs={"enable_thinking": False}, **p)\n    except TypeError:\n        return llm.create_chat_completion(messages=messages, stream=stream, **p)',
'def _call(messages, stream, **p):\n    return llm.create_chat_completion(messages=messages, stream=stream, **p)'))
reps.append((
'    msgs = [dict(m) for m in body.get("messages", [])]\n    for m in reversed(msgs):\n        if m.get("role") == "user" and "<tool_result" not in m.get("content", ""):\n            m["content"] = m.get("content", "").rstrip() + " /no_think"\n            break\n    p = dict(',
'    msgs = body.get("messages", [])\n    p = dict('))

for a, b in reps:
    if a not in s:
        print("NOT FOUND:", a[:55])
    else:
        s = s.replace(a, b, 1)
        print("patched:", a[:45])

open('build_runpod.py', 'w', encoding='utf-8').write(s)
