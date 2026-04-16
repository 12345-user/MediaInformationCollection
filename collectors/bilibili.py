# -*- coding: utf-8 -*-
"""
collectors/bilibili.py - B站数据采集
工具：bili CLI（agent-reach）
命令：user-videos / search
"""
import sys, json, subprocess, os
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

PYTHON_BIN = Path(r"C:\Users\12052\.agent-reach-venv\Scripts\python.exe")
BILI_CLI = Path(r"C:\Users\12052\.agent-reach-venv\Scripts\bili.exe")


def bili(*args):
    """调用 bili CLI，设置 PYTHONIOENCODING 解决 Windows GBK 编码问题"""
    if not BILI_CLI.exists():
        return {"error": f"bili CLI not found: {BILI_CLI}"}
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        r = subprocess.run(
            [str(PYTHON_BIN), str(BILI_CLI)] + list(args),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        return {"stdout": r.stdout, "stderr": r.stderr, "returncode": r.returncode}
    except Exception as e:
        return {"error": str(e)}


def _parse_json(stdout: str):
    """安全解析 JSON"""
    if not stdout or not stdout.strip():
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {}


def get_user_videos(uid_or_name: str, max_count: int = 10):
    """获取用户视频列表"""
    result = bili("user-videos", uid_or_name, "--max", str(max_count), "--json")
    if "error" in result:
        return []
    data = _parse_json(result["stdout"])
    # 格式: {"ok":true, "data": [...]}
    if data.get("ok") and isinstance(data.get("data"), list):
        return data["data"]
    return []


def search_users(keyword: str, max_count: int = 5):
    """搜索用户"""
    result = bili("search", keyword, "--type", "user", "--max", str(max_count), "--json")
    if "error" in result:
        return []
    data = _parse_json(result["stdout"])
    if data.get("ok") and isinstance(data.get("data"), list):
        return data["data"]
    return []


def parse_video(item: dict) -> dict:
    """解析 B站 视频数据为统一格式"""
    # 搜索结果的视频格式 vs user-videos 的格式
    bvid = item.get("bvid", item.get("id", ""))
    stats = item.get("stats", item)  # user-videos 用 stats，其他用直接字段
    title = item.get("title", "")
    url = item.get("url", f"https://www.bilibili.com/video/{bvid}")

    # 发布时间
    pubdate = item.get("pubdate", item.get("publish_date", ""))
    if isinstance(pubdate, int) and pubdate > 0:
        pubdate = datetime.fromtimestamp(pubdate).strftime("%Y-%m-%d")

    return {
        "id": bvid,
        "title": title,
        "description": item.get("description", "")[:200],
        "publish_date": str(pubdate),
        "views": stats.get("view", 0) or stats.get("play", 0),
        "likes": stats.get("like", 0),
        "comments": stats.get("danmaku", 0) or stats.get("reply", 0),
        "shares": stats.get("share", 0),
        "platform": "bilibili",
        "url": url,
    }


def collect_creator(uid_or_name: str, creator_id: str):
    """采集指定创作者的视频"""
    items = get_user_videos(uid_or_name, max_count=10)
    videos = []
    for item in items:
        v = parse_video(item)
        v["creator_id"] = creator_id
        videos.append(v)
    return videos


def collect_by_search(keyword: str, creator_id: str, max_count: int = 5):
    """通过搜索获取视频"""
    result = bili("search", keyword, "--type", "video", "--max", str(max_count), "--json")
    if "error" in result:
        return []
    data = _parse_json(result["stdout"])
    items = []
    if data.get("ok"):
        d = data.get("data", [])
        items = d if isinstance(d, list) else d.get("results", [])
    videos = []
    for item in items:
        v = parse_video(item)
        v["creator_id"] = creator_id
        videos.append(v)
    return videos
