# -*- coding: utf-8 -*-
"""
get_cookies.py — 从 Chrome 自动提取登录 Cookie
无需账号密码，直接读取浏览器已登录状态

使用方法：
1. 关闭 Chrome 浏览器（重要！否则 Cookie 数据库被锁）
2. 运行: python get_cookies.py
3. 脚本会自动提取抖音/小红书的 Cookie 并保存
"""
import sys, json, os, sqlite3, shutil, tempfile
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

COOKIE_DIR = Path(__file__).parent / "data"
COOKIE_DIR.mkdir(parents=True, exist_ok=True)

# Chrome Cookie 数据库路径
CHROME_COOKIE_DB = Path(
    os.environ.get("LOCALAPPDATA", "")
) / "Google/Chrome/User Data/Default/Network/Cookies"

PLATFORMS = {
    "douyin": {
        "name": "抖音",
        "domains": ["douyin.com", ".douyin.com"],
        "cookie_file": COOKIE_DIR / "douyin_cookies.json",
    },
    "xiaohongshu": {
        "name": "小红书",
        "domains": ["xiaohongshu.com", ".xiaohongshu.com"],
        "cookie_file": COOKIE_DIR / "xiaohongshu_cookies.json",
    },
}


def extract_cookies(domain_pattern: str) -> list:
    """从 Chrome Cookie 数据库提取指定域名的 Cookie"""
    if not CHROME_COOKIE_DB.exists():
        return []

    # 复制数据库（避免 Chrome 文件锁）
    temp_db = Path(tempfile.mktemp(suffix=".db"))
    try:
        shutil.copy2(CHROME_COOKIE_DB, temp_db)
    except PermissionError:
        print("  ⚠️ Cookie 数据库被 Chrome 占用！请先关闭 Chrome 浏览器")
        return []

    cookies = []
    try:
        conn = sqlite3.connect(str(temp_db))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Chrome 用 _dot + percent-encoded 域名存储
        encoded = domain_pattern.replace(".", "_")
        c.execute("""
            SELECT host_key, name, value, path, expires_utc,
                   is_secure, is_httponly, creation_utc, last_access_utc
            FROM cookies
            WHERE host_key LIKE ? OR host_key LIKE ?
            ORDER BY host_key, name
        """, (f"%{encoded}%", f"%{domain_pattern}%"))

        for row in c.fetchall():
            cookies.append({
                "name": row["name"],
                "value": row["value"],
                "domain": row["host_key"],
                "path": row["path"],
                "secure": bool(row["is_secure"]),
                "httpOnly": bool(row["is_httponly"]),
            })
        conn.close()
    finally:
        temp_db.unlink(missing_ok=True)

    return cookies


def format_cookies_for_requests(cookies: list) -> str:
    """把 Cookie 列表格式化成 requests 可用的字符串"""
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


def main():
    print()
    print("=" * 55)
    print("  🎯 抖音 / 小红书 Cookie 自动提取工具")
    print("=" * 55)
    print()
    print(f"Chrome Cookie DB: {CHROME_COOKIE_DB}")
    print(f"Cookie 保存目录: {COOKIE_DIR}")
    print()
    print("⚠️  请确保 Chrome 浏览器已关闭！")
    print()
    confirm = input("确认 Chrome 已关闭？按 Enter 继续（Ctrl+C 取消）... ")
    print()

    results = {}
    for key, cfg in PLATFORMS.items():
        print(f"[{cfg['name']}] 提取 Cookie...")
        all_cookies = []
        for domain in cfg["domains"]:
            found = extract_cookies(domain)
            print(f"  域名 {domain}: {len(found)} 个 Cookie")
            all_cookies.extend(found)

        # 去重
        seen = {}
        unique = []
        for c in all_cookies:
            if c["name"] not in seen:
                seen[c["name"]] = True
                unique.append(c)

        result = {
            "platform": key,
            "name": cfg["name"],
            "extracted_at": datetime.now().isoformat(),
            "cookie_count": len(unique),
            "cookies": unique,
            "cookie_header": format_cookies_for_requests(unique),
        }

        with open(cfg["cookie_file"], "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"  ✅ 保存到: {cfg['cookie_file']}")
        print(f"  ✅ 共 {len(unique)} 个 Cookie")
        results[key] = result
        print()

    print("=" * 55)
    print("  ✅ 提取完成！")
    print()
    for key, cfg in PLATFORMS.items():
        r = results[key]
        status = f"✅ {r['cookie_count']} Cookie" if r["cookie_count"] > 0 else "⚠️ 0 Cookie（可能Chrome未登录）"
        print(f"  {cfg['name']}: {status}")
    print()
    print("  Cookie 文件已保存到 data/ 目录")
    print("  运行 python collectors/run.py 即可使用 Cookie 采集数据")


if __name__ == "__main__":
    main()
