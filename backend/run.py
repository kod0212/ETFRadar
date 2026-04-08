"""ETF雷达 exe 入口"""
import sys
import os
import webbrowser
import threading

# PyInstaller 打包后的资源路径
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    os.chdir(BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 设置数据目录为 exe 同级的 data 文件夹（可写）
if getattr(sys, 'frozen', False):
    DATA_DIR = os.path.join(os.path.dirname(sys.executable), "data")
    os.makedirs(DATA_DIR, exist_ok=True)
    os.environ["ETF_DATA_DIR"] = DATA_DIR


def open_browser():
    import time
    time.sleep(2)
    webbrowser.open("http://localhost:8000")


if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    print("=" * 40)
    print("  ETF Radar starting...")
    print("  Browser will open automatically")
    print("  Close this window to exit")
    print("=" * 40)

    import uvicorn
    from app.main import app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
