"""
生成更新包 etf-radar-update.zip
包含 app/ + static/ + data/seed.db.gz
用于自动更新（不含exe）
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))

out = os.path.join(ROOT, "dist", "etf-radar-update.zip")
os.makedirs(os.path.dirname(out), exist_ok=True)

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    # app/
    app_dir = os.path.join(ROOT, "app")
    for dirpath, dirnames, filenames in os.walk(app_dir):
        # 跳过 __pycache__
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for f in filenames:
            if f.endswith(".pyc"):
                continue
            full = os.path.join(dirpath, f)
            arcname = os.path.relpath(full, ROOT)
            zf.write(full, arcname)

    # static/
    static_dir = os.path.join(ROOT, "static")
    if os.path.exists(static_dir):
        for dirpath, dirnames, filenames in os.walk(static_dir):
            for f in filenames:
                full = os.path.join(dirpath, f)
                arcname = os.path.relpath(full, ROOT)
                zf.write(full, arcname)

    # data/seed.db.gz
    seed = os.path.join(ROOT, "data", "seed.db.gz")
    if os.path.exists(seed):
        zf.write(seed, "data/seed.db.gz")

print(f"[build] Update package: {out}")
print(f"  Size: {os.path.getsize(out) / 1024 / 1024:.1f} MB")
