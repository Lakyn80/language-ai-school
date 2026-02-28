import re
from pathlib import Path


MODULES_ROOT = Path("backend/app/modules")
FORBIDDEN_DB_IMPORTS = (
    "from app.db.session import",
    "import app.db.session",
    "SessionLocal",
)
FROM_IMPORT_RE = re.compile(
    r"^\s*from\s+app\.modules\.([a-zA-Z_]\w*)\.([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)\s+import\s+"
)
DIRECT_IMPORT_RE = re.compile(
    r"^\s*import\s+app\.modules\.([a-zA-Z_]\w*)\.([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)"
)


def test_modules_do_not_import_internal_files_of_other_modules():
    violations: list[str] = []

    for file in MODULES_ROOT.rglob("*.py"):
        relative = file.relative_to(MODULES_ROOT)
        current_module = relative.parts[0]

        for line_no, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().startswith("#"):
                continue

            match = FROM_IMPORT_RE.match(line) or DIRECT_IMPORT_RE.match(line)
            if match is None:
                continue

            imported_module = match.group(1)
            imported_submodule = match.group(2)

            if imported_module != current_module:
                violations.append(
                    f"{relative}:{line_no} imports app.modules.{imported_module}.{imported_submodule}"
                )
                continue

            violations.append(
                f"{relative}:{line_no} uses absolute same-module import; use relative import"
            )

    assert not violations, "Modularity violations:\n" + "\n".join(violations)


def test_modules_do_not_depend_on_db_session_internals():
    violations: list[str] = []

    for file in MODULES_ROOT.rglob("*.py"):
        content = file.read_text(encoding="utf-8")
        for marker in FORBIDDEN_DB_IMPORTS:
            if marker in content:
                violations.append(f"{file.relative_to(MODULES_ROOT)} contains '{marker}'")

    assert not violations, "Database boundary violations:\n" + "\n".join(violations)
