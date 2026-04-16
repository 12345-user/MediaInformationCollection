# -*- coding: utf-8 -*-
"""
collectors/xiaohongshu.py - 小红书数据采集
策略：
  1. xhs CLI（agent-reach）需登录 Cookie
  2. Web 搜索 + 网页抓取
"""
import sys, json, re, subprocess
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

XHS_CLI = Path(r"C:\Users\12052\.agent-reach-venv\Scripts\xhs.exe")


def xhs_cli(*args):
    if not XHS_CLI.exists():
        return None
    try:
        r = subprocess.run(
            [str(XHS_CLI)] + list(args),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=30,
        )
        return r.stdout if r.returncode == 0 else None
    except:
        return None


def collect_creator(uid: str, creator_id: str):
    """采集小红书用户笔记"""
    videos = []

    # 尝试 CLI
    output = xhs_cli("user", uid, "--json")
    if output:
        try:
            data = json.loads(output)
            items = data if isinstance(data, list) else data.get("notes", [])
            for item in items:
                videos.append(parse_xhs_note(item))
        except:
            pass

    # Fallback: 搜索抓取
    if not videos:
        try:
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            }
            # 小红书用户主页（需登录）
            # 这里用搜索结果代替
            resp = requests.get(
                f"https://www.xiaohongshu.com/user/profile/{uid}",
                headers=headers, timeout=10,
            )
            # 提取基本信息
            titles = re.findall(r'"title":"([^"]{5,100})"', resp.text)
            for title in titles[:10]:
                videos.append({
                    "id": "",
                    "title": title,
                    "description": "",
                    "publish_date": "",
                    "views": 0, "likes": 0, "comments": 0, "shares": 0,
                    "platform": "xiaohongshu",
                    "url": f"https://www.xiaohongshu.com/user/profile/{uid}",
                })
        except Exception as e:
            print(f"[xiaohongshu] Error: {e}")

    for v in videos:
        v["creator_id"] = creator_id
    return videos


def parse_xhs_note(item: dict) -> dict:
    return {
        "id": item.get("note_id", ""),
        "title": item.get("title", item.get("display_title", "")),
        "description": item.get("desc", "")[:200],
        "publish_date": item.get("time", ""),
        "views": item.get("interact_info", {}).get("play_count", 0),
        "likes": item.get("interact_info", {}).get("liked_count", 0),
        "comments": item.get("interact_info", {}).get("comment_count", 0),
        "shares": item.get("interact_info", {}).get("share_count", 0),
        "platform": "xiaohongshu",
        "url": f"https://www.xiaohongshu.com/explore/{item.get('note_id', '')}",
    }
