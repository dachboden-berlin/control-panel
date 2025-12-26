import pathlib
import types
from RestrictedPython import compile_restricted
import controlpanel
import sys


SCRIPT_DIR = pathlib.Path(__file__).parent.parent.parent / "userscripts"


def load_script(name: str) -> types.ModuleType:
    from .load_scripts_helper import make_globals

    script_path = (SCRIPT_DIR / name).with_suffix(".py")
    if not script_path.is_file():
        raise FileNotFoundError(f"{script_path} is not a file")

    source_code = script_path.read_text()
    name = script_path.stem

    bytecode = compile_restricted(source_code, filename=name, mode="exec")

    module_name = f"userscripts.{name}"
    module = types.ModuleType(module_name)

    module.__dict__.update(make_globals())
    module.__dict__["__name__"] = module_name

    exec(bytecode, module.__dict__, module.__dict__)

    sys.modules[module_name] = module
    controlpanel.api.services.loaded_scripts[module_name] = module

    print(f"Loaded {module.__name__}")
    return module


def load_scripts(args: list[str]) -> None:
    for arg in args:
        load_script(arg)
