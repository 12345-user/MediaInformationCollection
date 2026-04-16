# -*- coding: utf-8 -*-
import sys, os, subprocess, json
sys.path.insert(0, r'D:\Tools\creator-monitor')
from database.db import init_db, upsert_creator, upsert_video, export_to_json, get_all_creators
from collectors import bilibili, douyin, xiaohongshu

def run_bili(*args):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(
        [r"C:\Users\12052\.agent-reach-venv\Scripts\python.exe",
         r"C:\Users\12052\.agent-reach-venv\Scripts\bili.exe"] + list(args),
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        env=env, timeout=30,
    )
    return r

print("=== Step 1: 搜索陈师傅路亚 B站 UID ===")
r = run_bili("search", "陈师傅路亚", "--type", "user", "--max", "5", "--json")
if r.stdout:
    data = json.loads(r.stdout)
    users = data.get("data", []) if isinstance(data, dict) else []
    print("Found users:")
    for u in users[:5]:
        print(f"  uid={u.get('id','?')}  name={u.get('name','?')}  fans={u.get('fans','?')}")

print()
print("=== Step 2: 采集帧数燃烧_B站视频 ===")
init_db()
videos = bilibili.collect_creator("3690994815994200", "zhen_shu_ran_shao_bilibili")
print(f"Collected {len(videos)} videos")
for v in videos[:3]:
    print(f"  {v.get('title','?')[:40]}")
    print(f"  views={v.get('views',0):,}  likes={v.get('likes',0):,}")
    upsert_creator({
        "id": "zhen_shu_ran_shao_bilibili",
        "name": "帧数燃烧_B站",
        "platform": "bilibili",
        "uid": "3690994815994200",
        "topic": "AI工具工作流",
        "style": "快节奏工具演示",
    })
    upsert_video("zhen_shu_ran_shao_bilibili", v)

print()
print("=== Step 3: 通过B站搜索采集 ===")
# 搜索帧数燃烧的AI相关视频
search_videos = bilibili.collect_by_search("AI工具 工作流 自媒体", "zhen_shu_ran_shao_bilibili", max_count=5)
print(f"Search found {len(search_videos)} videos")
for v in search_videos[:3]:
    print(f"  {v.get('title','?')[:40]}")
    upsert_video("zhen_shu_ran_shao_bilibili", v)

print()
print("=== Step 4: 导出数据 ===")
data = export_to_json()
print(f"Exported {len(data.get('recent_videos',[]))} videos")
print("Done!")
