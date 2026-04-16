# 🚀 创作者流量监控系统

> 多平台（抖音 / 小红书 / B站）博主作品流量实时监控 + 可视化网站

**本地部署 + GitHub 免费托管（Streamlit Cloud）**

---

## 系统架构

```
本地 PC（Cron 每6小时）
  └─ collectors/run.py
       ├─ bilibili.py（bili CLI）
       ├─ douyin.py（Web API）
       └─ xiaohongshu.py（xhs CLI）
  └─ database/db.py（SQLite）
       └─ data/latest_data.json（推送到 GitHub）

GitHub Actions（每6小时自动采集）
  └─ 同步 latest_data.json 到 main 分支

GitHub（Streamlit Cloud 自动部署）
  └─ dashboard/app.py → https://你的用户名-你的应用名.streamlit.app
```

---

## 目录结构

```
creator-monitor/
├── creators.json           # 博主配置（修改这里添加博主）
├── requirements.txt
├── .streamlit/config.toml
├── .github/workflows/collect.yml  # GitHub Actions 自动采集
├── database/
│   └── db.py              # SQLite 数据库操作
├── collectors/
│   ├── bilibili.py        # B站数据采集
│   ├── douyin.py          # 抖音数据采集
│   ├── xiaohongshu.py     # 小红书数据采集
│   └── run.py              # 主采集脚本
├── data/                  # 数据存储目录
│   ├── metrics.db          # SQLite 数据库（本地）
│   └── latest_data.json    # GitHub 同步数据
└── dashboard/
    └── app.py             # Streamlit 可视化网站
```

---

## 快速开始

### 1. 本地运行

```bash
cd D:\Tools\creator-monitor
pip install -r requirements.txt

# 首次：初始化数据库
python -c "from database.db import init_db; init_db()"

# 采集数据
python collectors/run.py

# 启动本地监控网站
streamlit run dashboard/app.py
# 访问 http://localhost:8501
```

### 2. GitHub 部署（免费）

**Step 1**: 在 GitHub 创建新仓库，上传本项目代码

**Step 2**: 登录 [Streamlit Cloud](https://streamlit.io/cloud)
- 连接你的 GitHub 仓库
- 选择 `dashboard/app.py` 作为主文件
- 填写 `requirements.txt` 路径
- 点击 **Deploy!**

**Step 3**: 获取免费 URL
```
https://你的用户名-你的项目名.streamlit.app
```

**Step 4**: 自动更新（可选）
- 在 GitHub Actions 中启用 `collect.yml`
- 设置仓库 secrets（如果需要 Cookie）
- 每天自动采集数据并更新显示

---

## 添加博主

编辑 `creators.json`：

```json
{
  "id": "自定义唯一ID",
  "name": "博主名称",
  "platform": "douyin | bilibili | xiaohongshu",
  "uid": "平台用户ID",
  "topic": "内容领域",
  "style": "内容风格"
}
```

---

## 定时采集（Cron）

在 OpenClaw 中添加 Cron 任务：

```python
# 每6小时采集一次
cron.add(
  name="创作者流量采集",
  schedule={"kind": "cron", "expr": "0 8,14,20 * * *", "tz": "Asia/Shanghai"},
  payload={"kind": "agentTurn",
           "message": "执行创作者数据采集：python collectors/run.py",
           "model": "minimax/MiniMax-M2.5"},
  sessionTarget="isolated",
)
```

---

## 功能特性

| 功能 | 状态 |
|------|------|
| 多平台监控（抖音/小红书/B站） | ✅ |
| 播放量/点赞/评论/转发追踪 | ✅ |
| 30天趋势图 | ✅ |
| 各平台对比分析 | ✅ |
| 最新视频动态 | ✅ |
| 博主详情页 | ✅ |
| 本地 Streamlit 部署 | ✅ |
| Streamlit Cloud 免费托管 | ✅ |
| GitHub Actions 自动采集 | ✅ |
| SQLite 本地持久化 | ✅ |
| GitHub 数据同步 | ✅ |

---

## 平台说明

| 平台 | 采集方式 | 说明 |
|------|---------|------|
| **B站** | bili CLI（官方工具） | 最稳定，直接获取所有数据 |
| **抖音** | Web API + 搜索 | 公开数据可能被限流，建议配置 Cookie |
| **小红书** | xhs CLI | 需要登录 Cookie（agent-reach） |

---

## 配置 Cookie（如需）

如果抖音/小红书采集受限，在 `creators.json` 同目录创建 `config.json`：

```json
{
  "douyin_cookie": "你的抖音Cookie",
  "xiaohongshu_cookie": "你的小红书Cookie"
}
```
