# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'D:\Tools\creator-monitor')
from collectors import bilibili

print("Testing bili CLI...")
result = bilibili.bili("--help")
print("stdout:", result.get("stdout", "")[:300])
print("stderr:", result.get("stderr", "")[:500])
print("returncode:", result.get("returncode"))
