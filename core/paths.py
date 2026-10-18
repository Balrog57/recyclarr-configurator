import sys
from pathlib import Path


def app_dir() -> Path:
    """Folder the app lives in: next to the .exe when frozen (portable), else the project root."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    """Writable data folder (updated from GitHub at startup)."""
    return app_dir() / "data"


def data_file(name: str) -> Path:
    """data/<name> next to the app, else the copy bundled inside the .exe (first run offline)."""
    local = data_dir() / name
    bundled = Path(getattr(sys, "_MEIPASS", app_dir())) / "data" / name
    return local if local.exists() or not bundled.exists() else bundled
