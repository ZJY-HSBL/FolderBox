from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

try:
    import winreg
except ImportError:  # pragma: no cover - Windows-only installer
    winreg = None


APP_NAME = "FolderBox"
PUBLISHER = "FolderBox"
APP_EXE = "FolderBox.exe"
UNINSTALL_KEY = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"


def resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent.parent


def payload_dir() -> Path:
    bundled = resource_root() / "payload" / APP_NAME
    if bundled.exists():
        return bundled
    return resource_root() / "dist" / APP_NAME


def asset_path(name: str) -> Path:
    return resource_root() / "assets" / name


def default_install_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "Programs" / APP_NAME


def desktop_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"


def start_menu_dir() -> Path:
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME


def powershell_quote(value: Path | str) -> str:
    text = str(value)
    return "'" + text.replace("'", "''") + "'"


def run_powershell(command: str) -> None:
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def create_shortcut(shortcut_path: Path, target_path: Path, working_dir: Path, description: str) -> None:
    shortcut_path.parent.mkdir(parents=True, exist_ok=True)
    command = (
        "$shell = New-Object -ComObject WScript.Shell; "
        f"$shortcut = $shell.CreateShortcut({powershell_quote(shortcut_path)}); "
        f"$shortcut.TargetPath = {powershell_quote(target_path)}; "
        f"$shortcut.WorkingDirectory = {powershell_quote(working_dir)}; "
        f"$shortcut.Description = {powershell_quote(description)}; "
        f"$shortcut.IconLocation = {powershell_quote(str(target_path) + ',0')}; "
        "$shortcut.Save()"
    )
    run_powershell(command)


def copy_payload(source: Path, destination: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"未找到安装资源：{source}")

    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            copy_payload(item, target)
        else:
            if item.name.lower() == "config.json" and item.parent.name.lower() == "config" and target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def write_uninstaller(install_dir: Path) -> Path:
    uninstall_cmd = install_dir / "Uninstall FolderBox.cmd"
    desktop_shortcut = desktop_dir() / f"{APP_NAME}.lnk"
    menu_folder = start_menu_dir()

    ps_command = (
        "$ErrorActionPreference = 'SilentlyContinue'; "
        "Start-Sleep -Milliseconds 800; "
        f"Remove-Item -LiteralPath {powershell_quote(desktop_shortcut)} -Force; "
        f"Remove-Item -LiteralPath {powershell_quote(menu_folder)} -Recurse -Force; "
        f"Remove-Item -LiteralPath 'HKCU:\\{UNINSTALL_KEY}' -Recurse -Force; "
        f"Remove-Item -LiteralPath {powershell_quote(install_dir)} -Recurse -Force"
    )
    cmd = (
        "@echo off\r\n"
        "start \"\" powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden "
        f"-Command \"{ps_command}\"\r\n"
        "exit /b 0\r\n"
    )
    uninstall_cmd.write_text(cmd, encoding="utf-8")
    return uninstall_cmd


def register_uninstall_entry(install_dir: Path, uninstall_cmd: Path) -> None:
    if winreg is None:
        return
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(install_dir / APP_EXE))
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstall_cmd}"')
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)


class InstallSignals(QObject):
    finished = Signal(Path)
    failed = Signal(str)


class InstallerWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        icon_path = asset_path("app.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.signals = InstallSignals()
        self.signals.finished.connect(self.install_success)
        self.signals.failed.connect(self.install_failed)

        self.setWindowTitle(f"{APP_NAME} 安装程序")
        self.setFixedSize(580, 330)

        self.path_edit = QLineEdit(str(default_install_dir()))
        self.desktop_checkbox = QCheckBox("创建桌面快捷方式")
        self.desktop_checkbox.setChecked(True)
        self.start_menu_checkbox = QCheckBox("创建开始菜单快捷方式")
        self.start_menu_checkbox.setChecked(True)
        self.run_checkbox = QCheckBox("安装完成后运行 FolderBox")
        self.run_checkbox.setChecked(True)
        self.status_label = QLabel("请选择安装位置，然后点击安装。")
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.install_button = QPushButton("安装")

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)

        title = QLabel("FolderBox")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        desc = QLabel("安装轻量化桌面文件夹可视化工具。安装目录可自定义，默认安装到当前用户目录。")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addWidget(QLabel("安装位置："))
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit, 1)
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.choose_folder)
        path_row.addWidget(browse_button)
        layout.addLayout(path_row)

        layout.addWidget(self.desktop_checkbox)
        layout.addWidget(self.start_menu_checkbox)
        layout.addWidget(self.run_checkbox)

        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.close)
        self.install_button.clicked.connect(self.start_install)
        button_row.addWidget(cancel_button)
        button_row.addWidget(self.install_button)
        layout.addLayout(button_row)

    def choose_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "选择安装文件夹", str(Path(self.path_edit.text()).parent))
        if selected:
            target = Path(selected)
            if target.name.lower() != APP_NAME.lower():
                target = target / APP_NAME
            self.path_edit.setText(str(target))

    def start_install(self) -> None:
        self.install_button.setEnabled(False)
        self.progress.setRange(0, 0)
        self.status_label.setText("正在安装，请稍候...")
        threading.Thread(target=self.install, daemon=True).start()

    def install(self) -> None:
        try:
            source = payload_dir()
            target = Path(self.path_edit.text()).expanduser()
            exe_path = target / APP_EXE

            copy_payload(source, target)
            uninstall_cmd = write_uninstaller(target)
            register_uninstall_entry(target, uninstall_cmd)

            if self.desktop_checkbox.isChecked():
                create_shortcut(desktop_dir() / f"{APP_NAME}.lnk", exe_path, target, APP_NAME)

            if self.start_menu_checkbox.isChecked():
                menu = start_menu_dir()
                create_shortcut(menu / f"{APP_NAME}.lnk", exe_path, target, APP_NAME)
                create_shortcut(menu / f"卸载 {APP_NAME}.lnk", uninstall_cmd, target, f"卸载 {APP_NAME}")

            if self.run_checkbox.isChecked():
                subprocess.Popen([str(exe_path)], cwd=str(target))

            self.signals.finished.emit(target)
        except Exception as exc:
            self.signals.failed.emit(str(exc))

    def install_success(self, target: Path) -> None:
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.status_label.setText(f"安装完成：{target}")
        QMessageBox.information(self, "安装完成", f"FolderBox 已安装到：\n{target}")
        self.close()

    def install_failed(self, message: str) -> None:
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.install_button.setEnabled(True)
        self.status_label.setText("安装失败。")
        QMessageBox.critical(self, "安装失败", message)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    icon_path = asset_path("app.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = InstallerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
