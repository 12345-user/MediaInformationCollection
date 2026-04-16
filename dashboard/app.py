# -*- coding: utf-8 -*-
"""
dashboard/app.py - Streamlit 可视化监控网站
本地运行：streamlit run dashboard/app.py
Streamlit Cloud: 部署此文件到 GitHub，自动同步
"""
import sys, json
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 添加项目路径
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import (
    init_db, get_all_creators, get_recent_videos,
    get_all_trends, get_daily_trend, export_to_json,
)

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
.stDataFrame { color: #e0e0e0; }
.css-1d391kg { background-color: #1a1d27; }
h1, h2, h3 { color: #ffffff; }
.metric-card { background: #1a1d27; border-radius: 10px; padding: 15px; text-align: center; }
div[data-testid="stMetricValue"] { color: #4fd1c5; font-size: 2em; }
</style>
""", unsafe_allow_html=True)


# ========== 数据加载 ==========
@st.cache_data(ttl=3600)
def load_data():
    init_db()
    creators = get_all_creators()
    recent = get_recent_videos(days=30)
    trends = get_all_trends(days=30)
    return creators, recent, trends


def load_github_data():
    """从 GitHub 同步的 JSON 加载数据（Streamlit Cloud 读取）"""
    github_file = BASE_DIR / "data" / "latest_data.json"
    if github_file.exists():
        try:
            data = json.loads(github_file.read_text(encoding="utf-8"))
            return data
        except:
            pass
    return None


# ========== 侧边栏 ==========
with st.sidebar:
    st.title("📊 配置")
    st.markdown("---")

    creators, recent, trends = load_data()
    platforms = ["全部"] + list(set(c["platform"] for c in creators))
    selected_platform = st.selectbox("选择平台", platforms)

    creator_options = [c["name"] for c in creators
                       if selected_platform == "全部" or c["platform"] == selected_platform]
    selected_creator = st.selectbox("选择创作者", ["全部"] + creator_options)

    days = st.slider("时间范围（天）", 7, 90, 30)

    st.markdown("---")
    st.caption(f"数据更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if st.button("🔄 刷新数据"):
        st.cache_data.clear()
        st.rerun()


# ========== 过滤数据 ==========
def filter_creators(creators, platform, name):
    result = creators
    if platform != "全部":
        result = [c for c in result if c["platform"] == platform]
    if name != "全部":
        result = [c for c in result if c["name"] == name]
    return result


filtered = filter_creators(creators, selected_platform, selected_creator)
filtered_ids = [c["id"] for c in filtered]

recent_df = pd.DataFrame([v for v in recent if v["creator_id"] in filtered_ids])
if not recent_df.empty:
    recent_df["collect_dt"] = pd.to_datetime(recent_df.get("collected_at", ""))
    recent_df = recent_df.sort_values("collect_dt", ascending=False)

trends_df = pd.DataFrame([t for t in trends if t["creator_id"] in filtered_ids])
if not trends_df.empty:
    trends_df["date_dt"] = pd.to_datetime(trends_df.get("date", ""))
    trends_df = trends_df.sort_values("date_dt")


# ========== 主页 ==========
st.title("🚨 创作者流量实时监控")
st.caption("多平台 · 多博主 · 趋势追踪 · 实时可视化")

# ---- 概览指标 ----
st.markdown("## 📈 概览")

col1, col2, col3, col4 = st.columns(4)
total_views = int(recent_df["views"].sum()) if not recent_df.empty else 0
total_likes = int(recent_df["likes"].sum()) if not recent_df.empty else 0
total_comments = int(recent_df["comments"].sum()) if not recent_df.empty else 0
creator_count = len(filtered)
video_count = len(recent_df)

with col1:
    st.metric("👁 总播放", f"{total_views:,}" if total_views > 0 else "暂无数据")
with col2:
    st.metric("❤️ 总点赞", f"{total_likes:,}" if total_likes > 0 else "暂无数据")
with col3:
    st.metric("💬 总评论", f"{total_comments:,}" if total_comments > 0 else "暂无数据")
with col4:
    st.metric("🎬 监控博主", creator_count)

st.markdown("---")


# ========== 平台分布 ==========
if not recent_df.empty and "views" in recent_df.columns:
    st.markdown("### 📱 平台播放量分布")

    # 图1: 各平台总播放量
    col_a, col_b = st.columns(2)
    with col_a:
        if "creator_id" in recent_df.columns and not recent_df.empty:
            creator_map = {c["id"]: c["name"] for c in creators}
            platform_map = {c["id"]: c["platform"] for c in creators}
            recent_df["platform_label"] = recent_df["creator_id"].map(platform_map)
            platform_stats = recent_df.groupby("platform_label")[["views", "likes", "comments"]].sum().reset_index()

            fig1 = px.bar(
                platform_stats,
                x="platform_label",
                y="views",
                color="platform_label",
                title="各平台总播放量",
                color_discrete_map={"douyin": "#ff6b6b", "bilibili": "#4ecdc4", "xiaohongshu": "#ffe66d"},
            )
            fig1.update_layout(
                plot_bgcolor="#1a1d27",
                paper_bgcolor="#1a1d27",
                font_color="#e0e0e0",
                showlegend=False,
            )
            st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        if not platform_stats.empty:
            fig2 = px.pie(
                platform_stats,
                names="platform_label",
                values="views",
                title="播放量占比",
                color="platform_label",
                color_discrete_map={"douyin": "#ff6b6b", "bilibili": "#4ecdc4", "xiaohongshu": "#ffe66d"},
            )
            fig2.update_layout(
                plot_bgcolor="#1a1d27",
                paper_bgcolor="#1a1d27",
                font_color="#e0e0e0",
            )
            st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")


# ========== 趋势图 ==========
st.markdown("### 📈 播放趋势（30天）")

if not trends_df.empty and "date_dt" in trends_df.columns:
    tab1, tab2 = st.tabs(["总播放趋势", "各博主对比"])

    with tab1:
        fig3 = px.line(
            trends_df.groupby("date_dt")[["total_views", "total_likes", "total_comments"]].sum().reset_index(),
            x="date_dt",
            y="total_views",
            title="每日总播放量趋势",
            markers=True,
        )
        fig3.update_layout(
            plot_bgcolor="#1a1d27",
            paper_bgcolor="#1a1d27",
            font_color="#e0e0e0",
            xaxis=dict(showgrid=True, gridcolor="#2a2d37"),
            yaxis=dict(showgrid=True, gridcolor="#2a2d37"),
        )
        st.plotly_chart(fig3, use_container_width=True)

    with tab2:
        # 各博主播放趋势
        if "name" in trends_df.columns:
            fig4 = px.line(
                trends_df,
                x="date_dt",
                y="total_views",
                color="name",
                title="各博主播放量对比",
                markers=True,
            )
            fig4.update_layout(
                plot_bgcolor="#1a1d27",
                paper_bgcolor="#1a1d27",
                font_color="#e0e0e0",
                xaxis=dict(showgrid=True, gridcolor="#2a2d37"),
                yaxis=dict(showgrid=True, gridcolor="#2a2d37"),
            )
            st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("暂无趋势数据，请先运行采集脚本收集数据")


# ========== 最新视频 ==========
st.markdown("### 🆕 最新视频动态")

if not recent_df.empty:
    display_cols = ["title", "creator_id", "views", "likes", "comments", "publish_date", "collect_dt"]
    existing_cols = [c for c in display_cols if c in recent_df.columns]
    df_show = recent_df[existing_cols].copy()

    creator_map = {c["id"]: c["name"] for c in creators}
    platform_map = {c["id"]: c["platform"] for c in creators}

    if "creator_id" in df_show.columns:
        df_show["博主"] = df_show["creator_id"].map(creator_map).fillna(df_show["creator_id"])
        df_show["平台"] = df_show["creator_id"].map(platform_map).fillna("")
        # 调整列顺序
        cols = ["title", "博主", "平台", "views", "likes", "comments", "publish_date"]
        cols = [c for c in cols if c in df_show.columns]
        df_show = df_show[cols]
        df_show.columns = ["标题", "博主", "平台", "播放", "点赞", "评论", "发布时间"]

    st.dataframe(
        df_show.head(20),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("暂无视频数据")


# ========== 博主详情 ==========
st.markdown("### 👤 博主详情")

if filtered:
    for creator in filtered:
        with st.expander(f"{creator['name']} ({creator['platform']})"):
            cid = creator["id"]
            creator_videos = [v for v in recent if v.get("creator_id") == cid]
            if creator_videos:
                df_c = pd.DataFrame(creator_videos)
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("播放", f"{int(df_c['views'].sum()):,}")
                with c2:
                    st.metric("点赞", f"{int(df_c['likes'].sum()):,}")
                with c3:
                    st.metric("评论", f"{int(df_c['comments'].sum()):,}")
                with c4:
                    st.metric("视频数", len(df_c))

                if len(df_c) > 1:
                    fig5 = px.bar(
                        df_c.head(5),
                        x="title",
                        y="views",
                        title=f"{creator['name']} 最新视频播放量",
                        color="likes",
                    )
                    fig5.update_layout(
                        plot_bgcolor="#1a1d27",
                        paper_bgcolor="#1a1d27",
                        font_color="#e0e0e0",
                        xaxis_tickangle=-30,
                    )
                    st.plotly_chart(fig5, use_container_width=True)


# ========== 页脚 ==========
st.markdown("---")
st.caption(
    f"🚀 创作者流量监控系统 · 数据更新于 {datetime.now().strftime('%Y-%m-%d %H:%M')} · "
    f"共监控 {len(creators)} 位博主 · GitHub 同步版"
)
