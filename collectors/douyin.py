# -*- coding: utf-8 -*-
import sys, json, re, requests
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent.parent
COOKIE_FILE = BASE_DIR / "data" / "douyin_cookies.json"


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
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Referer": "https://www.douyin.com/",
        "Accept": "application/json, text/plain, */*",
    }
    if cookie_str:
        headers["Cookie"] = cookie_str

    sec_uid = uid
    # 数字UID转sec_uid（如果需要）
    if uid and uid.isdigit():
        sec_uid = uid  # 直接用数字uid查询

    if sec_uid and cookie_str:
        # 策略1: 登录态API
        try:
            url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
            params = {
                "sec_user_id": sec_uid,
                "count": 18,
                "max_cursor": 0,
                "cookie_enabled": "true",
                "platform": "PC",
            }
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code == 200 and resp.text.strip().startswith("{"):
                data = resp.json()
                awemes = data.get("aweme_list", [])
                for item in awemes:
                    v = _parse(item)
                    v["creator_id"] = creator_id
                    videos.append(v)
                print("[douyin] API: " + str(len(awemes)) + " videos")
        except Exception as e:
            print("[douyin] API failed: " + str(e))

    if not videos:
        # 策略2: 用户主页 HTML
        try:
            if sec_uid:
                resp = requests.get(
                    "https://www.douyin.com/user/" + str(sec_uid),
                    headers={"User-Agent": headers["User-Agent"]},
                    timeout=15)
                titles = re.findall(r'"desc"\s*:\s*"([^"]{3,100})"', resp.text)
                plays = re.findall(r'"play_count"\s*:\s*"?(\d+)"?', resp.text)
                likes = re.findall(r'"digg_count"\s*:\s*"?(\d+)"?', resp.text)
                video_ids = re.findall(r'"aweme_id"\s*:\s*"(\d+)"?', resp.text)
                ids_unique = []
                for vid in video_ids:
                    if vid not in ids_unique:
                        ids_unique.append(vid)
                for i in range(min(len(ids_unique), 20)):
                    pl = int(plays[i]) if i < len(plays) and plays[i].isdigit() else 0
                    lk = int(likes[i]) if i < len(likes) and likes[i].isdigit() else 0
                    videos.append({
                        "id": ids_unique[i],
                        "title": titles[i] if i < len(titles) else "无标题",
                        "description": "",
                        "publish_date": "",
                        "views": pl,
                        "likes": lk,
                        "comments": 0,
                        "shares": 0,
                        "platform": "douyin",
                        "url": "https://www.douyin.com/video/" + ids_unique[i],
                        "creator_id": creator_id,
                    })
                print("[douyin] HTML parse: " + str(len(videos)) + " videos")
        except Exception as e:
            print("[douyin] HTML parse failed: " + str(e))

    return videos


def _parse(item):
    stats = item.get("statistics", {}) or {}
    ct = item.get("create_time", 0)
    try:
        if str(ct).isdigit() and int(ct) > 0:
            ct = datetime.fromtimestamp(int(ct)).strftime("%Y-%m-%d")
        else:
            ct = str(ct)
    except:
        ct = ""
    return {
        "id": item.get("aweme_id", ""),
        "title": (item.get("desc", "") or "无标题")[:80],
        "description": item.get("desc", "")[:200],
        "publish_date": str(ct),
        "views": int(stats.get("play_count", 0) or 0),
        "likes": int(stats.get("digg_count", 0) or 0),
        "comments": int(stats.get("comment_count", 0) or 0),
        "shares": int(stats.get("share_count", 0) or 0),
        "platform": "douyin",
        "url": "https://www.douyin.com/video/" + str(item.get("aweme_id", "")),
    }
