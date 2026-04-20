"""自动更新模块 - 从阿里云 OSS 检查并下载更新"""
import os
import shutil
import logging
import zipfile
import tempfile
import threading
import requests
from typing import Optional
from app.core.config import VERSION

logger = logging.getLogger(__name__)

OSS_BASE = "https://etf-radar-release1.oss-cn-hangzhou.aliyuncs.com"
VERSION_URL = f"{OSS_BASE}/version.json"

# 更新进度状态
_progress = {"status": "idle", "percent": 0, "message": ""}
_update_lock = threading.Lock()


def check_update() -> Optional[dict]:
    """检查 OSS 是否有新版本"""
    try:
        resp = requests.get(VERSION_URL, timeout=10)
        if resp.status_code != 200:
            return None
        info = resp.json()
        remote = info.get("version", "")
        if not remote or _compare_version(remote, VERSION) <= 0:
            return None
        return info
    except Exception as e:
        logger.debug(f"检查更新失败: {e}")
        return None


def get_progress() -> dict:
    return dict(_progress)


def do_update(update_info: dict):
    """在后台线程执行更新"""
    if not _update_lock.acquire(blocking=False):
        return
    threading.Thread(target=_run_update, args=(update_info,), daemon=True).start()


def _run_update(update_info: dict):
    """下载并应用热更新，优先GitHub，超时fallback到OSS"""
    base_dir = os.environ.get("ETF_BASE_DIR", os.getcwd())
    urls = []
    # 优先 GitHub
    if update_info.get("github_url"):
        urls.append(update_info["github_url"])
    # OSS 兜底
    if update_info.get("update_url"):
        urls.append(update_info["update_url"])

    try:
        _progress.update(status="downloading", percent=0, message="下载更新包...")

        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        downloaded = False
        for i, url in enumerate(urls):
            try:
                source = "GitHub" if "github" in url else "OSS"
                _progress["message"] = f"从{source}下载中..."
                resp = requests.get(url, timeout=30, stream=True)
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                dl = 0
                for chunk in resp.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                    dl += len(chunk)
                    if total:
                        _progress["percent"] = int(dl * 80 / total)
                downloaded = True
                logger.info(f"从{source}下载成功")
                break
            except Exception as e:
                logger.warning(f"从{source}下载失败: {e}")
                tmp.seek(0)
                tmp.truncate()
                if i < len(urls) - 1:
                    _progress["message"] = "切换备用下载源..."
                    continue
                else:
                    raise Exception("所有下载源均失败")
        tmp.close()

        if not downloaded:
            raise Exception("下载失败")

        _progress.update(status="extracting", percent=82, message="解压替换文件...")
        with zipfile.ZipFile(tmp.name, "r") as zf:
            tmp_dir = tempfile.mkdtemp()
            zf.extractall(tmp_dir)

            for folder in ("app", "static"):
                src = os.path.join(tmp_dir, folder)
                dst = os.path.join(base_dir, folder)
                if os.path.exists(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)

            seed_src = os.path.join(tmp_dir, "data", "seed.db.gz")
            seed_dst = os.path.join(base_dir, "data", "seed.db.gz")
            if os.path.exists(seed_src):
                shutil.copy2(seed_src, seed_dst)

            shutil.rmtree(tmp_dir)
        os.unlink(tmp.name)

        _progress.update(status="merging", percent=90, message="更新数据库...")
        try:
            from app.core.init_data import _merge_upgrade, _find_seed_gz
            seed = _find_seed_gz()
            if seed:
                _merge_upgrade(seed)
        except Exception as e:
            logger.warning(f"数据库合并跳过: {e}")

        _progress.update(status="done", percent=100,
                         message=f"更新到 v{update_info['version']} 完成")
        logger.info(f"更新到 v{update_info['version']} 完成")

    except Exception as e:
        _progress.update(status="failed", percent=0, message=f"更新失败: {e}")
        logger.error(f"更新失败: {e}")
    finally:
        _update_lock.release()


def _compare_version(v1: str, v2: str) -> int:
    parts1 = [int(x) for x in v1.split(".")]
    parts2 = [int(x) for x in v2.split(".")]
    for a, b in zip(parts1, parts2):
        if a > b: return 1
        if a < b: return -1
    return len(parts1) - len(parts2)
