import pathlib
import types
from RestrictedPython import compile_restricted
import controlpanel
import sys


SCRIPT_DIR = pathlib.Path(__file__).parent.parent.parent / "userscripts"
sys.path.append(str(SCRIPT_DIR))
WHITELIST_PATH = SCRIPT_DIR / "whitelist.txt"
WHITELIST: set[str] = set(WHITELIST_PATH.read_text().splitlines())


def load_script(name: str, force_unrestricted: bool = False) -> types.ModuleType | None:
    from .load_scripts_helper import make_globals

    unrestricted = (name in WHITELIST) or force_unrestricted
    if unrestricted:
        try:
            module = __import__(f"userscripts.{name}")
            print(f"Loaded {name}")
            return module
        except ImportError:
            pass

    script_path = (SCRIPT_DIR / name).with_suffix(".py")
    if not script_path.is_file():
        print(f"Failed to load {name}: file could not be found.")
        return None

    source_code = script_path.read_text()
    name = script_path.stem

    try:
        bytecode = compile_restricted(source_code, filename=name, mode="exec")
    except SyntaxError as e:
        print(f"Failed to compile {name}: {e}")
        return None

    module_name = f"userscripts.{name}"
    module = types.ModuleType(module_name)

    module.__dict__.update(make_globals())
    module.__dict__["__name__"] = module_name

    if name in WHITELIST:
        exec(bytecode)
    else:
        exec(bytecode, module.__dict__, module.__dict__)

    sys.modules[module_name] = module
    controlpanel.api.services.loaded_scripts[module_name] = module

    print(f"Loaded {name}")
    return module


def load_scripts(args: list[str], force_unrestricted: bool) -> None:
    for arg in args:
        load_script(arg, force_unrestricted=force_unrestricted)
