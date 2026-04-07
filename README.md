# ETF雷达

自动追踪A股ETF基金份额变化的Web应用，帮助投资者直观感知大资金动态。

## 功能

- 每日自动采集指定ETF的份额数据
- 同类ETF份额汇总趋势图
- ETF管理（添加/删除/分组）
- 数据表格 + ECharts图表可视化

## 技术栈

- **后端**: Python + FastAPI + APScheduler + SQLite
- **前端**: Vue 3 + ECharts + Ant Design Vue
- **数据源**: AKShare + 东方财富

## 项目结构

```
ETFProject/
├── backend/          # 后端服务
│   ├── app/
│   │   ├── api/      # API路由
│   │   ├── core/     # 配置、数据库
│   │   ├── models/   # 数据模型
│   │   ├── schemas/  # Pydantic模型
│   │   ├── services/ # 业务逻辑
│   │   └── main.py
│   ├── scripts/      # 数据采集脚本
│   └── requirements.txt
├── frontend/         # 前端应用
└── docs/             # 文档
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

## 需求文档

[ETF雷达 PRD](https://www.feishu.cn/docx/DpvLdnNnjoxCrSxVROAcQutqnTh)
