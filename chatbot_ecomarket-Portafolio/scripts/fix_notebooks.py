"""Repara notebooks para que GitHub pueda renderizarlos (nbformat válido)."""
import os
import sys

import nbformat
from nbformat.validator import normalize, validate

NOTEBOOKS_DIR = os.path.join(os.path.dirname(__file__), "..", "notebooks")


def fix_notebook(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    normalize(nb)

    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") == "stream" and "name" not in output:
                output["name"] = "stdout"
            if output.get("output_type") == "execute_result":
                output.setdefault("metadata", {})
                if "execution_count" not in output and cell.get("execution_count") is not None:
                    output["execution_count"] = cell["execution_count"]
            if output.get("output_type") == "display_data":
                output.setdefault("metadata", {})

    validate(nb)

    with open(path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)


def main() -> int:
    fixed = 0
    errors = []

    for name in sorted(os.listdir(NOTEBOOKS_DIR)):
        if not name.endswith(".ipynb"):
            continue
        path = os.path.join(NOTEBOOKS_DIR, name)
        try:
            fix_notebook(path)
            print(f"OK  {name}")
            fixed += 1
        except Exception as exc:
            print(f"ERR {name}: {exc}")
            errors.append(name)

    print(f"\nReparados: {fixed}/{fixed + len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
