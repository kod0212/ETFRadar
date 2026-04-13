"""
ETF Radar 打包脚本
产出:
  dist/ETFRadar/
  ├── ETFRadar.exe       # 启动器(极少更新)
  ├── _internal/         # Python运行时
  ├── app/               # 后端代码(可热更新)
  ├── static/            # 前端代码(可热更新)
  ├── data/
  │   └── seed.db.gz     # 预置数据(可热更新)
  └── 使用说明.txt
"""
import PyInstaller.__main__
import shutil
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist", "ETFRadar")

# 确认前端静态文件存在
static_dir = os.path.join(ROOT, "static")
if not os.path.exists(os.path.join(static_dir, "index.html")):
    print("[ERROR] frontend not built. Run:")
    print("  cd frontend && npm run build")
    print("  cp -r frontend/dist backend/static")
    exit(1)

seed_gz = os.path.join(ROOT, "data", "seed.db.gz")
if not os.path.exists(seed_gz):
    print("[ERROR] seed.db.gz not found")
    exit(1)

print("[build] Step 1: Building exe launcher...")

# 只打包 run.py 作为启动器
PyInstaller.__main__.run([
    "run.py",
    "--name=ETFRadar",
    "--onedir",
    "--console",
    "--hidden-import=uvicorn.logging",
    "--hidden-import=uvicorn.loops",
    "--hidden-import=uvicorn.loops.auto",
    "--hidden-import=uvicorn.protocols",
    "--hidden-import=uvicorn.protocols.http",
    "--hidden-import=uvicorn.protocols.http.auto",
    "--hidden-import=uvicorn.protocols.websockets",
    "--hidden-import=uvicorn.protocols.websockets.auto",
    "--hidden-import=uvicorn.lifespan",
    "--hidden-import=uvicorn.lifespan.on",
    "--hidden-import=sqlalchemy.dialects.sqlite",
    "--collect-submodules=akshare",
    "--collect-data=akshare",
    "--noconfirm",
    "--clean",
])

print("[build] Step 2: Copying app/ static/ data/ ...")

# 复制 app/ 到 dist（外置，可热更新）
app_dst = os.path.join(DIST, "app")
if os.path.exists(app_dst):
    shutil.rmtree(app_dst)
shutil.copytree(os.path.join(ROOT, "app"), app_dst)

# 复制 static/ 到 dist
static_dst = os.path.join(DIST, "static")
if os.path.exists(static_dst):
    shutil.rmtree(static_dst)
shutil.copytree(static_dir, static_dst)

# 复制 data/seed.db.gz 到 dist
data_dst = os.path.join(DIST, "data")
os.makedirs(data_dst, exist_ok=True)
shutil.copy2(seed_gz, os.path.join(data_dst, "seed.db.gz"))

print("[build] Done!")
print(f"  Output: {DIST}")
