from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from send2trash import send2trash

from folderbox.utils import format_exception, is_valid_windows_filename, is_windows

COPY_SUFFIX = " - \u526f\u672c"


class FileOperationError(Exception):
    """Raised when a user-facing file operation cannot be completed."""


def open_with_default_app(path: str | Path) -> None:
    target = Path(path)
    if not target.exists():
        raise FileOperationError("\u6587\u4ef6\u6216\u6587\u4ef6\u5939\u4e0d\u5b58\u5728\u3002")
    try:
        if is_windows():
            os.startfile(str(target))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(target)])
    except OSError as exc:
        raise FileOperationError(f"\u6253\u5f00\u5931\u8d25\uff1a{format_exception(exc)}") from exc


def open_folder_in_explorer(folder: str | Path) -> None:
    target = Path(folder)
    if not target.exists() or not target.is_dir():
        raise FileOperationError("\u5f53\u524d\u6587\u4ef6\u5939\u4e0d\u5b58\u5728\u3002")
    try:
        if is_windows():
            subprocess.Popen(["explorer.exe", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
    except OSError as exc:
        raise FileOperationError(
            f"\u6253\u5f00\u8d44\u6e90\u7ba1\u7406\u5668\u5931\u8d25\uff1a{format_exception(exc)}"
        ) from exc


def show_in_explorer(path: str | Path) -> None:
    target = Path(path)
    if not target.exists():
        raise FileOperationError("\u6587\u4ef6\u6216\u6587\u4ef6\u5939\u4e0d\u5b58\u5728\u3002")
    try:
        if is_windows():
            subprocess.Popen(["explorer.exe", f"/select,{target}"])
        else:
            subprocess.Popen(["xdg-open", str(target.parent)])
    except OSError as exc:
        raise FileOperationError(
            f"\u5728\u8d44\u6e90\u7ba1\u7406\u5668\u4e2d\u663e\u793a\u5931\u8d25\uff1a{format_exception(exc)}"
        ) from exc


def get_available_copy_path(target_path: Path) -> Path:
    if not target_path.exists():
        return target_path

    parent = target_path.parent
    if target_path.is_dir():
        stem = target_path.name
        suffix = ""
    else:
        stem = target_path.stem
        suffix = target_path.suffix

    first = parent / f"{stem}{COPY_SUFFIX}{suffix}"
    if not first.exists():
        return first

    counter = 2
    while True:
        candidate = parent / f"{stem}{COPY_SUFFIX} {counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def copy_items(source_paths: list[str | Path], destination_folder: str | Path) -> tuple[list[Path], list[tuple[Path, str]]]:
    destination = Path(destination_folder)
    if not destination.exists() or not destination.is_dir():
        raise FileOperationError("\u7c98\u8d34\u76ee\u6807\u6587\u4ef6\u5939\u4e0d\u5b58\u5728\u3002")

    copied: list[Path] = []
    failures: list[tuple[Path, str]] = []

    for source in source_paths:
        src = Path(source)
        try:
            if not src.exists():
                raise FileOperationError("\u6e90\u6587\u4ef6\u6216\u6587\u4ef6\u5939\u4e0d\u5b58\u5728\u3002")

            if src.is_dir() and _is_relative_to(destination, src):
                raise FileOperationError(
                    "\u4e0d\u80fd\u628a\u6587\u4ef6\u5939\u7c98\u8d34\u5230\u5b83\u81ea\u8eab\u6216\u5b50\u6587\u4ef6\u5939\u4e2d\u3002"
                )

            target = get_available_copy_path(destination / src.name)
            if src.is_dir():
                shutil.copytree(src, target, symlinks=True)
            else:
                shutil.copy2(src, target)
            copied.append(target)
        except Exception as exc:
            failures.append((src, format_exception(exc)))

    return copied, failures


def delete_to_recycle_bin(paths: list[str | Path]) -> list[tuple[Path, str]]:
    failures: list[tuple[Path, str]] = []
    for item in paths:
        target = Path(item)
        try:
            if not target.exists():
                raise FileOperationError("\u6587\u4ef6\u6216\u6587\u4ef6\u5939\u4e0d\u5b58\u5728\u3002")
            send2trash(str(target))
        except Exception as exc:
            failures.append((target, format_exception(exc)))
    return failures


def rename_item(path: str | Path, new_name: str) -> Path:
    source = Path(path)
    clean_name = new_name.strip()

    if not source.exists():
        raise FileOperationError("\u6587\u4ef6\u6216\u6587\u4ef6\u5939\u4e0d\u5b58\u5728\u3002")
    if not is_valid_windows_filename(clean_name):
        raise FileOperationError(
            '\u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a\uff0c\u4e14\u4e0d\u80fd\u5305\u542b \\ / : * ? " < > |\u3002'
        )

    target = source.with_name(clean_name)
    if target == source:
        return source
    if target.exists():
        raise FileOperationError("\u76ee\u6807\u540d\u79f0\u5df2\u7ecf\u5b58\u5728\u3002")

    try:
        source.rename(target)
    except OSError as exc:
        raise FileOperationError(f"\u91cd\u547d\u540d\u5931\u8d25\uff1a{format_exception(exc)}") from exc
    return target
