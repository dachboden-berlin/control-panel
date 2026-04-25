"""Manifest for freezing the package into .mpy files or firmware."""

from pathlib import Path

# Path to the controlpanel (package) directory. We cannot use __file__, better solution needed!
ROOT = Path("/root/control-panel/controlpanel")

# Folders to include in the build
INCLUDE_DIRS = ["shared", "upy"]

ROOT_FILES = {
    "boot.py",
    "main.py",
    "utils.py",
}  # These files are getting put in the "root" on the mpy file system


def list_py_files(folder: Path) -> list[str]:
    """Return all .py files within a folder, relative to ROOT."""
    return [
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in folder.rglob("*.py")
        if path.name not in ROOT_FILES
    ]


all_py_files: list[str] = []
for pkg in INCLUDE_DIRS:
    pkg_folder = ROOT / pkg
    py_files = list_py_files(pkg_folder)
    all_py_files.extend(py_files)

# Register package (used by MicroPython build system)
package("controlpanel", files=all_py_files)  # type: ignore
module("boot.py", base_path="controlpanel/upy")  # type: ignore
module("main.py", base_path="controlpanel/upy")  # type: ignore
module("utils.py", base_path="controlpanel/upy")  # type: ignore
