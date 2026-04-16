# 创作者流量监控系统

> 多平台博主作品实时监控 + 数据可视化

---

## 快速开始

### 1. 本地运行

```bash
cd D:\Tools\creator-monitor

# 安装依赖
pip install -r requirements.txt

# 启动监控网站
streamlit run streamlit_app.py
# 访问 http://localhost:8501
```

### 2. GitHub 部署

1. 上传代码到 GitHub 仓库
2. 登录 https://streamlit.io/cloud
3. 选择仓库 + `streamlit_app.py` → Deploy

---

## 获取 Cookie（抖音/小红书必读）

### 为什么要 Cookie？

B站：✅ 无需 Cookie，直接采集
抖音：❌ 需要登录 Cookie
小红书：❌ 需要登录 Cookie

### 步骤

**Step 1：关闭 Chrome 浏览器**（重要！否则 Cookie 数据库被锁）

**Step 2：运行 Cookie 提取工具**
```bash
python get_cookies.py
```

**Step 3：重启 Chrome，回到抖音/小红书重新登录**

**Step 4：再次运行 `get_cookies.py`**
```bash
python get_cookies.py
```
Cookie 自动保存到 `data/douyin_cookies.json` 和 `data/xiaohongshu_cookies.json`

### 提供 UID

还需要提供各平台的用户 ID：
- **抖音 UID**：抖音APP → 个人主页 → 分享 → 复制链接，链接里的数字
- **小红书 UID**：小红书APP → 个人主页 → 分享 → 复制链接，获取主页 URL 中的用户ID

---

## 添加博主

编辑 `creators.json`：
```json
{
  "id": "自定义ID",
  "name": "博主名称",
  "platform": "bilibili | douyin | xiaohongshu",
  "uid": "平台用户ID",
  "topic": "内容领域",
  "style": "内容风格"
}
```

---

## 定时采集

本地自动采集（每天 8:00 / 14:00 / 20:00）：
- Cron 任务已配置在 OpenClaw

GitHub Actions 自动采集（云端，每6小时）：
- 推送代码后自动启用

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `streamlit_app.py` | Streamlit Cloud 入口 |
| `dashboard/app.py` | 完整 Dashboard |
| `collectors/run.py` | 主采集脚本 |
| `collectors/bilibili.py` | B站采集（无需 Cookie） |
| `collectors/douyin.py` | 抖音采集（需要 Cookie） |
| `collectors/xiaohongshu.py` | 小红书采集（需要 Cookie） |
| `database/db.py` | SQLite 数据库 |
| `get_cookies.py` | Cookie 自动提取工具 |
| `creators.json` | 博主配置 |
| `data/*.json` | Cookie 和数据文件 |
