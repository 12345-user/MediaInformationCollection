# -*- coding: utf-8 -*-
"""
streamlit_app.py — 创作者流量监控系统 v2
直接从 SQLite 数据库读取，逻辑简化
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px

# ========== 数据库路径 ==========
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "metrics.db"

# ========== 配置 ==========
st.set_page_config(
    page_title="创作者流量监控",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background-color: #0f1117; color: #e0e0e0; }
h1, h2, h3 { color: #ffffff; }
div[data-testid="stMetricValue"] { color: #4fd1c5; font-size: 2em; }
</style>
""", unsafe_allow_html=True)


# ========== 数据加载 ==========
def get_db_creators():
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM creators ORDER BY platform, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_db_videos(creator_id=None):
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    if creator_id:
        rows = conn.execute(
            "SELECT * FROM videos WHERE creator_id=? ORDER BY collected_at DESC",
            (creator_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM videos ORDER BY collected_at DESC LIMIT 1000"
        ).fetchall()
    conn.close()
    result = [dict(r) for r in rows]
    # 写日志到文件，方便排查
    log_path = BASE_DIR / "debug_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] get_db_videos called, creator_id={creator_id}, returned {len(result)} videos\n")
        for r in result[:3]:
            f.write(f"  sample: {r.get('creator_id')} | {str(r.get('title',''))[:30]}\n")
    return result


# ========== 主程序 ==========
creators = get_db_creators()
all_videos = get_db_videos()

st.title("🚨 创作者流量实时监控")
st.caption(f"数据时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 数据库视频: {len(all_videos)} 条 · 创作者: {len(creators)} 位")

# 调试信息（直接显示在顶部）
debug_info = {
    "DB视频总数": len(all_videos),
    "DB创作者": [(c["id"], c["name"], c["platform"]) for c in creators[:6]],
    "视频creator_id样本": list(set(v.get("creator_id","") for v in all_videos[:20])),
}
with st.expander("🔧 调试信息"):
    st.write(debug_info)

# 侧边栏
with st.sidebar:
    st.title("📊 配置")

    # 平台选择
    platforms = ["全部"] + sorted(set(c.get("platform","") for c in creators))
    sel_platform = st.selectbox("平台", platforms)

    # 博主选择
    filtered_creators = [c for c in creators if sel_platform == "全部" or c.get("platform") == sel_platform]
    creator_names = [c["name"] for c in filtered_creators]
    sel_creator = st.selectbox("博主", ["全部"] + creator_names)

    # 时间范围
    days = st.slider("时间范围（天）", 7, 90, 30)

    # 刷新按钮
    if st.button("🔄 清除缓存刷新"):
        st.cache_data.clear()
        st.rerun()

# 过滤视频
filtered_videos = all_videos
if sel_creator != "全部":
    cid_map = {c["name"]: c["id"] for c in creators}
    sel_id = cid_map.get(sel_creator, "")
    filtered_videos = [v for v in filtered_videos if v.get("creator_id") == sel_id]
elif sel_platform != "全部":
    # 平台过滤：creator_id → platform 映射
    cid_to_platform = {c["id"]: c["platform"] for c in creators}
    filtered_videos = [v for v in filtered_videos
                       if cid_to_platform.get(v.get("creator_id","")) == sel_platform]

# 创建 DataFrame
df = pd.DataFrame(filtered_videos) if filtered_videos else pd.DataFrame()

# ========== 概览 ==========
st.markdown("## 📈 概览")
if not df.empty and "views" in df.columns:
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("👁 总播放", f"{int(df['views'].sum()):,}")
    with col2: st.metric("❤️ 总点赞", f"{int(df['likes'].sum()):,}")
    with col3: st.metric("💬 总评论", f"{int(df['comments'].sum()):,}")
    with col4: st.metric("🎬 视频数", len(df))
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("👁 总播放", "暂无" if df.empty else f"{int(df['likes'].sum()):,}")
    with col2: st.metric("❤️ 总点赞", f"{int(df['likes'].sum()):,}" if not df.empty else "暂无")
    with col3: st.metric("💬 总评论", f"{int(df['comments'].sum()):,}" if not df.empty else "暂无")
    with col4: st.metric("🎬 视频数", len(df))

# ========== 图表 ==========
if not df.empty:
    # 平台分布
    cid_to_platform = {c["id"]: c["platform"] for c in creators}
    df["平台"] = df["creator_id"].map(cid_to_platform).fillna("其他")

    if "views" in df.columns and df["views"].sum() > 0:
        col_a, col_b = st.columns(2)
        with col_a:
            grp = df.groupby("平台")["views"].sum().reset_index()
            fig1 = px.bar(grp, x="平台", y="views", title="各平台播放量",
                          color="平台",
                          color_discrete_map={"抖音": "#ff6b6b", "douyin": "#ff6b6b",
                                           "B站": "#4ecdc4", "bilibili": "#4ecdc4",
                                           "小红书": "#ffe66d"})
            fig1.update_layout(plot_bgcolor="#1a1d27", paper_bgcolor="#0f1117",
                             font_color="#e0e0e0", showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        with col_b:
            fig2 = px.pie(grp, names="平台", values="views", title="播放量占比", hole=0.4,
                          color="平台",
                          color_discrete_map={"抖音": "#ff6b6b", "douyin": "#ff6b6b",
                                           "B站": "#4ecdc4", "bilibili": "#4ecdc4",
                                           "小红书": "#ffe66d"})
            fig2.update_layout(plot_bgcolor="#1a1d27", paper_bgcolor="#0f1117", font_color="#e0e0e0")
            st.plotly_chart(fig2, use_container_width=True)

    # ========== 视频列表 ==========
    st.markdown(f"### 📋 视频列表 ({len(df)} 条)")

    if not df.empty:
        # 选择要显示的列
        col_map = {"title": "标题", "likes": "点赞", "comments": "评论",
                   "shares": "转发", "views": "播放", "publish_date": "发布时间",
                   "creator_id": "账号ID", "collected_at": "采集时间"}
        show_cols = [c for c in ["title", "likes", "comments", "shares", "views", "publish_date"] if c in df.columns]
        if show_cols:
            disp = df[show_cols].copy()
            disp.columns = [col_map.get(c, c) for c in disp.columns]
            # 格式化数字
            for col in ["点赞", "评论", "转发", "播放"]:
                if col in disp.columns:
                    disp[col] = disp[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
            st.dataframe(disp.head(30), use_container_width=True, hide_index=True)

# ========== 博主详情 ==========
if sel_creator != "全部":
    sel_c = next((c for c in creators if c["name"] == sel_creator), None)
    if sel_c:
        st.markdown(f"### 👤 {sel_c['name']} 详情")
        c1, c2, c3, c4 = st.columns(4)
        creator_videos = [v for v in all_videos if v.get("creator_id") == sel_c["id"]]
        with c1: st.metric("平台", sel_c.get("platform","?"))
        with c2: st.metric("视频数", len(creator_videos))
        with c3: st.metric("UID", str(sel_c.get("uid",""))[:12])
        with c4: st.metric("总点赞", f"{int(sum(v.get('likes',0) for v in creator_videos)):,}")

st.markdown("---")
st.caption(f"🚀 创作者流量监控系统 · 共 {len(creators)} 位博主 · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
