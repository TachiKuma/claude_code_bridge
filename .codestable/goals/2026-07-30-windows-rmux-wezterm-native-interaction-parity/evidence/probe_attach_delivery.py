import io,json,os,shutil,subprocess,tempfile,time,uuid
from pathlib import Path
RMUX=shutil.which("rmux") or "rmux"
def run(a,devnull=False,timeout=8.0):
    kw={"check":False,"timeout":timeout}
    if devnull: kw["stdout"]=subprocess.DEVNULL; kw["stderr"]=subprocess.DEVNULL
    else: kw["stdout"]=subprocess.PIPE; kw["stderr"]=subprocess.PIPE
    try: cp=subprocess.run(a,**kw)
    except subprocess.TimeoutExpired: return 124,"",""
    o=(cp.stdout or b"").decode("utf-8","replace") if not devnull else ""
    e=(cp.stderr or b"").decode("utf-8","replace") if not devnull else ""
    return cp.returncode,o,e
ns=f"ccbatt{uuid.uuid4().hex[:8]}"; sess="s1"; base=[RMUX,"-L",ns]
ev={}
attach=None
try:
    run([*base,"new-session","-d","-s",sess,"-x","80","-y","24"],devnull=True); time.sleep(1.0)
    # 后台 control-mode attach（-CC），不需要真实终端
    attach=subprocess.Popen([*base,"-CC","attach-session","-t",sess],
                            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    time.sleep(1.0)
    ev["attach_alive_after_1s"]=(attach.poll() is None)
    rc,o,e=run([*base,"send-keys","-t",f"{sess}:0.0","echo CCB_ATT_MARKER_999","Enter"]); ev["send"]=(rc,e[-150:])
    time.sleep(1.2)
    rc,o,e=run([*base,"capture-pane","-t",f"{sess}:0.0","-p"]); ev["capture_has_marker"]="CCB_ATT_MARKER_999" in o; ev["cap_tail"]=o[-300:]
    # 若 attach 已退出，记录 stderr
    if attach.poll() is not None:
        try: _,ae=attach.communicate(timeout=2); ev["attach_stderr"]=(ae or b"").decode("utf-8","replace")[-200:]
        except Exception: pass
finally:
    if attach and attach.poll() is None:
        attach.kill()
    run([*base,"kill-server"],devnull=True)
print(json.dumps(ev,ensure_ascii=False,indent=2))
