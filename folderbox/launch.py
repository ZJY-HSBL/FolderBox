from __future__ import annotations

from pathlib import Path


def requested_folder(argv: list[str]) -> str:
    args = list(argv[1:])
    if "--folder" not in args:
        return ""

    index = args.index("--folder")
    if index + 1 >= len(args):
        return ""

    try:
        path = Path(args[index + 1]).expanduser()
        if path.exists() and path.is_dir():
            return str(path.resolve())
    except (OSError, ValueError):
        pass
    return ""
