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
    webbrowser.open("http://localhost:9528")


if __name__ == "__main__":
    # 检查是否被移出了安装目录
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        internal = os.path.join(exe_dir, "_internal")
        if not os.path.exists(internal):
            print("=" * 50)
            print("  错误: 请勿将 ETFRadar.exe 移出安装目录!")
            print("  请将整个 ETFRadar 文件夹一起移动。")
            print("=" * 50)
            input("按回车键退出...")
            sys.exit(1)

    threading.Thread(target=open_browser, daemon=True).start()
    print("=" * 40)
    print("  ETF Radar starting...")
    print("  Browser will open automatically")
    print("  Close this window to exit")
    print("=" * 40)

    import uvicorn
    from app.main import app
    uvicorn.run(app, host="0.0.0.0", port=9528, log_level="info")
