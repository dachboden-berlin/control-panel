import pathlib
import types
import sys
import builtins
import importlib
import importlib.util
import importlib.abc

SCRIPT_DIR = pathlib.Path("./userscripts")
WHITELIST_PATH = SCRIPT_DIR / "whitelist.txt"
try:
    WHITELIST: set[str] = set(WHITELIST_PATH.read_text().splitlines())
except FileNotFoundError:
    WHITELIST = set()


class UserScriptsFinder(importlib.abc.MetaPathFinder):
    """This MetaPathFinder finds userscripts, and imports them as userscript.fullname"""
    def find_spec(self, fullname, path, target=None):
        # Only handle top-level names in userscripts
        if "." not in fullname:
            candidate = SCRIPT_DIR.resolve() / f"{fullname}.py"
            if candidate.exists():
                spec = importlib.util.spec_from_file_location(
                    f"userscripts.{fullname}", candidate
                )
                return spec
        return None

# Prepend our finder to meta path
sys.meta_path.insert(0, UserScriptsFinder())


def load_script_restricted(name) -> types.ModuleType | None:
    """Load the given script in restricted mode using RestrictedPython"""
    from RestrictedPython import compile_restricted
    import warnings
    from .load_scripts_helper import make_globals


    script_path = (SCRIPT_DIR / name).with_suffix(".py")
    if not script_path.is_file():
        print(f"Failed to load {name}: file could not be found.")
        return None

    source_code = script_path.read_text()
    name = script_path.stem

    try:
        # Here we suppress a Syntax Warning because we are not using RestrictedPython's PrintCollector as intended.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r".*Prints, but never reads 'printed' variable.*",
                category=SyntaxWarning
            )
            bytecode = compile_restricted(source_code, filename=name, mode="exec")
    except SyntaxError as e:
        print(f"Failed to compile {name}: {e}")
        return None

    module_name = f"userscripts.{name}"
    module = types.ModuleType(module_name)

    module.__dict__.update(make_globals(name))
    module.__dict__["__name__"] = module_name

    try:
        exec(bytecode, module.__dict__, module.__dict__)
    except Exception as e:
        print(f"Failed to import {name}: {e}")
        return None

    sys.modules[module_name] = module

    print(f"Loaded {name} (restricted mode)")
    setattr(sys.modules["userscripts"], name, module)
    return module


def load_script_unrestricted(name) -> types.ModuleType | None:
    """Load the given script in "unrestricted mode" by simply importing it as-is"""
    try:
        real_print = print  # Save the real print

        def print_override(*args: str, sep: str | None = " ", end: str | None = "\n", file=None, flush=False) -> None:
            """Custom print function that inserts the name of the script before the given args"""
            # TODO: Joining the strings is a hacky workaround until the dev console can properly display multi-arg print
            real_print(f"{name}: {sep.join(args)}", end=end, file=file, flush=flush)
            # real_print(f"{name}:", *args, sep=sep, end=end, file=file, flush=flush)  # Once fixed, use this instead

        # Override globally
        builtins.print = print_override

        try:
            module = __import__(f"userscripts.{name}", fromlist=[""])
        finally:
            # Restore original print
            builtins.print = real_print

        module.__dict__['print'] = print_override  # Ensure that all future uses of print will use our custom print function

        print(f"Loaded {name} (unrestricted)")
        return module
    except ImportError as e:
        print(f"Failed to import {name}: {e}")
        return None


def load_script(script: str, unrestricted: bool | None = None) -> types.ModuleType | None:
    """Load the given script. If unrestricted is set to either True or False, import in unrestricted or restricted mode.
    If unrestricted is left to None, import unrestricted if whitelisted, otherwise import restricted.
    Return the module if import was successful, otherwise return None."""
    if unrestricted is None:
        unrestricted = script in WHITELIST

    if f"userscripts.{script}" in sys.modules:
        print(f"{script} already loaded!")
        return sys.modules[f"userscripts.{script}"]
    if unrestricted:
        return load_script_unrestricted(script)
    else:
        return load_script_restricted(script)


def load_scripts(scripts: list[str], override_unrestricted: bool = False) -> None:
    try:
        import RestrictedPython
    except ModuleNotFoundError:
        print("Importing all scripts in unrestricted mode as RestrictedPython is not installed. (optional dependency)")
        override_unrestricted = True  # force unrestricted if RestrictedPython is missing

    for script in scripts:
        load_script(script, unrestricted=override_unrestricted or script in WHITELIST)
