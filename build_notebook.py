import json

def code(src):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}

def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}

cells = []

cells.append(md("""# Colab + Ollama = Qwen3-32B abliterated (بدون کامپایل!)

Ollama = نصب فوری، قالب بومی + thinking درست، بدون کامپایل.
مدل: Qwen3-32B abliterated (uncensored).

از بالا به پایين هر سلول Shift+Enter."""))

cells.append(code(
"!nvidia-smi || echo 'GPU not found'"
))

cells.append(code(
"!curl -fsSL https://ollama.com/install.sh | sh\n"
"!pip -q install fastapi uvicorn httpx\n"
"print('Ollama installed')\n"
"import subprocess; print(subprocess.run(['ollama','--version'],capture_output=True,text=True).stdout.strip())"
))

cells.append(code(
"import subprocess, os, time\n"
"os.environ['OLLAMA_HOST'] = '127.0.0.1:11434'\n"
"proc = subprocess.Popen(['ollama', 'serve'], stdout=open('/content/ollama.log','w'), stderr=subprocess.STDOUT)\n"
"time.sleep(4)\n"
"OLLAMA_MODEL = 'hf.co/mradermacher/Qwen3-32B-abliterated-GGUF:Q4_K_M'\n"
"print('Pulling model (~20GB)...')\n"
"subprocess.run(['ollama', 'pull', OLLAMA_MODEL])\n"
"print('Model ready:', OLLAMA_MODEL)"
))

# cell 4: proxy server + tunnel (downloads chat.html from repo)
srv = (
"# 4) Chat UI + proxy + tunnel\n"
"import subprocess, os, json, threading, time, re, urllib.request\n"
"import httpx\n"
"from fastapi import FastAPI, Request\n"
"from fastapi.responses import FileResponse, StreamingResponse\n"
"from fastapi.middleware.cors import CORSMiddleware\n"
"import uvicorn\n"
"\n"
"# Download chat.html from repo\n"
"subprocess.run(['wget', '-q', 'https://raw.githubusercontent.com/minam67889-bit/llm-uncensored-toolkit/main/chat.html', '-O', '/content/chat.html'])\n"
"print('chat.html:', os.path.getsize('/content/chat.html'), 'bytes')\n"
"\n"
"OLLAMA = 'http://127.0.0.1:11434'\n"
"app = FastAPI()\n"
"app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])\n"
"\n"
"@app.get('/')\n"
"async def _index():\n"
"    return FileResponse('/content/chat.html', media_type='text/html', headers={'Cache-Control':'no-store'})\n"
"\n"
"@app.get('/health')\n"
"async def _health():\n"
"    return {'status': 'ok'}\n"
"\n"
"@app.get('/v1/models')\n"
"async def _models():\n"
"    async with httpx.AsyncClient(timeout=10) as c:\n"
"        r = await c.get(OLLAMA + '/v1/models')\n"
"    return r.json()\n"
"\n"
"@app.post('/v1/chat/completions')\n"
"async def _chat(req: Request):\n"
"    body = await req.body()\n"
"    async def gen():\n"
"        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0)) as c:\n"
"            async with c.stream('POST', OLLAMA + '/v1/chat/completions', content=body, headers={'content-type':'application/json'}) as r:\n"
"                async for chunk in r.aiter_raw():\n"
"                    yield chunk\n"
"    return StreamingResponse(gen(), media_type='text/event-stream', headers={'Cache-Control':'no-store'})\n"
"\n"
"AWS = '/content/workspace'; os.makedirs(AWS, exist_ok=True)\n"
"def _res(path):\n"
"    p = os.path.realpath(os.path.join(AWS, path))\n"
"    if not (p == AWS or p.startswith(AWS + os.sep)): raise PermissionError('outside')\n"
"    return p\n"
"@app.post('/v1/tools/bash')\n"
"async def _bash(req: Request):\n"
"    cmd = (await req.json()).get('cmd', '')\n"
"    try:\n"
"        r = subprocess.run(cmd, shell=True, cwd=AWS, capture_output=True, text=True, timeout=600)\n"
"        out = (r.stdout or '') + ((chr(10) + r.stderr) if r.stderr else '')\n"
"        return {'result': out.strip()[:12000] + ((chr(10) + '[exit ' + str(r.returncode) + ']') if r.returncode else '')}\n"
"    except subprocess.TimeoutExpired: return {'result': '[timeout]'}\n"
"    except Exception as e: return {'result': '[error: ' + str(e) + ']'}\n"
"@app.post('/v1/tools/read_file')\n"
"async def _rd(req):\n"
"    try: return {'result': open(_res((await req.json()).get('path','')), encoding='utf-8', errors='replace').read()[:12000]}\n"
"    except Exception as e: return {'result': '[error: ' + str(e) + ']'}\n"
"@app.post('/v1/tools/write_file')\n"
"async def _wf(req):\n"
"    try:\n"
"        b = await req.json(); p = _res(b.get('path','')); os.makedirs(os.path.dirname(p), exist_ok=True)\n"
"        open(p,'w',encoding='utf-8').write(b.get('content','')); return {'result':'[written] '+b.get('path','')}\n"
"    except Exception as e: return {'result': '[error: ' + str(e) + ']'}\n"
"@app.post('/v1/tools/list_dir')\n"
"async def _ls(req):\n"
"    try:\n"
"        b = await req.json(); root = _res(b.get('path','.')); rows = []\n"
"        for r2, ds, fs in os.walk(root):\n"
"            ds[:] = [d for d in ds if d not in ('.git','node_modules','__pycache__')]\n"
"            rel = os.path.relpath(r2, AWS)\n"
"            for f in fs: rows.append(os.path.join(rel,f) if rel != '.' else f)\n"
"            if not b.get('recursive'): ds[:] = []\n"
"        return {'result': chr(10).join(sorted(rows)[:300]) or '[empty]'}\n"
"    except Exception as e: return {'result': '[error: ' + str(e) + ']'}\n"
"@app.post('/v1/upload')\n"
"async def _up(req):\n"
"    import base64\n"
"    try:\n"
"        b = await req.json(); fn = ''.join(ch for ch in os.path.basename(b.get('filename','u.bin')) if ch.isalnum() or ch in '._-')\n"
"        p = _res(fn); os.makedirs(os.path.dirname(p), exist_ok=True); open(p,'wb').write(base64.b64decode(b.get('content','')))\n"
"        return {'result':'[uploaded] '+fn, 'path':p}\n"
"    except Exception as e: return {'result':'[error: '+str(e)+']', 'path':''}\n"
"\n"
"cfg = uvicorn.Config(app, host='0.0.0.0', port=8000, log_level='warning')\n"
"srv = uvicorn.Server(cfg)\n"
"threading.Thread(target=srv.run, daemon=True).start()\n"
"for _ in range(60):\n"
"    try:\n"
"        urllib.request.urlopen('http://localhost:8000/health', timeout=3); break\n"
"    except Exception:\n"
"        time.sleep(1)\n"
"subprocess.run(['wget','-q','https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64','-O','/usr/local/bin/cloudflared'])\n"
"subprocess.run(['chmod','+x','/usr/local/bin/cloudflared'])\n"
"cf = subprocess.Popen(['cloudflared','tunnel','--url','http://localhost:8000'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)\n"
"TUNNEL_URL = None\n"
"def _rdtunnel():\n"
"    global TUNNEL_URL\n"
"    for line in cf.stdout:\n"
"        m = re.search(r'https://[a-z0-9-]+\\.trycloudflare\\.com', line)\n"
"        if m: TUNNEL_URL = m.group(0); break\n"
"threading.Thread(target=_rdtunnel, daemon=True).start()\n"
"for _ in range(90):\n"
"    if TUNNEL_URL: break\n"
"    time.sleep(1)\n"
"print('=' * 52)\n"
"print('READY! Open this URL:')\n"
"print('   ', TUNNEL_URL or '(tunnel failed)')\n"
"print('=' * 52)\n"
)
cells.append(code(srv))

cells.append(md("""## استفاده
1) آدرس trycloudflare رو باز کن.
2) مدل خودکار انتخاب میشه. چت کن (thinking روشنه).

روی T4 کند (~1-3 tok/s) ولی باکیفیت (قالب درست + thinking)."""))

cells.append(code(
"try:\n"
"    cf.terminate(); srv.should_exit = True; proc.terminate()\n"
"    print('stopped')\n"
"except Exception as e:\n"
"    print(e)"
))

nb = {"nbformat":4,"nbformat_minor":5,"metadata":{"accelerator":"GPU","colab":{"provenance":[],"gpuType":"T4","toc_visible":True},"kernelspec":{"name":"python3","display_name":"Python 3"},"language_info":{"name":"python"}},"cells":cells}
with open('/home/user/colab_setup.ipynb','w',encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print('OK cells:', len(cells))
