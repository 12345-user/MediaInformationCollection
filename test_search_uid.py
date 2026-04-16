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
        env=env, timeout=30,
    )
    return r

for keyword in ["Bob同学", "bob同学", "Bob", "大学生 AI学习", "AI 学习 自媒体 大学生"]:
    r = run_bili("search", keyword, "--type", "user", "--max", "3", "--json")
    if r.stdout:
        data = json.loads(r.stdout)
        users = data.get("data", []) if isinstance(data, dict) else []
        if users:
            print(f"[{keyword}] found:")
            for u in users:
                print(f"  uid={u.get('id','?')}  name={u.get('name','?')}  fans={u.get('fans','?')}")
        else:
            print(f"[{keyword}] no results")
    else:
        print(f"[{keyword}] no stdout, rc={r.returncode}")
