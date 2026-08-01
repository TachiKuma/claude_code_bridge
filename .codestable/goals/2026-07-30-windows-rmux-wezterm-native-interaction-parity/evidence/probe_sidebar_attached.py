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
    o=(cp.stdout or b"").decode("utf-8","replace") if not devnull else ""
    e=(cp.stderr or b"").decode("utf-8","replace") if not devnull else ""
    return cp.returncode,o,e
def sgr(col,row,press=True):
    seq=f"\x1b[<0;{col};{row}{'M' if press else 'm'}".encode("ascii")
    return [f"{b:02x}" for b in seq]
def loadp(p):
    return json.loads(io.open(p,encoding="utf-8").read()) if p.exists() else None
ns=f"ccbsa{uuid.uuid4().hex[:8]}"; sess="s1"; base=[RMUX,"-L",ns]
proj=Path(tempfile.mkdtemp(prefix="ccb-sa-")); probe=Path(tempfile.mkdtemp(prefix="ccb-sap-"))/"p.json"
stub=proj/"ccb-stub.cmd"; stub.write_text("@echo stub %*\r\n",encoding="ascii")
env=dict(os.environ); env["CCB_AGENT_SIDEBAR_MOUSE_PROBE"]=str(probe); env["CCB_SIDEBAR_CCB_BIN"]=str(stub)
cmd=f'"{SIDEBAR}" --ccbd-socket "\\.\pipe\bogus-{ns}" --project-root "{proj}" --pane-window main'
ev={"probe_path":str(probe),"steps":[]}; attach=None
try:
    run([*base,"new-session","-d","-s",sess,"-x","80","-y","24",cmd],devnull=True,env=env)
    for _ in range(30):
        time.sleep(0.25)
        if probe.exists(): break
    ev["probe_created"]=probe.exists()
    # 后台 -CC attach 泵输入
    attach=subprocess.Popen([*base,"-CC","attach-session","-t",sess],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    time.sleep(1.2); ev["attach_alive"]=(attach.poll() is None)
    tp=f"{sess}:0.0"
    # 1) plain 'c' -> settings
    run([*base,"send-keys","-t",tp,"c"]); time.sleep(0.8); ev["after_c"]=loadp(probe)
    # 2) SGR mouse mid via -H
    run([*base,"send-keys","-t",tp,"-H",*sgr(40,5)]); run([*base,"send-keys","-t",tp,"-H",*sgr(40,5,False)])
    time.sleep(0.8); ev["after_mid_mouse"]=loadp(probe)
    # 3) SGR mouse at settings col (width80 -> crossterm col 76 -> SGR col 77). 扫 74..79 提升命中率
    for c in (77,76,78,75,79):
        run([*base,"send-keys","-t",tp,"-H",*sgr(c,1)]); run([*base,"send-keys","-t",tp,"-H",*sgr(c,1,False)]); time.sleep(0.3)
    time.sleep(0.6); ev["after_settings_sweep"]=loadp(probe)
    rc,o,e=run([*base,"capture-pane","-t",tp,"-p"]); ev["cap_tail"]=o[-200:]
finally:
    if attach and attach.poll() is None: attach.kill()
    run([*base,"kill-server"],devnull=True)
print(json.dumps(ev,ensure_ascii=False,indent=2))
