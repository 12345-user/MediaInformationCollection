import sys, json, os
from pathlib import Path
sys.path.insert(0, r'D:\Tools\creator-monitor')
sys.stdout.reconfigure(encoding='utf-8')

# Patch subprocess to fix Python 3.14 compatibility
import subprocess as _subprocess
_orig_run = _subprocess.run
def _fixed_run(*args, **kwargs):
    if 'timeout' in kwargs and not isinstance(kwargs['timeout'], (int, float, type(None))):
        kwargs['timeout'] = int(kwargs['timeout'])
    return _orig_run(*args, **kwargs)
_subprocess.run = _fixed_run

from collectors import douyin, bilibili
from database.db import init_db, upsert_creator, upsert_video, export_to_json

init_db()

results = {}

# B站 - 帧数燃烧
print("[1] B站 帧数燃烧...")
v = bilibili.collect_creator("3690994815994200", "zhen_shu_ran_shao_bilibili")
for x in v:
    upsert_creator({"id": "zhen_shu_ran_shao_bilibili", "name": "帧数燃烧_B站", "platform": "bilibili", "uid": "3690994815994200"})
    upsert_video("zhen_shu_ran_shao_bilibili", x)
print("  B站 帧数燃烧:", len(v), "videos")

# B站 - 陈师傅路亚
print("[2] B站 陈师傅路亚...")
v = bilibili.collect_creator("434181042", "chen_shi_fu_bilibili")
for x in v:
    upsert_creator({"id": "chen_shi_fu_bilibili", "name": "陈师傅路亚_B站", "platform": "bilibili", "uid": "434181042"})
    upsert_video("chen_shi_fu_bilibili", x)
print("  B站 陈师傅:", len(v), "videos")

# 抖音 - 帧数燃烧
print("[3] 抖音 帧数燃烧...")
v = douyin.collect_creator("25424815218", "zhen_shu_ran_shao_douyin")
for x in v:
    upsert_creator({"id": "zhen_shu_ran_shao_douyin", "name": "帧数燃烧_抖音", "platform": "douyin", "uid": "25424815218"})
    upsert_video("zhen_shu_ran_shao_douyin", x)
print("  抖音 帧数燃烧:", len(v), "videos")

# 抖音 - Bob同学
print("[4] 抖音 Bob同学...")
v = douyin.collect_creator("baodi6611", "bob_tong_xue_douyin")
for x in v:
    upsert_creator({"id": "bob_tong_xue_douyin", "name": "Bob同学_抖音", "platform": "douyin", "uid": "baodi6611"})
    upsert_video("bob_tong_xue_douyin", x)
print("  抖音 Bob同学:", len(v), "videos")

# Export
data = export_to_json()
out = r"D:\Tools\creator-monitor\data\latest_data.json"
text = json.dumps(data, ensure_ascii=False, indent=2)
Path(out).write_text(text, encoding="utf-8")
print()
total = len(data.get("recent_videos", []))
print("Done! Total videos:", total)
print("Saved to:", out)
