import argparse
import ipaddress
import socket
from pathlib import Path
import pathspec
from .checksumtest import file_has_changed, update_checksum
from . import webrepl
from collections import defaultdict
from typing import TypeAlias, Union


NestedList: TypeAlias = list[Union[str, "NestedList"]]


SRC_PATH = Path(__file__).parent.parent.parent


def get_included_files(base_path: Path) -> list[Path]:
    """Walks base_path recursively. Each directory may contain a `.webreplignore` file with gitwildmatch patterns.
    Patterns apply to that directory and all subdirectories (like .gitignore).
    Returns a list of filepaths that are NOT ignored."""
    base_path = base_path.resolve()
    included_files: list[Path] = []

    def load_ignore_file(dir_path: Path) -> pathspec.PathSpec | None:
        ignore_file = dir_path / ".webreplignore"
        if not ignore_file.is_file():
            return None
        lines = ignore_file.read_text().splitlines()
        return pathspec.PathSpec.from_lines("gitwildmatch", lines)

    def walk(dir_path: Path, parent_specs: list[pathspec.PathSpec]) -> None:
        # Load ignore rules for this directory
        spec = load_ignore_file(dir_path)
        specs = parent_specs + ([spec] if spec else [])

        for entry in dir_path.iterdir():
            rel_path = entry.relative_to(base_path)

            # Check against all active ignore specs
            ignored = any(
                s.match_file(rel_path.as_posix())
                for s in specs
            )

            if ignored:
                continue

            if entry.is_dir():
                walk(entry, specs)
            elif entry.is_file():
                included_files.append(entry)

    walk(base_path, [])
    return included_files


def resolve_ip(hostname: str) -> str | None:
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


def validate_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def build_structure_from_files(files: list[Path], base_path: Path) -> NestedList:
    structure = lambda: defaultdict(structure)
    root = structure()

    for file_path in files:
        parts = file_path.relative_to(base_path).parts[:-1]  # drop filename
        node = root
        for part in parts:
            node = node[part]

    def to_list(d: defaultdict) -> NestedList:
        return [[k, to_list(v)] for k, v in sorted(d.items())]

    return to_list(root)


def create_structure(ws: webrepl.WebSocket, structure: NestedList) -> None:
    webrepl.run_webrepl_cmd(ws, f'import os')
    for folder_name, subfolders in structure:
        webrepl.run_webrepl_cmd(ws, f'os.mkdir("{folder_name}")')
        webrepl.run_webrepl_cmd(ws, f'os.chdir("{folder_name}")')
        create_structure(ws, subfolders)
        webrepl.run_webrepl_cmd(ws, 'os.chdir("..")')


def main() -> None:
    parser = argparse.ArgumentParser(description='Control Panel File Transfer Tool')
    parser.add_argument("hostname", help="The name of the device to send the files to, and to store checksums under.")
    parser.add_argument("--path", type=str, default=None, help="Optional: the files to transfer. Default is all in CWD.")
    parser.add_argument("--IP", help="IP override")
    parser.add_argument("--timeout", type=float, default=30.0, help="The duration of the socket timeout. Default is 30.")
    parser.add_argument('-f', '--force', action='store_true', help='Ignore the checksums.')
    parser.add_argument('--password', type=str, help='The webrepl password.', required=True)
    parser.add_argument("--transfer-files-only", action='store_true', help="Only transfer files, don't create folder structure.")
    args = parser.parse_args()

    hostname: str = args.hostname
    path = Path(args.path) if args.path else SRC_PATH

    all_files = get_included_files(path)
    changed_files: list[Path] = list(filter(lambda f: file_has_changed(str(f), hostname), all_files)) if not args.force else all_files

    if not changed_files:
        print(f"Device '{hostname}' is up to date!")
        return

    if args.IP:
        if not validate_ip(args.IP):
            print("Invalid IP address!")
            return
        ip = args.IP
    else:
        ip = resolve_ip(hostname)
        if not ip:
            print("Failed to resolve IP address!")
            return

    print("Connecting to device... ", end="")
    try:
        ws = webrepl.webrepl_connect(ip, args.password, timeout=args.timeout)
    except TimeoutError as e:
        print(e)
        return
    except ConnectionRefusedError as e:
        print(e)
        return
    print("Connected!")

    if not args.transfer_files_only:
        print("Creating folder structure... ", end="")
        structure = build_structure_from_files(changed_files, path)
        create_structure(ws, structure)
        print("Done!")

    print("Transferring files... ")
    for file in changed_files:
        local_file = str(file)
        remote_file = str(file).replace("\\", "/") if file.name not in {"main.py", "boot.py", "credentials.json", "utils.py", "hostname_manifest.json"} else file.name
        webrepl.webrepl_put(ws, local_file, remote_file)
        update_checksum(local_file, hostname)
    print("Files transferred!")

    try:
        webrepl.run_webrepl_cmd(ws, 'import machine; machine.reset()')
    except (TimeoutError, ConnectionResetError):
        pass

    ws.close()


if __name__ == "__main__":
    main()
