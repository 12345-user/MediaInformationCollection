# -*- coding: utf-8 -*-
"""
collectors/run.py - 主采集脚本
支持：UID精准采集 + 关键词搜索采集
"""
import sys, json, os, subprocess
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"D:\Tools\creator-monitor")

from database.db import init_db, upsert_creator, upsert_video, export_to_json, clean_old_data
from collectors import bilibili, douyin, xiaohongshu

PYTHON_BIN = r"C:\Users\12052\.agent-reach-venv\Scripts\python.exe"
BILI_CLI = r"C:\Users\12052\.agent-reach-venv\Scripts\bili.exe"

CREATORS_FILE = Path(r"D:\Tools\creator-monitor\creators.json")
DATA_DIR = Path(r"D:\Tools\creator-monitor\data")
GITHUB_DATA_FILE = DATA_DIR / "latest_data.json"


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


def search_bilibili_users(keyword: str, max_count: int = 5):
    """搜索B站用户，返回 [(uid, name, fans), ...]"""
    result = run_bili("search", keyword, "--type", "user", "--max", str(max_count), "--json")
    if result.get("returncode") != 0:
        return []
    try:
        data = json.loads(result["stdout"])
        if data.get("ok"):
            users = data.get("data", [])
            return [(u.get("id", ""), u.get("name", ""), u.get("fans", 0)) for u in users]
    except:
        pass
    return []


def load_creators():
    if CREATORS_FILE.exists():
        data = json.loads(CREATORS_FILE.read_text(encoding="utf-8"))
        return data.get("creators", [])
    return []


def collect_all():
    creators = load_creators()
    init_db()
    total_collected = 0
    results = {}

    for creator in creators:
        cid = creator["id"]
        platform = creator["platform"]
        uid = creator.get("uid", "")
        name = creator["name"]

        print(f"[{platform}] {name} (uid={uid})...")
        upsert_creator(creator)
        videos = []

        try:
            if platform == "bilibili":
                if uid and uid not in ("搜索中", "xxxxxxx", ""):
                    # UID 精准采集
                    videos = bilibili.collect_creator(uid, cid)
                    print(f"  UID采集: {len(videos)} videos")
                else:
                    # 关键词搜索采集
                    keywords = creator.get("topic", "").split("/")
                    for kw in keywords:
                        kw = kw.strip()
                        if kw:
                            found_videos = bilibili.collect_by_search(kw, cid, max_count=5)
                            videos.extend(found_videos)
                            print(f"  搜索[{kw}]: {len(found_videos)} videos")
                    videos = videos[:10]  # 去重，保留10个

            elif platform == "douyin":
                if uid and uid not in ("MS4wLjABAAAAHxxxxxxxx",):
                    videos = douyin.collect_creator(uid, cid)
                else:
                    # Fallback: 用关键词搜索
                    videos = douyin.collect_creator(uid, cid)  # 会用搜索fallback
                print(f"  抖音: {len(videos)} videos")

            elif platform == "xiaohongshu":
                if uid and uid != "xxxxxxx":
                    videos = xiaohongshu.collect_creator(uid, cid)
                print(f"  小红书: {len(videos)} videos")

            # 去重
            seen = set()
            unique = []
            for v in videos:
                vid = v.get("id", "") + v.get("title", "")
                if vid not in seen:
                    seen.add(vid)
                    unique.append(v)
            videos = unique

            for v in videos:
                upsert_video(cid, v)

            results[cid] = {"name": name, "platform": platform, "videos": len(videos)}
            total_collected += len(videos)
            print(f"  => 采集 {len(videos)} 个视频")

        except Exception as e:
            results[cid] = {"name": name, "platform": platform, "error": str(e)}
            print(f"  => ERROR: {e}")

    # 导出 JSON（GitHub 同步用）
    GITHUB_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    all_data = export_to_json()
    GITHUB_DATA_FILE.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 清理旧数据
    deleted = clean_old_data(days=90)

    summary = {
        "collected_at": datetime.now().isoformat(),
        "total_videos": total_collected,
        "creators_processed": len(creators),
        "old_records_deleted": deleted,
        "results": results,
    }

    report_file = DATA_DIR / f"collect_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[完成] 共采集 {total_collected} 个视频，覆盖 {len(creators)} 位创作者")
    print(f"[完成] 数据已导出: {GITHUB_DATA_FILE}")
    return summary


if __name__ == "__main__":
    collect_all()
