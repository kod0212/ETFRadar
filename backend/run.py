"""ETF雷达 启动器"""
import sys
import os
import webbrowser
import threading

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
os.environ["ETF_DATA_DIR"] = DATA_DIR
os.environ["ETF_BASE_DIR"] = BASE_DIR

PORT = 9528


def open_browser():
    import time
    time.sleep(2)
    webbrowser.open(f"http://localhost:{PORT}")


if __name__ == "__main__":
    app_dir = os.path.join(BASE_DIR, "app")
    if not os.path.exists(app_dir):
        print("错误: 缺少 app/ 目录!")
        input("按回车键退出...")
        sys.exit(1)

    print("=" * 50)
    print(f"  ETF Radar starting...")
    print(f"  http://localhost:{PORT}")
    print("  Close this window to exit")
    print("=" * 50)

    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    from app.main import app
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
