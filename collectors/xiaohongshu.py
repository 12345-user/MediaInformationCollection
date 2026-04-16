# -*- coding: utf-8 -*-
import sys, json, re, requests
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent.parent
COOKIE_FILE = BASE_DIR / "data" / "xiaohongshu_cookies.json"


def load_cookie_header():
    if COOKIE_FILE.exists():
        try:
            data = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
            return data.get("cookie_header", "")
        except:
            pass
    return ""


def collect_creator(uid, creator_id):
    cookie_str = load_cookie_header()
    videos = []

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
        "Cookie": cookie_str,
        "Referer": "https://www.xiaohongshu.com/",
        "Accept": "application/json, text/plain, */*",
    }

    if uid and uid != "xxxxxxx" and cookie_str:
        # 策略1: API 请求
        try:
            url = "https://edith.xiaohongshu.com/api/sns/web/v1/user_posted"
            resp = requests.get(url, headers=headers,
                params={"user_id": uid, "cursor": "", "num": 20, "sort_type": 1},
                timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                notes = data.get("data", {}).get("notes", [])
                for note in notes:
                    v = _parse(note)
                    v["creator_id"] = creator_id
                    videos.append(v)
                print("[xiaohongshu] API: " + str(len(notes)) + " notes")
        except Exception as e:
            print("[xiaohongshu] API failed: " + str(e))

    if not videos and uid and uid != "xxxxxxx":
        # 策略2: HTML 解析
        try:
            resp = requests.get(
                "https://www.xiaohongshu.com/user/profile/" + uid,
                headers={"User-Agent": headers["User-Agent"]},
                timeout=15)
            # 提取标题和点赞数
            titles = re.findall(r'"title"\s*:\s*"([^"]{3,80})"', resp.text)
            likes = re.findall(r'"liked_count"\s*:\s*"?(\d+)"?', resp.text)
            note_ids = re.findall(r'"note_id"\s*:\s*"([^"]{10,30})"', resp.text)
            ids_unique = []
            for nid in note_ids:
                if nid not in ids_unique:
                    ids_unique.append(nid)
            for i in range(min(len(ids_unique), 20)):
                lk = int(likes[i]) if i < len(likes) and likes[i].isdigit() else 0
                videos.append({
                    "id": ids_unique[i],
                    "title": titles[i] if i < len(titles) else "无标题",
                    "description": "",
                    "publish_date": "",
                    "views": 0,
                    "likes": lk,
                    "comments": 0,
                    "shares": 0,
                    "platform": "xiaohongshu",
                    "url": "https://www.xiaohongshu.com/explore/" + ids_unique[i],
                    "creator_id": creator_id,
                })
            print("[xiaohongshu] HTML: " + str(len(videos)) + " notes")
        except Exception as e:
            print("[xiaohongshu] HTML parse failed: " + str(e))

    return videos


def _parse(item):
    interact = item.get("interact_info", {}) or {}
    ts = str(item.get("time", "0"))
    try:
        if ts.isdigit():
            ts = datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d")
    except:
        pass
    try:
        likes = int(interact.get("liked_count", 0) or 0)
    except:
        likes = 0
    try:
        comments = int(interact.get("comment_count", 0) or 0)
    except:
        comments = 0
    try:
        shares = int(interact.get("share_count", 0) or 0)
    except:
        shares = 0
    return {
        "id": item.get("note_id", ""),
        "title": item.get("title", item.get("display_title", "")),
        "description": item.get("desc", "")[:200],
        "publish_date": str(ts),
        "views": 0,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "platform": "xiaohongshu",
        "url": "https://www.xiaohongshu.com/explore/" + str(item.get("note_id", "")),
    }
