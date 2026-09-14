# ⚔️ 代码冒险者 · 软件工程游戏化 AI 问答系统

> 面向「在校学生 + 求职应届生」的软件工程专属游戏化 AI 学习问答系统（MVP 落地版）
> 基于《软件工程游戏化AI智能问答系统 专项设计方案》开发，覆盖 P0 核心闭环 + P1 核心玩法。

**边玩边学、边练边面**：注册 → 选择职业分支 → 关卡闯关 → AI 导师对话 → 获得奖励 → 升级，最终拿到「虚拟 Offer」。

---

## ✨ 功能总览

| 模块 | 说明 | 优先级 |
|---|---|---|
| 🧙 角色系统 | 5 大职业分支（前端法师/后端战士/算法刺客/测试牧师/运维骑士），等级 1~100，称号体系（实习生→架构师） | P0 |
| 🗺️ 关卡地图 | 9 大场景 · 21 个关卡（新手村→数据结构森林→算法峡谷→…→架构师王座），L1~L5 难度分级 | P0 |
| 🎯 知识闯关 | 每关 10 题（选择/填空/简答/编程），3 条命，答错即时 AI 解析，通关掉经验/代码币 | P0 |
| 💬 AI 导师对话 | 6 位导师角色，RAG 知识库检索增强，支持连续追问/写代码/画流程图/考点总结 | P0 |
| 📕 错题本 | 答题错误自动收录，错因归类（概念不清/计算错误/思路偏差），支持重刷 | P0 |
| 📊 个人中心 | 成就墙（15 个）、能力雷达图、学习数据、每日任务、排行榜 | P0 |
| 📋 游戏化体系 | EXP/代码币/生命值/成就徽章/每日任务/签到/排行榜（总榜·周榜·方向榜） | P0 |
| 🐛 Bug 猎人 | 9 道 Python 找 Bug 挑战（语法/逻辑/性能/安全），提交修复实时运行验证，排行榜 | P1 |
| 🎤 面试闯关 | 一面基础→二面深度→三面主管→HR面 四轮，四维评分（技术/逻辑/表达/STAR），完整面试报告 + 虚拟 Offer | P1 |
| 🖥️ 代码运行 | 在线运行 Python（本地演示沙箱，生产可替换 Judge0） | P1 |

## 🏗️ 技术架构

```
前端  React 19 + TypeScript + Tailwind CSS + Ant Design 5 + Framer Motion + ECharts
后端  FastAPI (Python 3.12) + SQLAlchemy 2.0
数据库 MySQL 8.0（用户/题库/业务数据） + Redis（排行榜缓存，降级为 DB 计算）
AI     OpenAI 兼容协议（豆包 / DeepSeek / 通义千问）+ RAG 检索增强（无 Key 自动进入离线演示模式）
沙箱  Python 子进程（超时/体积/危险模块黑名单，开发演示用）
```

### 目录结构

```
SoftwareEngineeringWebsite/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── config.py        # 配置（.env）
│   │   ├── models.py        # ORM 模型（18 张表）
│   │   ├── schemas.py       # Pydantic 模型
│   │   ├── ai/client.py     # AI 客户端（含离线降级 + RAG-lite）
│   │   ├── services/        # 成长体系/闯关/代码沙箱
│   │   ├── routers/         # 9 组 API 路由
│   │   └── seed/            # 种子数据（题库 73 题/21 关/9 Bug/20 面试题/15 成就/20 知识条目）
│   ├── .env                 # 环境配置
│   ├── requirements.txt
│   ├── run.py               # 启动入口
│   └── smoke_test.py        # API 冒烟测试脚本
└── frontend/                # React 前端
    └── src/
        ├── pages/           # 9 个页面（登录/引导/首页/地图/闯关/对话/面试/Bug/个人中心）
        ├── components/      # 布局、HUD
        ├── api/             # API 客户端
        └── store/           # 认证状态
```

## 🚀 快速启动

### 0. 环境要求

- Python 3.12 + MySQL 8.0（默认 root/root，可用 `.env` 修改）
- Node.js 18+（推荐 20+）

### 1. 后端

```bash
cd backend

# （可选）创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖（国内加速：清华源）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 初始化数据库（自动建库建表 + 种子数据）
# 1) 手动创建数据库（或直接改 .env 用已有库）：
mysql -uroot -proot -e "CREATE DATABASE IF NOT EXISTS code_adventurer DEFAULT CHARACTER SET utf8mb4"

# 2) 启动服务（首次启动自动建表并写入种子数据）
python run.py
# 或：python -m uvicorn app.main:app --reload
```

启动后：API 文档 http://127.0.0.1:8000/docs

### 2. 前端

```bash
cd frontend

# 安装依赖（国内加速：npmmirror）
npm install --registry=https://registry.npmmirror.com

# 开发模式（已配置 /api 代理到后端 8000 端口）
npm run dev
```

浏览器访问 http://localhost:5173

### 3. 接入真实 AI（可选）

默认「离线演示模式」：内置规则引擎 + 20 条知识库，全部玩法可跑通、零成本。

接入真实大模型只需编辑 `backend/.env`（OpenAI 兼容协议）：

```ini
# 豆包（火山方舟）示例
AI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
AI_API_KEY=你的APIKey
AI_MODEL=ep-你的接入点ID

# DeepSeek 示例
AI_BASE_URL=https://api.deepseek.com
AI_API_KEY=sk-xxxx
AI_MODEL=deepseek-chat
```

配置后自动升级为：真实对话 + RAG 检索增强 + AI 错题归因 + AI 动态出题 + AI 面试评分。

## 🧪 测试

后端冒烟测试（覆盖注册→引导→闯关→对话→面试→Bug→代码运行→排行榜全链路）：

```bash
cd backend && python smoke_test.py
```

## ⚠️ 已知边界

- **代码沙箱**：当前为本地子进程演示沙箱（超时 5s + 危险模块黑名单），**仅限本机学习演示**。生产环境应按设计方案接入 Judge0/Docker 隔离沙箱。
- **RAG**：当前为关键词检索的 RAG-lite，生产可替换为 Milvus 向量检索 + Embedding。
- **Redis**：排行榜优先写 Redis 周榜，Redis 不可用时自动降级为数据库计算。
- **闯关运行态**（题目进度/HP）保存在内存中，重启后端需重新开始当前闯关。
- **面试语音**、系统设计沙盘、组队刷题等为 P2 规划，未包含在本次 MVP。

## 📝 参考

- 设计文档：《软件工程游戏化AI智能问答系统 专项设计方案.docx》
