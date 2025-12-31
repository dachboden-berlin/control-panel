from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import tempfile
import ast

from controlpanel.linting.restricted_checker import RestrictedPythonChecker

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"
UPLOAD_DIR = Path("./userscripts")
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def run_lint(code: str) -> list[dict]:
    """
    Runs RestrictedPythonChecker linter and returns a list of issues.
    """
    issues = []

    with tempfile.NamedTemporaryFile("w+", suffix=".py") as f:
        f.write(code)
        f.flush()
        filename = f.name

        # Step 1: Try parsing the AST
        try:
            tree = ast.parse(code, filename=filename)
        except SyntaxError as e:
            return [{
                "line": e.lineno or 0,
                "column": e.offset or 0,
                "message": f"SyntaxError: {e.msg}"
            }]

        # Step 2: Run checker
        checker = RestrictedPythonChecker(tree=tree, filename=filename, always_check=True)
        for lineno, col_offset, message, _ in checker.run():
            issues.append({
                "line": lineno,
                "column": col_offset,
                "message": message
            })

    return issues


@app.get("/")
async def index(request: Request):
    msg = request.cookies.get("upload_msg", "")
    cls = request.cookies.get("upload_class", "")

    response = templates.TemplateResponse(
        "index.html",
        {"request": request, "message": msg, "message_class": cls}
    )

    if msg:
        response.delete_cookie("upload_msg")
        response.delete_cookie("upload_class")

    return response


@app.post("/lint")
async def lint(code: str = Form(...)):
    """
    POST endpoint to lint code from the editor.
    """
    issues = run_lint(code)
    return {"results": issues}


@app.post("/upload")
async def upload(
    filename: str = Form(...),
    code: str = Form(...)
):
    code = code.replace("\r\n", "\n").replace("\r", "\n")

    issues = run_lint(code)
    if issues:
        return {
            "status": "error",
            "message": "Upload failed: Code did not pass linting."
        }

    final_name = Path(filename).stem + ".py"
    target_path = UPLOAD_DIR / final_name

    if target_path.exists():
        return {
            "status": "error",
            "message": f"Upload failed: '{final_name}' already exists."
        }

    target_path.write_text(code, encoding="utf-8")

    return {
        "status": "success",
        "message": f"Upload successful ({final_name})"
    }
