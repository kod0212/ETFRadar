"""自动更新模块
从 GitHub Release 检查并下载更新包
更新包只包含 app/ + static/ + data/seed.db.gz（不含 exe）
"""
import os
import sys
import json
import shutil
import logging
import zipfile
import tempfile
import requests
from pathlib import Path
from typing import Optional
from app.core.config import VERSION

logger = logging.getLogger(__name__)

GITHUB_REPO = "kod0212/ETFRadar"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
UPDATE_ASSET_NAME = "etf-radar-update.zip"


def check_update() -> Optional[dict]:
    """检查 GitHub 是否有新版本，返回更新信息或 None"""
    try:
        resp = requests.get(GITHUB_API, timeout=10,
                            headers={"Accept": "application/vnd.github.v3+json"})
        if resp.status_code != 200:
            return None
        release = resp.json()
        remote_version = release.get("tag_name", "").lstrip("v")
        if not remote_version:
            return None

        if _compare_version(remote_version, VERSION) <= 0:
            logger.info(f"当前版本 v{VERSION} 已是最新")
            return None

        # 找更新包资源
        download_url = None
        for asset in release.get("assets", []):
            if asset["name"] == UPDATE_ASSET_NAME:
                download_url = asset["browser_download_url"]
                break

        if not download_url:
            logger.info(f"新版本 v{remote_version} 无更新包，需手动更新")
            return None

        return {
            "version": remote_version,
            "download_url": download_url,
            "description": release.get("body", "")[:200],
        }
    except Exception as e:
        logger.debug(f"检查更新失败: {e}")
        return None


def do_update(update_info: dict):
    """下载并应用更新"""
    base_dir = os.environ.get("ETF_BASE_DIR", os.getcwd())
    download_url = update_info["download_url"]

    logger.info(f"下载更新包: {download_url}")
    print("  下载更新包...")

    # 下载到临时文件
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    try:
        resp = requests.get(download_url, timeout=120, stream=True)
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        for chunk in resp.iter_content(chunk_size=8192):
            tmp.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded * 100 // total
                print(f"\r  下载进度: {pct}%", end="", flush=True)
        print()
        tmp.close()

        # 解压
        print("  应用更新...")
        with zipfile.ZipFile(tmp.name, "r") as zf:
            # 解压到临时目录
            tmp_dir = tempfile.mkdtemp()
            zf.extractall(tmp_dir)

            # 替换 app/
            app_src = os.path.join(tmp_dir, "app")
            app_dst = os.path.join(base_dir, "app")
            if os.path.exists(app_src):
                if os.path.exists(app_dst):
                    shutil.rmtree(app_dst)
                shutil.copytree(app_src, app_dst)
                logger.info("更新 app/ 完成")

            # 替换 static/
            static_src = os.path.join(tmp_dir, "static")
            static_dst = os.path.join(base_dir, "static")
            if os.path.exists(static_src):
                if os.path.exists(static_dst):
                    shutil.rmtree(static_dst)
                shutil.copytree(static_src, static_dst)
                logger.info("更新 static/ 完成")

            # 替换 seed.db.gz
            seed_src = os.path.join(tmp_dir, "data", "seed.db.gz")
            seed_dst = os.path.join(base_dir, "data", "seed.db.gz")
            if os.path.exists(seed_src):
                shutil.copy2(seed_src, seed_dst)
                logger.info("更新 seed.db.gz 完成")

            shutil.rmtree(tmp_dir)

        logger.info(f"更新到 v{update_info['version']} 完成")
    finally:
        os.unlink(tmp.name)


def _compare_version(v1: str, v2: str) -> int:
    """比较版本号，v1>v2返回1，v1==v2返回0，v1<v2返回-1"""
    parts1 = [int(x) for x in v1.split(".")]
    parts2 = [int(x) for x in v2.split(".")]
    for a, b in zip(parts1, parts2):
        if a > b:
            return 1
        if a < b:
            return -1
    return len(parts1) - len(parts2)
