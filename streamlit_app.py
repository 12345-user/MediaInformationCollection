# -*- coding: utf-8 -*-
"""
streamlit_app.py — 创作者流量监控系统
Streamlit Cloud 部署入口
本地: streamlit run streamlit_app.py
"""
import sys, json
from pathlib import Path
from datetime import datetime, timedelta

# 加载内嵌数据（B站采集的23个视频）
try:
    from _embedded_data import EMBEDDED_DATA
    CLOUD_DATA = EMBEDDED_DATA
except ImportError:
    CLOUD_DATA = None

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="创作者流量监控",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========== 数据库兼容路径 ==========
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "metrics.db"
GITHUB_DATA = BASE_DIR / "data" / "latest_data.json"
CREATORS_FILE = BASE_DIR / "creators.json"

# ========== 样式 ==========
st.markdown("""
<style>
.stApp { background-color: #0f1117; color: #e0e0e0; }
h1, h2, h3 { color: #ffffff; }
div[data-testid="stMetricValue"] { color: #4fd1c5; font-size: 2em; }
</style>
""", unsafe_allow_html=True)

# ========== 数据加载 ==========
@st.cache_data(ttl=3600)
def load_github_data():
    """优先用内嵌数据，其次用本地JSON文件"""
    if CLOUD_DATA:
        return CLOUD_DATA
    if GITHUB_DATA.exists():
        try:
            return json.loads(GITHUB_DATA.read_text(encoding="utf-8"))
        except:
            pass
    return None

@st.cache_data(ttl=3600)
def load_creators_config():
    if CREATORS_FILE.exists():
        try:
            return json.loads(CREATORS_FILE.read_text(encoding="utf-8")).get("creators", [])
        except:
            pass
    return []

def get_db_videos():
    """从 SQLite 读取数据（移除30天限制，读取全部）"""
    try:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute(
            "SELECT * FROM videos ORDER BY collected_at DESC LIMIT 1000"
        ).fetchall()
        conn.close()
        result = [dict(r) for r in rows]
        return result
    except Exception as e:
        return []

def get_db_creators():
    try:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute("SELECT * FROM creators").fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except:
        return []

def get_db_daily():
    try:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        rows = c.execute("""
            SELECT d.date, d.creator_id, c.name, c.platform,
                   SUM(d.views) as total_views, SUM(d.likes) as total_likes,
                   COUNT(DISTINCT d.video_id) as video_count
            FROM daily_stats d
            JOIN creators c ON d.creator_id = c.id
            WHERE d.date>=?
            GROUP BY d.date, d.creator_id
            ORDER BY d.date, total_views DESC
        """, (cutoff,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except:
        return []

# ========== 主程序 ==========
def main():
    st.title("🚨 创作者流量实时监控")
    st.caption(f"数据更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 加载数据
    creators_cfg = load_creators_config()
    data = load_github_data()
    db_videos = get_db_videos()
    db_creators = get_db_creators()
    db_daily = get_db_daily()

    # 合并数据源
    all_creators = db_creators or [{"id": c["id"], "name": c["name"], "platform": c["platform"]} for c in creators_cfg]
    all_videos = db_videos
    if not all_videos and data:
        all_videos = data.get("recent_videos", [])

    # 侧边栏过滤
    with st.sidebar:
        st.title("📊 配置")
        platforms = ["全部"] + list(set(c.get("platform","") for c in all_creators))
        sel_platform = st.selectbox("平台", platforms)
        creator_names = [c["name"] for c in all_creators
                        if sel_platform == "全部" or c.get("platform") == sel_platform]
        sel_creator = st.selectbox("博主", ["全部"] + creator_names)
        days = st.slider("时间范围（天）", 7, 90, 30)
        if st.button("🔄 刷新"):
            st.cache_data.clear()
            st.rerun()

    # 过滤（支持中文平台名）
    filtered_v = all_videos
    # 平台名映射：统一大小写
    platform_aliases = {
        '抖音': ['抖音', 'douyin'],
        'B站': ['B站', 'bilibili'],
        '小红书': ['小红书', 'xiaohongshu'],
    }
    def match_platform(c_platform, sel):
        if sel == '全部': return True
        for alias in platform_aliases.get(sel, [sel]):
            if c_platform == alias:
                return True
        return c_platform == sel

    if sel_platform != "全部":
        cid_map = {c["id"]: c["platform"] for c in all_creators}
        filtered_v = [v for v in filtered_v
                     if match_platform(cid_map.get(v.get("creator_id",""), ""), sel_platform)]
    if sel_creator != "全部":
        cid_map = {c["name"]: c["id"] for c in all_creators}
        cid = cid_map.get(sel_creator, "")
        filtered_v = [v for v in filtered_v if v.get("creator_id","") == cid]

    df = pd.DataFrame(filtered_v) if filtered_v else pd.DataFrame()

    # ========== 概览 ==========
    st.markdown("## 📈 概览")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👁 总播放", f"{int(df['views'].sum()):,}" if not df.empty and "views" in df else "暂无")
    with col2:
        st.metric("❤️ 总点赞", f"{int(df['likes'].sum()):,}" if not df.empty and "likes" in df else "暂无")
    with col3:
        st.metric("💬 总评论", f"{int(df['comments'].sum()):,}" if not df.empty and "comments" in df else "暂无")
    with col4:
        st.metric("🎬 监控博主", len(all_creators))

    # ========== 图表 ==========
    if not df.empty and "views" in df.columns:
        col_a, col_b = st.columns(2)
        with col_a:
            platform_map = {c["id"]: c["platform"] for c in all_creators}
            df["平台"] = df["creator_id"].map(platform_map).fillna("其他")
            grp = df.groupby("平台")["views"].sum().reset_index()
            fig1 = px.bar(grp, x="平台", y="views", title="各平台播放量",
                          color="平台",
                          color_discrete_map={"抖音": "#ff6b6b", "douyin": "#ff6b6b", "B站": "#4ecdc4", "bilibili": "#4ecdc4", "小红书": "#ffe66d", "xiaohongshu": "#ffe66d"})
            fig1.update_layout(plot_bgcolor="#1a1d27", paper_bgcolor="#0f1117",
                             font_color="#e0e0e0", showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        with col_b:
            fig2 = px.pie(grp, names="平台", values="views", title="播放量占比", hole=0.4,
                          color="平台",
                          color_discrete_map={"抖音": "#ff6b6b", "douyin": "#ff6b6b", "B站": "#4ecdc4", "bilibili": "#4ecdc4", "小红书": "#ffe66d", "xiaohongshu": "#ffe66d"})
            fig2.update_layout(plot_bgcolor="#1a1d27", paper_bgcolor="#0f1117", font_color="#e0e0e0")
            st.plotly_chart(fig2, use_container_width=True)

    # ========== 最新视频 ==========
    st.markdown("### 🆕 最新视频动态")
    if not df.empty:
        show_cols = [c for c in ["title", "views", "likes", "comments", "publish_date"] if c in df.columns]
        if show_cols:
            disp = df[show_cols].copy()
            disp.columns = [c.capitalize() for c in disp.columns]
            st.dataframe(disp.head(20), use_container_width=True, hide_index=True)

    # ========== 博主列表 ==========
    st.markdown("### 👤 博主列表")
    if all_creators:
        for c in all_creators:
            with st.expander(f"{c['name']} ({c.get('platform','?')})"):
                cv = [v for v in filtered_v if v.get("creator_id") == c["id"]]
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("播放", f"{int(sum(v.get('views',0) for v in cv)):,}" if cv else "0")
                with c2:
                    st.metric("点赞", f"{int(sum(v.get('likes',0) for v in cv)):,}" if cv else "0")
                with c3:
                    st.metric("视频数", len(cv))

    # ========== 页脚 ==========
    st.markdown("---")
    src = "GitHub同步" if GITHUB_DATA.exists() else "本地数据库"
    st.caption(f"🚀 创作者流量监控系统 · {src} · 共监控 {len(all_creators)} 位博主 · {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()
