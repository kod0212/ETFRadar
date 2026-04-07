# ETF雷达

自动追踪A股ETF基金份额变化的Web应用，帮助投资者直观感知大资金动态。

## 功能

- 每日自动采集指定ETF的份额/规模数据（增量更新）
- 同类ETF份额汇总趋势图
- ETF管理（添加/删除/分组）
- 数据表格 + ECharts图表可视化

## 技术栈

- **后端**: Python + FastAPI + SQLite + APScheduler
- **前端**: Vue 3 + ECharts + Ant Design Vue
- **数据源**: 腾讯财经(主) + AKShare(辅) + 东方财富(校准)

## 项目结构

```
ETFProject/
├── backend/
│   ├── app/
│   │   ├── api/           # API路由 (RESTful, 兼容Web+小程序)
│   │   │   ├── v1/        # API v1 版本
│   │   │   │   ├── funds.py    # ETF管理
│   │   │   │   ├── shares.py   # 份额数据查询
│   │   │   │   └── collect.py  # 采集控制
│   │   │   └── deps.py    # 依赖注入(DB session等)
│   │   ├── core/
│   │   │   ├── config.py  # 配置管理
│   │   │   ├── database.py # SQLite连接
│   │   │   └── scheduler.py # 定时任务
│   │   ├── models/        # SQLAlchemy ORM模型
│   │   ├── schemas/       # Pydantic请求/响应模型
│   │   ├── services/      # 业务逻辑
│   │   │   ├── collector.py  # 数据采集服务
│   │   │   └── analyzer.py   # 数据分析服务
│   │   └── main.py
│   ├── data/              # SQLite数据库文件
│   ├── scripts/           # 工具脚本
│   └── requirements.txt
├── frontend/              # Web前端 (Vue 3)
└── docs/                  # 文档
```

## 快速开始

```bash
# 后端
cd backend
pip install -r requirements.txt
python -m app.main

# 前端
cd frontend
npm install
npm run dev
```

## 架构设计

详见 [docs/architecture.md](docs/architecture.md)

## 需求文档

[ETF雷达 PRD](https://www.feishu.cn/docx/DpvLdnNnjoxCrSxVROAcQutqnTh)
