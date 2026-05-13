"""测试自升级流程"""
import io
import os
import time
import zipfile
import threading
from unittest.mock import patch, MagicMock
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestVersionCompare:
    """版本号比较"""

    def setup_method(self):
        from app.core.updater import _compare_version
        self.cmp = _compare_version

    def test_newer(self):
        assert self.cmp("1.3.0", "1.2.3") == 1

    def test_same(self):
        assert self.cmp("1.2.3", "1.2.3") == 0

    def test_older(self):
        assert self.cmp("1.2.2", "1.2.3") == -1

    def test_major_bump(self):
        assert self.cmp("2.0.0", "1.9.9") == 1

    def test_patch_bump(self):
        assert self.cmp("1.2.4", "1.2.3") == 1


class TestCheckUpdate:
    """检查更新"""

    @patch("app.core.updater.requests.get")
    def test_no_update_when_same_version(self, mock_get):
        from app.core.updater import check_update, VERSION
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"version": VERSION}
        mock_get.return_value = mock_resp

        result = check_update()
        assert result is None

    @patch("app.core.updater.requests.get")
    def test_has_update_when_newer(self, mock_get):
        from app.core.updater import check_update
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "version": "99.0.0",
            "update_type": "hot",
            "changelog": "- 测试更新",
            "download_size": "15MB",
            "github_url": "https://github.com/test/update.zip",
            "update_url": "https://oss.test/update.zip",
        }
        mock_get.return_value = mock_resp

        result = check_update()
        assert result is not None
        assert result["version"] == "99.0.0"
        assert result["changelog"] == "- 测试更新"
        assert result["download_size"] == "15MB"

    @patch("app.core.updater.requests.get")
    def test_returns_none_on_network_error(self, mock_get):
        from app.core.updater import check_update
        mock_get.side_effect = Exception("网络超时")

        result = check_update()
        assert result is None

    @patch("app.core.updater.requests.get")
    def test_returns_none_on_http_error(self, mock_get):
        from app.core.updater import check_update
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        result = check_update()
        assert result is None

    @patch("app.core.updater.requests.get")
    def test_cold_update_detected(self, mock_get):
        from app.core.updater import check_update
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "version": "99.0.0",
            "update_type": "cold",
        }
        mock_get.return_value = mock_resp

        result = check_update()
        assert result["update_type"] == "cold"


class TestDoUpdate:
    """执行更新"""

    def _make_update_zip(self) -> bytes:
        """创建一个模拟的更新 zip 包"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("app/__init__.py", "# updated")
            zf.writestr("app/core/config.py", 'VERSION = "99.0.0"')
            zf.writestr("static/index.html", "<html>updated</html>")
            zf.writestr("data/seed.db.gz", b"fake_seed_data")
        return buf.getvalue()

    @patch("app.core.updater.requests.get")
    def test_hot_update_success(self, mock_get):
        """模拟完整热更新流程：下载 → 解压 → 替换文件"""
        import tempfile
        import shutil
        from app.core.updater import do_update, get_progress, _progress, _update_lock

        # 重置状态
        _progress.update(status="idle", percent=0, message="")

        # 创建临时 base_dir 模拟安装目录
        base_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(base_dir, "app"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "static"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)

        # mock 下载响应
        zip_data = self._make_update_zip()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-length": str(len(zip_data))}
        mock_resp.iter_content.return_value = [zip_data]
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        update_info = {
            "version": "99.0.0",
            "github_url": "https://github.com/test/update.zip",
            "update_url": "https://oss.test/update.zip",
        }

        # mock init_data 避免真实数据库操作
        with patch.dict(os.environ, {"ETF_BASE_DIR": base_dir}):
            with patch("app.core.updater._run_update.__module__", "app.core.updater"):
                with patch("app.core.init_data._merge_upgrade"):
                    with patch("app.core.init_data._find_seed_gz", return_value=None):
                        do_update(update_info)
                        # 等待后台线程完成
                        time.sleep(2)

        # 验证进度状态
        progress = get_progress()
        assert progress["status"] == "done"
        assert "99.0.0" in progress["message"]

        # 验证文件被替换
        assert os.path.exists(os.path.join(base_dir, "app", "__init__.py"))
        assert os.path.exists(os.path.join(base_dir, "static", "index.html"))
        assert os.path.exists(os.path.join(base_dir, "data", "seed.db.gz"))

        with open(os.path.join(base_dir, "static", "index.html")) as f:
            assert "updated" in f.read()

        # 清理
        shutil.rmtree(base_dir)

    @patch("app.core.updater.requests.get")
    def test_update_fails_gracefully(self, mock_get):
        """所有下载源失败时，状态变为 failed"""
        from app.core.updater import do_update, get_progress, _progress

        _progress.update(status="idle", percent=0, message="")
        mock_get.side_effect = Exception("连接超时")

        update_info = {
            "version": "99.0.0",
            "github_url": "https://github.com/test/update.zip",
            "update_url": "https://oss.test/update.zip",
        }

        do_update(update_info)
        time.sleep(2)

        progress = get_progress()
        assert progress["status"] == "failed"
        assert "失败" in progress["message"]

    @patch("app.core.updater.requests.get")
    def test_github_fails_fallback_to_oss(self, mock_get):
        """GitHub 下载失败时 fallback 到 OSS"""
        import tempfile
        import shutil
        from app.core.updater import do_update, get_progress, _progress

        _progress.update(status="idle", percent=0, message="")

        base_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(base_dir, "app"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "static"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)

        zip_data = self._make_update_zip()

        call_count = [0]

        def side_effect(url, **kwargs):
            call_count[0] += 1
            if "github" in url:
                raise Exception("GitHub 超时")
            # OSS 成功
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.headers = {"content-length": str(len(zip_data))}
            mock_resp.iter_content.return_value = [zip_data]
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        mock_get.side_effect = side_effect

        update_info = {
            "version": "99.0.0",
            "github_url": "https://github.com/test/update.zip",
            "update_url": "https://oss.test/update.zip",
        }

        with patch.dict(os.environ, {"ETF_BASE_DIR": base_dir}):
            with patch("app.core.init_data._merge_upgrade"):
                with patch("app.core.init_data._find_seed_gz", return_value=None):
                    do_update(update_info)
                    time.sleep(2)

        progress = get_progress()
        assert progress["status"] == "done"
        assert call_count[0] == 2  # GitHub 失败 + OSS 成功

        shutil.rmtree(base_dir)

    def test_concurrent_update_blocked(self):
        """并发更新时第二个请求被阻塞"""
        from app.core.updater import _update_lock, _progress, do_update

        _progress.update(status="idle", percent=0, message="")

        # 手动占住锁
        _update_lock.acquire()
        try:
            # do_update 应该直接返回（acquire 失败）
            with patch("app.core.updater.requests.get"):
                do_update({"version": "99.0.0", "github_url": "http://test"})
                time.sleep(0.5)
                # 进度应该还是 idle（线程没启动）
                assert _progress["status"] == "idle"
        finally:
            _update_lock.release()


class TestProgressReset:
    """进度状态管理"""

    def test_do_update_resets_progress(self):
        """do_update 调用时重置 progress"""
        from app.core.updater import _progress, do_update, _update_lock

        _progress.update(status="done", percent=100, message="上次更新完成")

        # 模拟锁被占用，do_update 会重置 progress 但不启动线程
        _update_lock.acquire()
        try:
            do_update({"version": "99.0.0"})
            # progress 应该被重置为 idle
            assert _progress["status"] == "idle"
            assert _progress["percent"] == 0
        finally:
            _update_lock.release()


class TestAPIEndpoints:
    """API 端点测试"""

    @patch("app.core.updater.requests.get")
    def test_check_update_api_no_update(self, mock_get):
        from app.core.updater import VERSION
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"version": VERSION}
        mock_get.return_value = mock_resp

        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        resp = client.get("/api/v1/collect/check_update")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["has_update"] is False
        assert data["current"] == VERSION

    @patch("app.core.updater.requests.get")
    def test_check_update_api_has_update(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "version": "99.0.0",
            "update_type": "hot",
            "changelog": "- 新功能",
            "download_size": "12MB",
            "github_url": "https://github.com/test.zip",
            "update_url": "https://oss.test.zip",
        }
        mock_get.return_value = mock_resp

        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        resp = client.get("/api/v1/collect/check_update")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["has_update"] is True
        assert data["version"] == "99.0.0"
        assert data["changelog"] == "- 新功能"
        assert data["download_size"] == "12MB"
        assert "current" in data

    @patch("app.core.updater.requests.get")
    def test_do_update_api_cold_rejected(self, mock_get):
        """冷更新不触发下载，返回 cold 状态"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "version": "99.0.0",
            "update_type": "cold",
            "full_url_windows": "https://oss.test/full.zip",
        }
        mock_get.return_value = mock_resp

        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        resp = client.post("/api/v1/collect/do_update")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "cold"
        assert "完整包" in data["message"]

    @patch("app.core.updater.requests.get")
    def test_do_update_api_no_update(self, mock_get):
        """已是最新时返回 up_to_date"""
        from app.core.updater import VERSION
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"version": VERSION}
        mock_get.return_value = mock_resp

        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        resp = client.post("/api/v1/collect/do_update")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "up_to_date"

    def test_update_progress_api(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core.updater import _progress

        _progress.update(status="downloading", percent=50, message="下载中...")

        client = TestClient(app)
        resp = client.get("/api/v1/collect/update_progress")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "downloading"
        assert data["percent"] == 50

        # 清理
        _progress.update(status="idle", percent=0, message="")
