import json, os, shutil, subprocess, tempfile, time, uuid
from pathlib import Path
RMUX=shutil.which("rmux") or "rmux"
def run(a,devnull=False,timeout=8.0,env=None):
    kw={"check":False,"timeout":timeout}
    if devnull: kw["stdout"]=subprocess.DEVNULL; kw["stderr"]=subprocess.DEVNULL
    else: kw["stdout"]=subprocess.PIPE; kw["stderr"]=subprocess.PIPE
    if env is not None: kw["env"]=env
    try: cp=subprocess.run(a,**kw)
    except subprocess.TimeoutExpired: return 124,"",""
    o=(cp.stdout or b"").decode("utf-8","replace") if not devnull else ""
    e=(cp.stderr or b"").decode("utf-8","replace") if not devnull else ""
    return cp.returncode,o,e
ns=f"ccbctl{uuid.uuid4().hex[:8]}"; sess="s1"; base=[RMUX,"-L",ns]
ev={}
try:
    # 普通 shell pane（默认 shell）
    rc,o,e=run([*base,"new-session","-d","-s",sess,"-x","80","-y","24"],devnull=True); ev["new-session"]=rc
    time.sleep(1.0)
    rc,o,e=run([*base,"send-keys","-t",sess,"echo CCB_CTL_MARKER_123","Enter"]); ev["send-echo"]=(rc,e[-150:])
    time.sleep(1.0)
    rc,o,e=run([*base,"capture-pane","-t",sess,"-p"]); ev["capture_has_marker"]="CCB_CTL_MARKER_123" in o; ev["cap_tail"]=o[-400:]
finally:
    run([*base,"kill-server"],devnull=True)
print(json.dumps(ev,ensure_ascii=False,indent=2))
