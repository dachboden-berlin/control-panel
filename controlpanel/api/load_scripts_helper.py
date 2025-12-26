import RestrictedPython.Eval
from RestrictedPython import safe_builtins, utility_builtins, limited_builtins
from typing import Any
import types
import controlpanel.api as api


controlpanel_fake = types.SimpleNamespace(api=api)  # Fake controlpanel namespace that only allows access to API


ALLOWED_MODULES = {
    'math': __import__('math'),
    'random': __import__('random'),
    'enum': __import__('enum'),
    'controlpanel': controlpanel_fake,
    'controlpanel.api': api,
}


def safe_import(name: str, globals=None, locals=None, fromlist=(), level=0):
    if name in ALLOWED_MODULES:
        return ALLOWED_MODULES[name]

    if f"userscripts.{name}" in api.services.loaded_scripts:
        return api.services.loaded_scripts[f"userscripts.{name}"]

    from .load_scripts import load_script
    try:
        return load_script(name)
    except FileNotFoundError:
        pass

    raise ImportError(f"Import '{name}' is not allowed.")


def safe_getattr(obj: Any, name: str) -> Any:
    if name.startswith("_"):
        raise AttributeError("Access to private attributes is forbidden.")

    return getattr(obj, name)


def safe_write(obj):
    """
    RestrictedPython requires a write-guard, but it is safe to allow writes
    to objects you explicitly place into the execution namespace.
    """
    return obj


def safe_inplacevar(op: str, a, b):
    if op == "+=":
        return a + b
    elif op == "-=":
        return a - b
    elif op == "*=":
        return a * b
    elif op == "/=":
        return a / b
    elif op == "//=":
        return a // b
    raise ValueError(f"{op} is not a valid operation.")


def make_globals() -> dict[str, Any]:
    g = {}

    # Builtins
    custom_safe_inbuilts = dict(safe_builtins)
    custom_safe_inbuilts["__import__"] = safe_import

    # g.update(safe_builtins)
    g['__builtins__'] = custom_safe_inbuilts

    # Allowed utility functions
    g.update(utility_builtins)
    g.update(limited_builtins)

    # Guards
    g['_getattr_'] = RestrictedPython.Guards.safer_getattr
    g['_getitem_'] = lambda obj, key: obj[key]
    g['_getiter_'] = RestrictedPython.Eval.default_guarded_getiter
    g['_iter_unpack_sequence_'] = RestrictedPython.Guards.guarded_iter_unpack_sequence
    g['_unpack_sequence_'] = RestrictedPython.Guards.guarded_unpack_sequence
    g['_write_'] = lambda x: x
    g['_inplacevar_'] = safe_inplacevar
    g['__import__'] = safe_import
    g['__metaclass__'] = type  # needs to be set for classes to work

    return g
