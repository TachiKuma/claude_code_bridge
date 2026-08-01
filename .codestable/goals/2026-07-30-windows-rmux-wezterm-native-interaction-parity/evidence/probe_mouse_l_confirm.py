import io,json,os,shutil,subprocess,tempfile,time,uuid
from pathlib import Path
REPO=Path("D:/Python/GitHub/claude_code_bridge"); RMUX=shutil.which("rmux") or "rmux"
SIDEBAR=REPO/"bin"/"ccb-agent-sidebar.exe"
def run(a,devnull=False,timeout=8.0,env=None):
    kw={"check":False,"timeout":timeout}
    if devnull: kw["stdout"]=subprocess.DEVNULL; kw["stderr"]=subprocess.DEVNULL
    else: kw["stdout"]=subprocess.PIPE; kw["stderr"]=subprocess.PIPE
    if env is not None: kw["env"]=env
    try: cp=subprocess.run(a,**kw)
    except subprocess.TimeoutExpired: return 124,"",""
    return cp.returncode,(cp.stdout or b"").decode("utf-8","replace") if not devnull else "",(cp.stderr or b"").decode("utf-8","replace") if not devnull else ""
def loadp(p): return json.loads(io.open(p,encoding="utf-8").read()) if p.exists() else None
ns=f"ccbml{uuid.uuid4().hex[:8]}"; sess="s1"; base=[RMUX,"-L",ns]
proj=Path(tempfile.mkdtemp(prefix="ccb-ml-")); probe=Path(tempfile.mkdtemp(prefix="ccb-mlp-"))/"p.json"
stub=proj/"ccb-stub.cmd"; stub.write_text("@echo stub %*\r\n",encoding="ascii")
env=dict(os.environ); env["CCB_AGENT_SIDEBAR_MOUSE_PROBE"]=str(probe); env["CCB_SIDEBAR_CCB_BIN"]=str(stub)
cmd=f'"{SIDEBAR}" --ccbd-socket "\\.\pipe\bogus-{ns}" --project-root "{proj}" --pane-window main'
ev={}; attach=None
try:
    run([*base,"new-session","-d","-s",sess,"-x","80","-y","24",cmd],devnull=True,env=env)
    for _ in range(30):
        time.sleep(0.25)
        if probe.exists(): break
    attach=subprocess.Popen([*base,"-CC","attach-session","-t",sess],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    time.sleep(1.2); ev["attach_alive"]=(attach.poll() is None)
    tp=f"{sess}:0.0"
    # -l 原子发送完整 SGR press+release
    run([*base,"send-keys","-t",tp,"-l","\x1b[<0;40;5M"]); run([*base,"send-keys","-t",tp,"-l","\x1b[<0;40;5m"])
    time.sleep(0.8); ev["after_l_mouse"]=loadp(probe)
    # 对照：键盘 j（移动）再 c（settings）确认键盘链路仍通
    run([*base,"send-keys","-t",tp,"c"]); time.sleep(0.6); ev["after_c"]=loadp(probe)
finally:
    if attach and attach.poll() is None: attach.kill()
    run([*base,"kill-server"],devnull=True)
print(json.dumps(ev,ensure_ascii=False,indent=2))
