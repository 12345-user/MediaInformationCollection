# -*- coding: utf-8 -*-
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.douyin.com/",
}

# 测试抖音sec_uid（陈师傅路亚）
sec_uid = "MS4wLjABAAAAIaxl8QfBDEg6mEKha4dKNXM8JxtQQXADYHBmTYSvgNk"

print("=== Test 1: Web API ===")
try:
    url = f"https://www.douyin.com/aweme/v1/web/aweme/post/?sec_uid={sec_uid}&count=5&max_cursor=0&cookie_enabled=false"
    r = requests.get(url, headers=headers, timeout=15)
    print("Status:", r.status_code, "len:", len(r.text))
    if r.text.strip().startswith("{"):
        data = r.json()
        print("Keys:", list(data.keys())[:5])
        awemes = data.get("aweme_list", [])
        print("Videos:", len(awemes))
        for a in awemes[:2]:
            print(" -", a.get("desc","?")[:50], "| play:", a.get("statistics",{}).get("play_count",0))
    else:
        print("Response:", r.text[:200])
except Exception as e:
    print("Error:", e)

print()
print("=== Test 2: User Profile HTML ===")
try:
    url2 = f"https://www.douyin.com/user/{sec_uid}"
    r2 = requests.get(url2, headers=headers, timeout=15)
    print("Status:", r2.status_code, "len:", len(r2.text))
    # 找视频数据
    matches = re.findall(r'"aweme_id"\s*:\s*"(\d+)"', r2.text)
    print("aweme_id matches:", len(matches), matches[:5])
    # 找标题
    titles = re.findall(r'"desc"\s*:\s*"([^"]{5,100})"', r2.text)
    print("Titles:", titles[:5])
except Exception as e:
    print("Error:", e)

print()
print("=== Test 3: 数字UID 25424815218 ===")
try:
    url3 = "https://www.douyin.com/aweme/v1/web/aweme/post/?sec_uid=25424815218&count=5&max_cursor=0&cookie_enabled=false"
    r3 = requests.get(url3, headers=headers, timeout=15)
    print("Status:", r3.status_code, "len:", len(r3.text))
    if r3.text.strip().startswith("{"):
        data3 = r3.json()
        print("Keys:", list(data3.keys())[:5])
        print("aweme_list:", len(data3.get("aweme_list", [])))
except Exception as e:
    print("Error:", e)
