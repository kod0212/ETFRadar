"""
ETF Radar - build script
Usage: cd backend && python build_exe.py
"""
import PyInstaller.__main__
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

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

print("[build] Starting ETFRadar packaging...")

PyInstaller.__main__.run([
    "run.py",
    "--name=ETFRadar",
    "--onedir",
    "--console",
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

print("[build] Done!")
print(f"  Output: {os.path.join(ROOT, 'dist', 'ETFRadar')}")
