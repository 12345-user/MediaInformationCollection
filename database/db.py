# -*- coding: utf-8 -*-
"""
database/db.py - SQLite 数据库操作
存储创作者数据和视频指标
"""
import sqlite3, json, sys, os
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")

# 跨平台路径：优先用环境变量，其次用项目根目录下的 data/
_db_env = os.environ.get("CREATOR_MONITOR_DB", "")
DB_PATH = Path(_db_env) if _db_env else Path(__file__).parent.parent / "data" / "metrics.db"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS creators (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            platform TEXT NOT NULL,
            uid TEXT,
            url TEXT,
            topic TEXT,
            style TEXT,
            first_seen TEXT,
            last_updated TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id TEXT NOT NULL,
            video_id TEXT NOT NULL,
            title TEXT,
            description TEXT,
            publish_date TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            collected_at TEXT NOT NULL,
            UNIQUE(creator_id, video_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id TEXT NOT NULL,
            video_id TEXT NOT NULL,
            date TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            collected_at TEXT NOT NULL,
            UNIQUE(creator_id, video_id, date)
        )
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_videos_creator ON videos(creator_id)
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_daily_creator ON daily_stats(creator_id, date)
    """)
    conn.commit()
    conn.close()


def upsert_creator(creator: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO creators (id, name, platform, uid, url, topic, style, first_seen, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            platform=excluded.platform,
            uid=excluded.uid,
            url=excluded.url,
            topic=excluded.topic,
            style=excluded.style,
            last_updated=excluded.last_updated
    """, (
        creator["id"],
        creator["name"],
        creator["platform"],
        creator.get("uid", ""),
        creator.get("url", ""),
        creator.get("topic", ""),
        creator.get("style", ""),
        datetime.now().isoformat(),
        datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()


def upsert_video(creator_id: str, video: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO videos
        (creator_id, video_id, title, description, publish_date, views, likes, comments, shares, collected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(creator_id, video_id) DO UPDATE SET
            title=excluded.title,
            description=excluded.description,
            views=excluded.views,
            likes=excluded.likes,
            comments=excluded.comments,
            shares=excluded.shares,
            collected_at=excluded.collected_at
    """, (
        creator_id,
        video.get("id", ""),
        video.get("title", ""),
        video.get("description", ""),
        video.get("publish_date", ""),
        video.get("views", 0),
        video.get("likes", 0),
        video.get("comments", 0),
        video.get("shares", 0),
        datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()


def record_daily_stats(creator_id: str, video_id: str, stats: dict):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO daily_stats
        (creator_id, video_id, date, views, likes, comments, shares, collected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(creator_id, video_id, date) DO UPDATE SET
            views=excluded.views,
            likes=excluded.likes,
            comments=excluded.comments,
            shares=excluded.shares,
            collected_at=excluded.collected_at
    """, (
        creator_id, video_id, today,
        stats.get("views", 0),
        stats.get("likes", 0),
        stats.get("comments", 0),
        stats.get("shares", 0),
        datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()


def get_all_creators():
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("SELECT * FROM creators ORDER BY platform, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_videos(creator_id: str = None, days: int = 7):
    conn = get_conn()
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    if creator_id:
        rows = c.execute(
            "SELECT * FROM videos WHERE creator_id=? AND collected_at>=? ORDER BY collected_at DESC",
            (creator_id, cutoff)
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT * FROM videos WHERE collected_at>=? ORDER BY collected_at DESC",
            (cutoff,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_daily_trend(creator_id: str, days: int = 30):
    conn = get_conn()
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = c.execute("""
        SELECT date, SUM(views) as total_views, SUM(likes) as total_likes,
               SUM(comments) as total_comments, SUM(shares) as total_shares,
               COUNT(DISTINCT video_id) as video_count
        FROM daily_stats
        WHERE creator_id=? AND date>=?
        GROUP BY date
        ORDER BY date
    """, (creator_id, cutoff)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_trends(days: int = 30):
    conn = get_conn()
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = c.execute("""
        SELECT d.date, d.creator_id, c.name, c.platform,
               SUM(d.views) as total_views, SUM(d.likes) as total_likes,
               SUM(d.comments) as total_comments,
               COUNT(DISTINCT d.video_id) as video_count
        FROM daily_stats d
        JOIN creators c ON d.creator_id = c.id
        WHERE d.date>=?
        GROUP BY d.date, d.creator_id
        ORDER BY d.date, total_views DESC
    """, (cutoff,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def export_to_json():
    """导出全部数据为 JSON（用于 GitHub 同步）"""
    conn = get_conn()
    c = conn.cursor()
    creators = [dict(r) for r in c.execute("SELECT * FROM creators").fetchall()]
    videos = [dict(r) for r in c.execute("SELECT * FROM videos ORDER BY collected_at DESC LIMIT 500").fetchall()]
    daily = [dict(r) for r in c.execute("SELECT * FROM daily_stats ORDER BY date DESC, creator_id LIMIT 2000").fetchall()]
    conn.close()
    return {
        "exported_at": datetime.now().isoformat(),
        "creators": creators,
        "recent_videos": videos,
        "daily_stats": daily,
    }


def import_from_json(data: dict):
    """从 JSON 导入数据"""
    init_db()
    for c_data in data.get("creators", []):
        upsert_creator(c_data)
    for v_data in data.get("recent_videos", []):
        upsert_video(v_data["creator_id"], v_data)


def clean_old_data(days: int = 90):
    """清理超过 N 天的旧数据"""
    conn = get_conn()
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    c.execute("DELETE FROM daily_stats WHERE date < ?", (cutoff,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return deleted
