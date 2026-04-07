# Docker 部署指南

## 前提条件

安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（Mac / Windows / Linux 均支持）。

安装完成后确认：

```bash
docker --version    # Docker version 24.0+
docker compose version  # Docker Compose version v2.20+
```

## 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/kod0212/ETFRadar.git
cd ETFRadar

# 2. 构建并启动
docker compose up --build

# 首次构建约 2-3 分钟（下载依赖），之后启动秒级
```

启动成功后会看到：

```
backend-1   | INFO:     Uvicorn running on http://0.0.0.0:8000
frontend-1  | /docker-entrypoint.sh: Configuration complete; ready for start up
```

## 访问

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端页面 | http://localhost:5173 | 主界面 |
| 后端 API | http://localhost:8000 | API 服务 |
| API 文档 | http://localhost:8000/api/docs | Swagger UI |

## 常用命令

```bash
# 后台运行
docker compose up -d

# 查看日志
docker compose logs -f

# 只看后端日志
docker compose logs -f backend

# 停止服务
docker compose down

# 停止并删除数据（重置数据库）
docker compose down -v

# 重新构建（代码更新后）
docker compose up --build
```

## 数据持久化

数据库文件存储在 Docker volume `etf_data` 中：

- `docker compose down` → 数据保留
- `docker compose down -v` → 数据清除（下次启动从预置数据恢复）

查看数据卷：

```bash
docker volume ls | grep etf
```

## 端口冲突

如果 5173 或 8000 端口被占用，修改 `docker-compose.yml`：

```yaml
services:
  backend:
    ports:
      - "9000:8000"    # 改为 9000
  frontend:
    ports:
      - "3000:80"      # 改为 3000
```

## 不使用 Docker（本地开发）

如果不想用 Docker，也可以直接本地运行：

**终端 1 — 后端**：
```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

**终端 2 — 前端**：
```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173
