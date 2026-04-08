# 打包为 exe（Windows 桌面应用）

## 打包步骤

```bash
# 1. 构建前端
cd frontend
npm install
npm run build

# 2. 复制前端到后端
cp -r dist ../backend/static    # Mac/Linux
# xcopy dist ..\backend\static /E /I   # Windows

# 3. 打包
cd ../backend
pip install pyinstaller
python build_exe.py
```

打包完成后在 `backend/dist/ETFRadar/` 目录下。

## 使用

- **Windows**: 双击 `ETFRadar.exe`
- **Mac/Linux**: 运行 `./ETFRadar`

浏览器会自动打开 http://localhost:9528

关闭命令行窗口即可退出。

## 分发

把 `dist/ETFRadar/` 整个文件夹打成 zip 发给别人即可，对方不需要安装任何环境。

## 数据存储

exe 运行时，数据库文件 `etf.db` 存放在 exe 同级的 `data/` 目录下。首次运行自动从预置数据恢复。
