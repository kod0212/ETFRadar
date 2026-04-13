"""ETF雷达 启动器
这是唯一打包进 exe 的文件，负责：
1. 检查更新
2. 启动后端服务
3. 打开浏览器
"""
import sys
import os
import webbrowser
import threading

# exe 所在目录作为工作目录
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
os.environ["ETF_DATA_DIR"] = DATA_DIR
os.environ["ETF_BASE_DIR"] = BASE_DIR

PORT = 9528


def check_dependencies():
    """检查 app/ 和 static/ 是否存在"""
    app_dir = os.path.join(BASE_DIR, "app")
    if not os.path.exists(app_dir):
        print("=" * 50)
        print("  错误: 缺少 app/ 目录!")
        print("  请确保 app/ 文件夹和 ETFRadar.exe 在同一目录")
        print("=" * 50)
        input("按回车键退出...")
        sys.exit(1)


def open_browser():
    import time
    time.sleep(2)
    webbrowser.open(f"http://localhost:{PORT}")


def check_and_update():
    """检查更新并执行"""
    try:
        from app.core.updater import check_update, do_update
        update_info = check_update()
        if update_info:
            print(f"  发现新版本: v{update_info['version']}")
            print(f"  更新内容: {update_info.get('description', '')}")
            answer = input("  是否更新？(Y/n): ").strip().lower()
            if answer != 'n':
                do_update(update_info)
                print("  更新完成，正在启动...")
            else:
                print("  跳过更新")
    except Exception as e:
        print(f"  检查更新失败(不影响使用): {e}")


if __name__ == "__main__":
    check_dependencies()

    print("=" * 50)
    print(f"  ETF Radar starting...")
    print(f"  http://localhost:{PORT}")
    print("  Close this window to exit")
    print("=" * 50)

    # 检查更新
    check_and_update()

    # 启动浏览器
    threading.Thread(target=open_browser, daemon=True).start()

    # 启动服务
    import uvicorn
    from app.main import app
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
