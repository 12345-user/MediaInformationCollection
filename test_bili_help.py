# -*- coding: utf-8 -*-
import sys, os, subprocess, json
sys.path.insert(0, r'D:\Tools\creator-monitor')
from collectors import bilibili

# Test user-videos with the corrected function
print("=== Test: get_user_videos ===")
videos = bilibili.get_user_videos("477469167", max_count=3)
print("Videos:", len(videos))
for v in videos[:3]:
    print(" -", v.get("title","?")[:50], "| views:", v.get("views","?"), "| url:", v.get("url","?"))

print()
print("=== Test: search_users ===")
users = bilibili.search_users("帧数燃烧", max_count=5)
print("Users:", len(users))
for u in users[:5]:
    print(" -", u.get("uname","?"), "| uid:", u.get("uid","?"))

print()
print("=== Test: search_users Bob同学 ===")
users2 = bilibili.search_users("Bob同学 自媒体", max_count=5)
print("Users:", len(users2))
for u in users2[:5]:
    print(" -", u.get("uname","?"), "| uid:", u.get("uid","?"))
