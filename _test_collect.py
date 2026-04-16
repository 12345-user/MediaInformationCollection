import sys
sys.path.insert(0, r'D:\Tools\creator-monitor')
from collectors import douyin, bilibili
from database.db import init_db, upsert_creator, upsert_video

init_db()

print("=== B站 ===")
v = bilibili.collect_creator("3690994815994200", "zhu")
print("B站 videos:", len(v))
for x in v[:2]:
    t = x.get("title", "?")
    w = x.get("views", 0)
    print(w, t[:30])

print()
print("=== 抖音 ===")
v2 = douyin.collect_creator("25424815218", "zhen")
print("抖音 videos:", len(v2))
for x in v2[:3]:
    t = x.get("title", "?")
    w = x.get("views", 0)
    lk = x.get("likes", 0)
    print(w, lk, t[:30])

print("Done")
