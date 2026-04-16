# -*- coding: utf-8 -*-
import sys, os, subprocess, json
PYTHON_BIN = r"C:\Users\12052\.agent-reach-venv\Scripts\python.exe"
BILI_CLI = r"C:\Users\12052\.agent-reach-venv\Scripts\bili.exe"

def run_bili(*args):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(
        [PYTHON_BIN, BILI_CLI] + list(args),
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        env=env, timeout=20,
    )
    return r

# Check raw search output
print("=== Search raw ===")
r = run_bili("search", "帧数燃烧", "--type", "user", "--max", "5", "--json")
if r.stdout:
    try:
        data = json.loads(r.stdout)
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
    except:
        print(r.stdout[:500])

print()
print("=== User videos raw (帧数燃烧 uid 未知) ===")
# First search to get uid, then get videos
r2 = run_bili("user-videos", "帧数燃烧", "--max", "5", "--json")
print("rc:", r2.returncode, "stdout len:", len(r2.stdout))
if r2.stdout:
    try:
        data = json.loads(r2.stdout)
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
    except:
        print(r2.stdout[:500])
else:
    print("stderr:", r2.stderr[:300])
