import ast
from pathlib import Path
from controlpanel.api.load_scripts_helper import ALLOWED_MODULES

class RestrictedPythonChecker:
    name = "restrictedpython-checker"
    version = "0.1.0"

    def __init__(self, tree, filename, always_check = False):
        self.tree = tree
        self.filename = filename
        self.always_check = always_check

    def run(self):
        if not self.always_check and not self._in_userscripts_dir():
            return

        for node in ast.walk(self.tree):

            # -----------------------------------------------------------
            # RSP001 – AnnAssign forbidden
            # -----------------------------------------------------------
            if isinstance(node, ast.AnnAssign):
                yield (
                    node.lineno,
                    node.col_offset,
                    "RSP001 AnnAssign is not allowed in userscripts (RestrictedPython).",
                    type(self),
                )

            # -----------------------------------------------------------
            # RSP002 – Ellipsis forbidden
            # -----------------------------------------------------------
            if isinstance(node, ast.Ellipsis):
                yield (
                    node.lineno,
                    node.col_offset,
                    "RSP002 Ellipsis (...) is not allowed in userscripts (RestrictedPython).",
                    type(self),
                )

            # -----------------------------------------------------------
            # RSP003 – Variable names beginning with "_" forbidden
            # (assignment targets)
            # -----------------------------------------------------------
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id.startswith("_"):
                    yield (
                        node.lineno,
                        node.col_offset,
                        "RSP003 Variables may not start with '_' in userscripts (RestrictedPython).",
                        type(self),
                    )

            # -----------------------------------------------------------
            # RSP004 – Argument names beginning with "_" forbidden
            # -----------------------------------------------------------
            if isinstance(node, ast.arg):
                if node.arg.startswith("_"):
                    yield (
                        node.lineno,
                        node.col_offset,
                        "RSP004 Argument names may not start with '_' in userscripts (RestrictedPython).",
                        type(self),
                    )

            # -----------------------------------------------------------
            # RSP006 – Attribute access allowed, but attribute *names* starting with "_" forbidden
            # e.g., obj._secret → forbidden
            # -----------------------------------------------------------
            if isinstance(node, ast.Attribute):
                if node.attr.startswith("_"):
                    yield (
                        node.lineno,
                        node.col_offset,
                        f"RSP006 Attribute '{node.attr}' starting with '_' is forbidden in RestrictedPython.",
                        type(self),
                    )

            # -----------------------------------------------------------
            # RSP007 – Function or class names starting with "_" forbidden
            # -----------------------------------------------------------
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                if node.name.startswith("_") and not self._is_dunder(node.name):
                    yield (
                        node.lineno,
                        node.col_offset,
                        f"RSP007 Function name '{node.name}' may not start with '_' in RestrictedPython.",
                        type(self),
                    )

            if isinstance(node, ast.ClassDef):
                if node.name.startswith("_") and not self._is_dunder(node.name):
                    yield (
                        node.lineno,
                        node.col_offset,
                        f"RSP007 Class name '{node.name}' may not start with '_' in RestrictedPython.",
                        type(self),
                    )

            # -----------------------------------------------------------
            # RSP008 – Import checking
            # -----------------------------------------------------------
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] not in ALLOWED_MODULES:
                        yield (
                            node.lineno,
                            node.col_offset,
                            f"RSP008 Import of '{alias.name}' is not allowed.",
                            type(self),
                        )

            if isinstance(node, ast.ImportFrom):
                module_name = node.module.split(".")[0] if node.module else ""
                if module_name not in ALLOWED_MODULES:
                    yield (
                        node.lineno,
                        node.col_offset,
                        f"RSP008 Import from '{module_name}' is not allowed.",
                        type(self),
                    )

    def _in_userscripts_dir(self):
        try:
            parts = Path(self.filename).parts
            return "userscripts" in parts
        except Exception:
            return False

    @staticmethod
    def _is_dunder(name: str) -> bool:
        return name.startswith("__") and name.endswith("__")
