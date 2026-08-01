import json

def code(src):
    return {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":src.splitlines(keepends=True)}
def md(src):
    return {"cell_type":"markdown","metadata":{},"source":src.splitlines(keepends=True)}

cells=[]
cells.append(md("# Qwen3-14B abliterated — chat ساده و سریع (GPU)\nllama-cpp-python + chatml + thinking ON. بدون agent/tools (سادگی = اعتماد).\nRun all cells."))

cells.append(code("!nvidia-smi || echo 'no GPU'"))

cells.append(code(
"!pip -q install llama-cpp-python==0.3.34 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124\n"
"!pip -q install fastapi uvicorn huggingface_hub\n"
"import llama_cpp; print('version:', llama_cpp.__version__)"
))

cells.append(code(
"import os\n"
"from huggingface_hub import hf_hub_download\n"
"d='/content/models'; os.makedirs(d, exist_ok=True)\n"
"f='huihui-ai_Qwen3-14B-abliterated-Q4_K_M.gguf'\n"
"lp=os.path.join(d,f)\n"
"if os.path.exists(lp) and os.path.getsize(lp)==9001749568:\n"
"    print('cached')\n"
"else:\n"
"    print('downloading ~9GB...')\n"
"    hf_hub_download(repo_id='bartowski/huihui-ai_Qwen3-14B-abliterated-GGUF', filename=f, local_dir=d)\n"
"print('ready:', lp)"
))

S=(
"# Server (simple chat only, no tools)\n"
"import subprocess, os, json, threading, time, urllib.request\n"
"from llama_cpp import Llama\n"
"from fastapi import FastAPI, Request\n"
"from fastapi.responses import FileResponse, StreamingResponse\n"
"from fastapi.middleware.cors import CORSMiddleware\n"
"import uvicorn\n"
"\n"
"subprocess.run(['wget','-q','https://raw.githubusercontent.com/minam67889-bit/llm-uncensored-toolkit/main/chat.html','-O','/content/chat.html'])\n"
"print('loading model on GPU...')\n"
"llm=Llama(model_path=lp, n_gpu_layers=-1, n_ctx=8192, chat_format='chatml', verbose=False)\n"
"print('model ready')\n"
"\n"
"app=FastAPI()\n"
"app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])\n"
"\n"
"@app.get('/')\n"
"async def _i(): return FileResponse('/content/chat.html', media_type='text/html', headers={'Cache-Control':'no-store'})\n"
"@app.get('/health')\n"
"def _h(): return {'status':'ok'}\n"
"@app.get('/v1/models')\n"
"def _m(): return {'object':'list','data':[{'id':'qwen3-14b-abliterated','object':'model'}]}\n"
"\n"
"@app.post('/v1/chat/completions')\n"
"async def _c(req: Request):\n"
"    body=await req.json()\n"
"    msgs=body.get('messages',[])\n"
"    p=dict(max_tokens=min(int(body.get('max_tokens',4096)),8000), temperature=float(body.get('temperature',0.3)), top_p=0.95)\n"
"    if body.get('stream'):\n"
"        def gen():\n"
"            try:\n"
"                for ch in llm.create_chat_completion(messages=msgs, stream=True, **p):\n"
"                    yield 'data: '+json.dumps(ch)+chr(10)+chr(10)\n"
"            except Exception as e:\n"
"                print('ERR:',repr(e),flush=True)\n"
"                yield 'data: '+json.dumps({'choices':[{'index':0,'delta':{'content':'[ERR '+str(e)[:200]+']'}}]})+chr(10)+chr(10)\n"
"            yield 'data: [DONE]'+chr(10)+chr(10)\n"
"        return StreamingResponse(gen(), media_type='text/event-stream', headers={'Cache-Control':'no-store'})\n"
"    try: return llm.create_chat_completion(messages=msgs, **p)\n"
"    except Exception as e: return {'error':{'message':str(e)}}\n"
"\n"
"cfg=uvicorn.Config(app, host='0.0.0.0', port=8000, log_level='warning')\n"
"uvS=uvicorn.Server(cfg)\n"
"threading.Thread(target=uvS.run, daemon=True).start()\n"
"for _ in range(60):\n"
"    try: urllib.request.urlopen('http://localhost:8000/health',timeout=3); break\n"
"    except Exception: time.sleep(1)\n"
"\n"
"subprocess.run(['wget','-q','https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64','-O','/usr/local/bin/cloudflared'])\n"
"subprocess.run(['chmod','+x','/usr/local/bin/cloudflared'])\n"
"cf=subprocess.Popen(['cloudflared','tunnel','--url','http://localhost:8000'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)\n"
"TU=None\n"
"def _rd():\n"
"    global TU\n"
"    for line in cf.stdout:\n"
"        if 'trycloudflare.com' in line:\n"
"            for w in line.split():\n"
"                if w.startswith('https://') and 'trycloudflare' in w: TU=w.strip(); return\n"
"threading.Thread(target=_rd,daemon=True).start()\n"
"for _ in range(90):\n"
"    if TU: break\n"
"    time.sleep(1)\n"
"print('='*52)\n"
"print('READY:',TU or '(failed)')\n"
"print('='*52)\n"
)
cells.append(code(S))

cells.append(md("Open the URL. Chat is auto-connected. Thinking ON (like HF). 14B fully on T4 GPU = fast.\nNo agent/bash — just clean chat. If Colab disconnects: re-run last cell, new URL."))

cells.append(code(
"try:\n"
"    cf.terminate(); uvS.should_exit=True\n"
"except: pass\n"
))

nb={"nbformat":4,"nbformat_minor":5,"metadata":{"accelerator":"GPU","colab":{"provenance":[],"gpuType":"T4","toc_visible":True},"kernelspec":{"name":"python3","display_name":"Python 3"},"language_info":{"name":"python"}},"cells":cells}
open('/home/user/colab_setup.ipynb','w',encoding='utf-8').write(json.dumps(nb,ensure_ascii=False,indent=1))
print('cells:',len(cells))
