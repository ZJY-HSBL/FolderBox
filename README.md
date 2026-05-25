# FolderBox

## 项目简介

FolderBox 是一个轻量化桌面文件夹可视化整理工具。它把真实本地文件夹映射为桌面上的半透明可视化容器，让用户可以直接在多个小窗口中查看和操作不同文件夹。

## 功能特性

- 支持同时打开多个 FolderBox 窗口，每个窗口可以绑定不同文件夹。
- 启动时自动恢复上次保留的多个窗口、位置、大小、文件夹和置顶状态。
- 使用 `QFileSystemModel + QListView` 展示文件和子文件夹。
- 半透明无边框窗口，支持拖动、右下角缩放、最小化和关闭。
- 透明度只作用于窗口背景，文件图标和文字保持清晰不透明。
- 支持图标网格视图和类似 Windows 资源管理器的详细信息视图。
- 详细信息视图显示名称、大小、类型、修改日期，支持列宽拖动和按列排序。
- 双击打开文件，双击文件夹进入子目录。
- 支持返回上一级、刷新、复制、粘贴、删除到回收站、重命名。
- 支持多选复制和多选删除。
- 支持 `Ctrl+C`、`Ctrl+V`、`Delete`、`F2`、`F5`、`Backspace`、`Ctrl+A` 等常用桌面快捷键。
- 支持把资源管理器里的文件或文件夹拖入窗口复制到当前绑定目录。
- 右键菜单支持文件操作、空白区域操作和新建窗口。
- 支持在 Windows 资源管理器中打开当前文件夹或定位文件。
- 配置文件缺失或损坏时自动恢复默认配置。

## 环境要求

- Windows 11
- Python 解释器：

```powershell
D:/software/miniconda3/envs/myenv/python.exe
```

## 安装依赖

```powershell
D:/software/miniconda3/envs/myenv/python.exe -m pip install -r requirements.txt
```

## 运行项目

```powershell
D:/software/miniconda3/envs/myenv/python.exe main.py
```

## 使用说明

启动后点击“选择文件夹”绑定本地目录。点击顶部“新窗口”可以再打开一个 FolderBox，并为它选择另一个文件夹。每个窗口都可以独立拖动、缩放、置顶和调整背景透明度。

顶部透明度滑块只改变背景透明度，不会影响文件图标和文件名文字的透明度。

顶部“图标 / 详细信息”按钮可以切换显示方式。图标模式适合像桌面一样快速操作，详细信息模式适合查看长文件名、文件大小、文件类型和修改日期。右键菜单里也可以切换视图。

文件区支持类似桌面的快捷键：`Enter` 打开、`F2` 重命名、`Delete` 删除到回收站、`Backspace` 返回上一级、`F5` 刷新、`Ctrl+A` 全选、`Ctrl+C` 复制、`Ctrl+V` 粘贴。从资源管理器拖入文件或文件夹时，会复制到当前窗口绑定的目录。

## 性能设计

- 使用 `QFileSystemModel` 的按需加载机制展示当前目录。
- 不生成图片、视频、PDF、Office 缩略图。
- 不使用高频定时器，也不每秒刷新目录。
- 不递归扫描子文件夹、磁盘或用户目录。
- 每个窗口只处理自己绑定的当前文件夹。
- 文件复制使用 `shutil.copy2` / `shutil.copytree`，避免把文件内容整体读入内存。
- 空闲时没有主动轮询任务，CPU 占用应接近 0。

## 打包为 exe

```powershell
D:/software/miniconda3/envs/myenv/python.exe -m pip install pyinstaller
D:/software/miniconda3/envs/myenv/python.exe -m PyInstaller -y --noconsole --name FolderBox --icon assets/app.ico --add-data "config;config" --add-data "assets;assets" main.py
```

图标文件位于：

```text
assets/app.png
assets/app.ico
```

## 生成安装包

项目内置了一个 PySide6 安装器脚本，会把 `dist/FolderBox` 嵌入单个安装程序。安装时可以选择安装路径，并可创建桌面快捷方式、开始菜单快捷方式和卸载入口。

```powershell
D:/software/miniconda3/envs/myenv/python.exe -m PyInstaller -y --onefile --noconsole --name FolderBoxSetupQt --icon assets/app.ico --add-data "dist/FolderBox;payload/FolderBox" --add-data "assets;assets" installer/installer.py
```

生成结果：

```text
dist/FolderBoxSetupQt.exe
dist/FolderBoxSetup-latest.exe
```
