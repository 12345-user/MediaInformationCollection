# -*- coding: utf-8 -*-
import sys, os, subprocess, json
sys.stdout.reconfigure(encoding='utf-8')

DOUYIN_CLI = r"C:\Users\12052\.agent-reach-venv\Scripts\douyin-mcp-server.exe"
PYTHON_BIN = r"C:\Users\12052\.agent-reach-venv\Scripts\python.exe"

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"

print("=== Douyin MCP CLI --help ===")
r = subprocess.run(
    [PYTHON_BIN, DOUYIN_CLI, "--help"],
    capture_output=True, text=True,
    encoding="utf-8", errors="replace",
    env=env, timeout=15,
)
print("rc:", r.returncode)
print("stdout:", r.stdout[:500])
print("stderr:", r.stderr[:300])

print()
print("=== Douyin MCP video list ===")
r2 = subprocess.run(
    [PYTHON_BIN, DOUYIN_CLI, "video-list", "--uid", "MS4wLjABAAAAIaxl8QfBDEg6mEKha4dKNXM8JxtQQXADYHBmTYSvgNk"],
    capture_output=True, text=True,
    encoding="utf-8", errors="replace",
    env=env, timeout=20,
)
print("rc:", r2.returncode)
print("stdout:", r2.stdout[:500])
print("stderr:", r2.stderr[:300])
