# 📡 ETF雷达

自动追踪A股ETF基金份额变化的Web应用，帮助投资者直观感知大资金（如国家队）的动态。

## 功能

- 📊 **份额趋势图** — 按分组查看ETF份额/市值变化趋势
- 📋 **最新数据表格** — 所有追踪ETF的最新份额、市值、变化量
- 🔍 **ETF详情** — 单只ETF历史趋势 + 数据表格
- ⚙️ **ETF管理** — 添加/删除/分组，新增ETF自动有历史数据
- 🔄 **自动更新** — 打开页面自动补上缺失天数，无需手动操作

## 数据来源

| 数据 | 来源 | 精度 |
|------|------|------|
| 上交所ETF每日份额 | 上交所官网 (sse.com.cn) | 每日精确 |
| 深交所ETF每日份额 | 深交所官网 (szse.cn) | 每日精确 |
| ETF实时价格/市值 | 腾讯财经 | 实时 |
| 预置历史数据 | 上交所+深交所 | 1461只ETF, 约1年 |

## 快速开始

### 方式一：Docker（推荐）

```bash
git clone https://github.com/kod0212/ETFRadar.git
cd ETFRadar
docker-compose up
```

打开 http://localhost:5173

### 方式二：本地开发

**后端**（终端1）：
```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

**前端**（终端2）：
```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **前端**: Vue 3 + TypeScript + Ant Design Vue + ECharts
- **数据源**: 上交所/深交所官方接口 + 腾讯财经

## 项目结构

```
ETFRadar/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # RESTful API (funds/shares/collect)
│   │   ├── core/          # 配置、数据库、初始化
│   │   ├── models/        # SQLAlchemy ORM
│   │   ├── schemas/       # Pydantic 模型
│   │   └── services/      # 数据采集服务
│   ├── data/
│   │   └── seed.db.gz     # 预置数据 (1461只ETF, ~43万条)
│   └── scripts/           # 数据回补脚本
├── frontend/
│   └── src/
│       ├── views/         # 仪表盘/管理/详情页
│       ├── api.ts         # API 封装
│       └── router.ts      # 路由
├── docker-compose.yml     # 一键部署
└── docs/
    └── architecture.md    # 架构设计文档
```

## API 文档

启动后端后访问 http://localhost:8000/api/docs 查看 Swagger UI。

主要接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/funds | ETF列表 |
| POST | /api/v1/funds | 添加ETF |
| GET | /api/v1/shares/latest | 最新份额 |
| GET | /api/v1/shares/trend | 趋势数据 |
| POST | /api/v1/collect/trigger | 触发增量更新 |

## 数据更新机制

- **预置数据**: 首次启动从 `seed.db.gz` 恢复，包含约1年历史
- **增量更新**: 打开页面时自动检查，补上数据库最新日期到今天的缺失数据
- **数据源**: 上交所/深交所官方接口，每日精确份额

## 相关文档

- [产品需求文档 (PRD)](docs/prd.md)
- [架构设计](docs/architecture.md)

## License

MIT
