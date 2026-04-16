# -*- coding: utf-8 -*-
import sys, os, subprocess, json
sys.path.insert(0, r'D:\Tools\creator-monitor')
from collectors import bilibili

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

print("=== Test 1: bili user-videos ===")
r = run_bili("user-videos", "477469167", "--max", "3", "--json")
print("rc:", r.returncode)
if r.stdout:
    try:
        videos = json.loads(r.stdout)
        print("Videos:", len(videos) if isinstance(videos, list) else "dict")
        if isinstance(videos, list):
            for v in videos[:3]:
                print(" -", v.get("title","?")[:50], "| views:", v.get("stat",{}).get("view","?"))
        elif isinstance(videos, dict):
            print("Keys:", list(videos.keys()))
            for k, v in list(videos.items())[:3]:
                print(f" {k}: {str(v)[:80]}")
    except Exception as e:
        print("JSON error:", e, "| stdout:", r.stdout[:200])

print()
print("=== Test 2: bili search 用户 ===")
r2 = run_bili("search", "帧数燃烧", "--type", "user", "--max", "5", "--json")
print("rc:", r2.returncode)
if r2.stdout:
    try:
        raw = json.loads(r2.stdout)
        inner = raw.get("data", {}) if isinstance(raw, dict) else {}
        results = inner.get("results", []) if isinstance(inner, dict) else inner
        print("Users found:", len(results) if isinstance(results, list) else "N/A")
        if isinstance(results, list):
            for u in results[:3]:
                print(" -", u.get("uname","?"), "| uid:", str(u.get("uid",""))[:20])
    except Exception as e:
        print("Parse error:", e)
        print(r2.stdout[:300])

print()
print("=== Test 3: Module collect ===")
videos = bilibili.collect_creator("477469167", "test_bilibili")
print("Collected:", len(videos), "videos")
for v in videos[:2]:
    print(" -", v.get("title","?")[:50], "| views:", v.get("views","?"))

users = bilibili.search_users("帧数燃烧", max_count=3)
print("Search users:", len(users))
for u in users[:3]:
    print(" -", u.get("uname","?"))
