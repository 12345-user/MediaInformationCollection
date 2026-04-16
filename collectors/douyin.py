# -*- coding: utf-8 -*-
"""
collectors/douyin.py - 抖音数据采集
策略：
  1. 尝试 douyin-mcp-server CLI
  2. Web 搜索 + 第三方平台代理获取公开数据
  3. 直接抓取（需 Cookie，有限制）
"""
import sys, json, re, subprocess
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

DOUYIN_CLI = Path(r"C:\Users\12052\.agent-reach-venv\Scripts\douyin-mcp-server.exe")


def douyin_cli(*args):
    if not DOUYIN_CLI.exists():
        return None
    try:
        r = subprocess.run(
            [str(DOUYIN_CLI)] + list(args),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=30,
        )
        return r.stdout if r.returncode == 0 else None
    except:
        return None


def fetch_via_webapi(uid: str) -> list:
    """
    通过抖音用户主页/API 获取视频列表
    uid 可能是数字UID或sec_uid
    """
    import requests

    videos = []
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.douyin.com/",
    }

    # 确定使用哪个uid参数
    sec_uid = uid  # 默认uid就是sec_uid格式

    # 策略1：抖音用户主页（移动端UA，容易绕过反爬）
    try:
        url = f"https://www.douyin.com/aweme/v1/web/aweme/post/?sec_uid={sec_uid}&count=18&max_cursor=0&cookie_enabled=true&platform=PC"
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code == 200 and resp.text.strip().startswith("{"):
            data = resp.json()
            aweme_list = data.get("aweme_list", [])
            for item in aweme_list:
                videos.append(parse_douyin_video(item))
    except Exception as e:
        print(f"[douyin] API failed: {e}")

    # 策略2：通过用户主页HTML解析
    if not videos:
        try:
            profile_url = f"https://www.douyin.com/user/{sec_uid}"
            resp = requests.get(profile_url, headers=headers, timeout=15)
            # 从HTML中提取RENDER_DATA或视频信息
            render_data = re.search(r'<script id="RENDER_DATA" type="application/json">([^<]+)</script>', resp.text)
            if render_data:
                import html as html_module
                unescaped = html_module.unescape(render_data.group(1))
                data = json.loads(unescaped)
                # 解析用户数据...
        except Exception as e:
            print(f"[douyin] Profile parse failed: {e}")

    return videos


def parse_douyin_video(item: dict) -> dict:
    """解析抖音视频数据"""
    desc = item.get("desc", "")
    stats = item.get("statistics", {})
    create_time = item.get("create_time", 0)
    if create_time:
        create_time = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d") if isinstance(create_time, int) else str(create_time)
    return {
        "id": item.get("aweme_id", ""),
        "title": desc[:80] if desc else "无标题",
        "description": desc[:200],
        "publish_date": create_time,
        "views": stats.get("play_count", 0),
        "likes": stats.get("digg_count", 0),
        "comments": stats.get("comment_count", 0),
        "shares": stats.get("share_count", 0),
        "platform": "douyin",
        "url": f"https://www.douyin.com/video/{item.get('aweme_id', '')}",
    }


def collect_creator(uid: str, creator_id: str):
    """采集指定创作者的视频"""
    videos = fetch_via_webapi(uid)
    for v in videos:
        v["creator_id"] = creator_id
    return videos
