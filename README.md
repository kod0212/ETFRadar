# 📡 ETF雷达

自动追踪A股ETF基金份额/规模变化的桌面应用，帮助投资者直观感知大资金（如国家队）的动态。

## 功能

- 📊 **份额趋势图** — 按标签筛选，支持1月/3月/6月/1年/全部时间范围
- 📋 **最新数据表格** — 支持排序、搜索、分页
- 🏷️ **标签体系** — 系统标签（自动识别80+种分类）+ 自定义标签
- 🔍 **ETF详情** — 单只ETF历史趋势 + 数据表格
- ⚙️ **ETF管理** — 添加/删除/标签编辑，预置1400+只ETF历史数据
- 🔄 **自动数据更新** — 打开页面自动补上缺失天数
- 🆙 **自动版本更新** — 网页端一键更新，无需手动替换文件

## 数据来源

| 数据 | 来源 | 精度 |
|------|------|------|
| 上交所ETF每日份额 | 上交所官网 (sse.com.cn) | 每日精确 |
| 深交所ETF每日份额 | 深交所官网 (szse.cn) | 每日精确 |
| ETF实时价格/市值 | 腾讯财经 | 实时 |
| 历史K线 | 新浪财经 | 每日 |

## 使用方式

### 下载安装

从 [Releases](https://github.com/kod0212/ETFRadar/releases) 下载对应平台的完整包，解压后运行。

- **Windows**: 双击 `ETFRadar.exe`
- **Mac**: 终端执行 `./ETFRadar`（首次需 `xattr -cr ETFRadar/`）

启动后浏览器自动打开 http://localhost:9528

### 版本更新

程序会自动检查新版本，网页顶部提示更新，点击即可完成。

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
python run.py

# 前端
cd frontend
npm install
npm run dev
```

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **前端**: Vue 3 + TypeScript + Ant Design Vue + ECharts
- **打包**: PyInstaller (exe启动器 + 外置代码)
- **更新**: 阿里云 OSS 分发，网页端一键热更新
- **CI/CD**: GitHub Actions 自动打包 + 发布

## 项目结构

```
ETFRadar/                    # 打包产物
├── ETFRadar.exe             # 启动器（极少更新）
├── app/                     # 后端代码（可热更新）
├── static/                  # 前端页面（可热更新）
├── data/
│   ├── etf.db               # 用户数据库（自动生成，永不覆盖）
│   └── seed.db.gz           # 预置数据（可热更新）
└── log/                     # 日志
```

## 发版流程

```bash
# 改代码 → 更新 VERSION → 提交
git add -A && git commit -m "release: vX.Y.Z"
git tag vX.Y.Z && git push && git push --tags
# Actions 自动: 打包 → 上传 OSS → 创建 Release
# 用户下次打开自动检测到新版本
```

## License

MIT
