#!/usr/bin/env python3
"""
Generate a Colab bootstrap cell for JupyterLab over Cloudflare with stable token.

Key changes:
- Default Jupyter port 8888 (no forced 9999).
- Stable token: passed via --ServerApp.token and exported as JUPYTER_TOKEN env var.
- --clean option kills existing Jupyter processes before starting (prevents stray token).
- --auth-proxy optional: if enabled, backend runs on 8889, tiny proxy on 8888 injecting Authorization header.
- Without --auth-proxy token in URL should suffice (single server).
"""

import argparse, secrets, sys, json, pathlib
from string import Template

DEFAULT_REPO = "git@github.com:alfredsasko/llm_engineering.git"

CELL_TEMPLATE = Template(r"""# ===================== Colab Jupyter (Cloudflare tunnel, stable token) =====================
# Paste this cell into Colab and run.
# Startup goals:
#  - Stable token ($token) (will not change because only one server is launched).
#  - Single Jupyter instance on port 8888 (unless auth proxy used, then backend on 8889, proxy 8888).
#  - Copy one printed URL EXACTLY into VS Code (Command Palette -> Jupyter: Specify Jupyter Server).

COLAB_JUPYTER_TOKEN = "$token"
DISABLE_AUTH = $disable_auth
USE_AUTH_PROXY = $use_auth_proxy
PERFORM_CLEAN = $do_clean
REPOS = $repos_json
GITHUB_PRIVATE_KEY_B64 = $deploy_key_b64
OPTIONAL_ENV_FILE_CONTENT = $env_content_json

# Port logic:
#  - If auth proxy disabled: Jupyter runs on 8888 (tunnel to 8888).
#  - If auth proxy enabled: backend 8889, proxy 8888, tunnel to 8888.
BACKEND_PORT = 8889 if (USE_AUTH_PROXY and not DISABLE_AUTH) else 8888
PROXY_PORT = 8888  # always the public tunnel port

import os, pathlib, base64, threading, time, re, subprocess, sys, shutil, urllib.request

assert "COLAB_RELEASE_TAG" in os.environ, "Run inside Google Colab."

# Clean existing Jupyter if requested
if PERFORM_CLEAN:
    print("Cleaning existing Jupyter processes...")
    try:
        # Escaped awk field ref so Template does not treat $$2 as a placeholder
        subprocess.run(["bash","-lc","ps -ef | grep '[j]upyter-lab' | awk '{print $$2}' | xargs -r kill -9"], check=False)
        subprocess.run(["bash","-lc","ps -ef | grep '[j]upyter-lab'"], check=False)
    except Exception as e:
        print("Clean warning:", e)

!pip -q install "jupyterlab>=4" "jupyter_server>=2"

def ensure_cloudflared():
    if shutil.which("cloudflared"): return
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    dst = "/usr/local/bin/cloudflared"
    print("Downloading cloudflared...")
    subprocess.run(["curl","-L",url,"-o",dst], check=True)
    subprocess.run(["chmod","+x",dst], check=True)
    if not shutil.which("cloudflared"):
        raise RuntimeError("cloudflared install failed")
ensure_cloudflared()

os.chdir("/content")

# Export token to environment (extra safety; some tooling reads JUPYTER_TOKEN)
os.environ["JUPYTER_TOKEN"] = COLAB_JUPYTER_TOKEN

if GITHUB_PRIVATE_KEY_B64.strip():
    ssh_dir = pathlib.Path.home()/".ssh"; ssh_dir.mkdir(exist_ok=True)
    key_path = ssh_dir/"id_ed25519"
    # Decode the base64 deploy key (ensure we use base64 module)
    key_path.write_bytes(base64.b64decode(GITHUB_PRIVATE_KEY_B64.encode()))
    os.chmod(key_path, 0o600)
    for _t in ("ed25519","rsa"):
        os.system("ssh-keyscan -t " + _t + " github.com >> ~/.ssh/known_hosts 2>/dev/null")

JUPYTER_LOG = "/tmp/jupyter.log"

def start_jupyter():
    auth_args = []
    if DISABLE_AUTH:
        auth_args = ["--ServerApp.token=", "--ServerApp.password="]
    else:
        auth_args = [f"--ServerApp.token={COLAB_JUPYTER_TOKEN}", "--ServerApp.password=''"]
    cmd = [
        "python","-m","jupyterlab",
        "--ServerApp.ip=0.0.0.0",
        f"--ServerApp.port={BACKEND_PORT}",
        "--ServerApp.open_browser=False",
        "--ServerApp.allow_remote_access=True",
        "--ServerApp.allow_origin='*'",
        "--ServerApp.allow_origin_pat='.*'",
        "--ServerApp.disable_check_xsrf=True",
        "--ServerApp.trust_xheaders=True",
        "--ServerApp.root_dir=/content",
        "--ServerApp.log_level=INFO",
    ] + auth_args
    print("Launching Jupyter on port", BACKEND_PORT, "auth disabled =", bool(DISABLE_AUTH))
    with open(JUPYTER_LOG,"w") as lf: lf.write("Starting Jupyter...\n")
    return subprocess.Popen(cmd, stdout=open(JUPYTER_LOG,"a"), stderr=subprocess.STDOUT)

jupyter_proc = start_jupyter()

def ready(timeout=240):
    base_root = f"http://127.0.0.1:{BACKEND_PORT}/"
    urls = [base_root, base_root + "api/status"]
    if not DISABLE_AUTH:
        urls += [u + "?token=" + COLAB_JUPYTER_TOKEN for u in urls[:]]
    start=time.time(); shown=set()
    while time.time()-start < timeout:
        if int(time.time()-start)%20==0:
            tag=int(time.time()-start)
            if tag not in shown:
                try: print("Jupyter log tail:\n"+"".join(open(JUPYTER_LOG).readlines()[-8:]).strip())
                except: pass
                shown.add(tag)
        for u in urls:
            try:
                with urllib.request.urlopen(u) as r:
                    if r.status in (200,302,403,404): return True
            except: pass
        if jupyter_proc.poll() is not None:
            print("Jupyter exited early code", jupyter_proc.returncode); return False
        time.sleep(2)
    return False

if not ready():
    print("Jupyter failed. Last 100 lines:")
    try: print("".join(open(JUPYTER_LOG).readlines()[-100:]))
    except: pass
    raise SystemExit

# Optional auth proxy (only if auth enabled)
proxy_proc = None
if USE_AUTH_PROXY and not DISABLE_AUTH:
    BACKEND = BACKEND_PORT
    PROXY = PROXY_PORT
    PROXY_CODE = f'''
import http.server, socketserver, urllib.request, urllib.error, sys
TARGET = "http://127.0.0.1:{BACKEND}"
TOKEN = "{COLAB_JUPYTER_TOKEN}"
class H(http.server.BaseHTTPRequestHandler):
    def do_ANY(self):
        import urllib.request
        url = TARGET + self.path
        req = urllib.request.Request(url)
        if TOKEN and "token=" not in self.path:
            req.add_header("Authorization","token "+TOKEN)
        for k,v in self.headers.items():
            if k.lower()!="host": req.add_header(k,v)
        if self.command in ("POST","PUT","PATCH"):
            ln = int(self.headers.get("Content-Length","0"))
            body = self.rfile.read(ln) if ln else b""
            req.data = body
        req.method = self.command
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                body = r.read()
                self.send_response(r.status)
                for k,v in r.getheaders():
                    if k.lower()=="content-length": continue
                    self.send_header(k,v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            for k,v in e.headers.items():
                if k.lower()=="content-length": continue
                self.send_header(k,v)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as ex:
            b = ("Proxy error: "+repr(ex)).encode()
            self.send_response(502)
            self.send_header("Content-Type","text/plain")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
    def do_GET(self): self.do_ANY()
    def do_POST(self): self.do_ANY()
    def do_PUT(self): self.do_ANY()
    def do_DELETE(self): self.do_ANY()
    def do_PATCH(self): self.do_ANY()
    def log_message(self,*a): pass
with socketserver.ThreadingTCPServer(("0.0.0.0",{PROXY}), H) as httpd:
    print("Auth proxy on", {PROXY}, "->", {BACKEND})
    httpd.serve_forever()
'''
    print("Starting auth proxy on port", PROXY_PORT, "->", BACKEND_PORT)
    proxy_proc = subprocess.Popen([sys.executable,"-c",PROXY_CODE])

TUNNEL_TARGET_PORT = PROXY_PORT

def open_tunnel():
    print("Opening cloudflared tunnel to", TUNNEL_TARGET_PORT)
    proc = subprocess.Popen(
        ["cloudflared","tunnel","--url",f"http://localhost:{TUNNEL_TARGET_PORT}","--no-autoupdate","--loglevel","info"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    domain=None; deadline=time.time()+180
    while time.time()<deadline:
        line=proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                print("cloudflared exited", proc.returncode); break
            time.sleep(0.2); continue
        m=re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
        if m:
            domain=m.group(0); print("Tunnel domain:", domain); break
    return domain, proc

public_url,_tp = open_tunnel()
if not public_url:
    print("No Cloudflare URL. Exiting."); raise SystemExit

print("\nVerifying actual running servers (inside Colab):")
os.system("jupyter server list")

if DISABLE_AUTH:
    print("\nJupyter URLs (no auth):")
    print(public_url)
    print(public_url + "/lab")
else:
    print("\nJupyter URLs (try in order):")
    print(public_url + "/?token=" + COLAB_JUPYTER_TOKEN)
    print(public_url + "?token=" + COLAB_JUPYTER_TOKEN)
    print(public_url + "/lab?token=" + COLAB_JUPYTER_TOKEN)
    if USE_AUTH_PROXY:
        print("(Auth proxy injects Authorization header)")

def keep_alive():
    while True:
        try:
            url = public_url + "/api/status"
            if not DISABLE_AUTH:
                url += "?token=" + COLAB_JUPYTER_TOKEN
            urllib.request.urlopen(url, timeout=15).read()
        except: pass
        time.sleep(120)
threading.Thread(target=keep_alive, daemon=True).start()

def _clone(repo):
    print("Cloning:", repo)
    env=os.environ.copy()
    env["GIT_SSH_COMMAND"]="ssh -o StrictHostKeyChecking=accept-new"
    subprocess.run(["git","clone",repo], check=False, env=env)
for r in REPOS: _clone(r)

if OPTIONAL_ENV_FILE_CONTENT.strip():
    for r in REPOS:
        name=r.split(":")[-1].rsplit("/",1)[-1].removesuffix(".git")
        p=pathlib.Path("/content")/name/".env"
        p.write_text(OPTIONAL_ENV_FILE_CONTENT, encoding="utf-8")
        print("Wrote .env:", p)

print("\nColab ready. Copy one URL above into VS Code.")
# ============================================================================== 
""")

def build_cell(token, repos, deploy_key_b64, env_content, no_auth, auth_proxy, clean):
    return CELL_TEMPLATE.substitute(
        token=token,
        repos_json=json.dumps(repos, indent=2),
        deploy_key_b64=json.dumps(deploy_key_b64),
        env_content_json=json.dumps(env_content),
        disable_auth=("True" if no_auth else "False"),
        use_auth_proxy=("True" if auth_proxy else "False"),
        do_clean=("True" if clean else "False"),
    )

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--token", help="Explicit token (ignored if --no-auth).")
    p.add_argument("--no-auth", action="store_true", help="Disable Jupyter auth (INSECURE).")
    p.add_argument("--auth-proxy", action="store_true", help="Add proxy injecting Authorization header.")
    p.add_argument("--clean", action="store_true", help="Kill existing Jupyter processes first.")
    p.add_argument("--repo", action="append", default=[], help="SSH repo URL (repeatable).")
    p.add_argument("--deploy-key-b64", default="", help="Base64 private key for cloning.")
    p.add_argument("--env-file", help="Optional .env file to inject into each repo.")
    return p.parse_args()

def main():
    args = parse_args()
    token = "" if args.no_auth else (args.token or secrets.token_hex(32))
    repos = args.repo or [DEFAULT_REPO]
    deploy_key_b64 = args.deploy_key_b64 or ""
    env_content = ""
    if args.env_file:
        path = pathlib.Path(args.env_file)
        if path.is_file():
            env_content = path.read_text()
    sys.stdout.write(build_cell(token, repos, deploy_key_b64, env_content, args.no_auth, args.auth_proxy, args.clean))

if __name__ == "__main__":
    main()
