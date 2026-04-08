"""
ETF雷达 打包脚本
用法: cd backend && python build_exe.py

前提:
  1. pip install pyinstaller
  2. 前端已 build: cd frontend && npm run build
  3. 前端 dist 已复制: cp -r frontend/dist backend/static
"""
import PyInstaller.__main__
import shutil
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

# 确认前端静态文件存在
static_dir = os.path.join(ROOT, "static")
if not os.path.exists(os.path.join(static_dir, "index.html")):
    print("❌ 前端未构建，请先执行:")
    print("   cd frontend && npm run build")
    print("   cp -r frontend/dist backend/static")
    exit(1)

# 确认 seed.db.gz 存在
seed_gz = os.path.join(ROOT, "data", "seed.db.gz")
if not os.path.exists(seed_gz):
    print("❌ seed.db.gz 不存在")
    exit(1)

print("📦 开始打包 ETF雷达...")

PyInstaller.__main__.run([
    "run.py",
    "--name=ETFRadar",
    "--onedir",
    "--console",  # 保留控制台窗口显示日志
    f"--add-data=static{os.pathsep}static",
    f"--add-data=data/seed.db.gz{os.pathsep}data",
    f"--add-data=app{os.pathsep}app",
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
    "--noconfirm",
    "--clean",
])

print("\n✅ 打包完成！")
print(f"   输出目录: {os.path.join(ROOT, 'dist', 'ETFRadar')}")
print("   运行: dist/ETFRadar/ETFRadar.exe (Windows)")
print("   运行: dist/ETFRadar/ETFRadar (Mac/Linux)")
