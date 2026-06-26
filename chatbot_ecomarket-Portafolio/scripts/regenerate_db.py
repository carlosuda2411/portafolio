"""Actualiza data/ecomarket.db ejecutando el notebook 01.

Por defecto (RESET_DB=False en el notebook) conserva pedidos, detalle,
devoluciones y tickets; solo refresca catálogo y promociones.

Para borrar todo y empezar de cero, pon RESET_DB=True en la celda de conexión.
"""
import json
import sqlite3
import os
import random
import sys
import types
from datetime import datetime, timedelta

NOTEBOOK = os.path.join(os.path.dirname(__file__), "..", "notebooks", "01_base_datos.ipynb")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ecomarket.db")


class _FakeSeries:
    def __getitem__(self, key):
        return self

    def value_counts(self):
        return self

    def nunique(self):
        return 0

    def __repr__(self):
        return ""


class _FakePD:
    @staticmethod
    def read_sql(*args, **kwargs):
        return _FakeSeries()


sys.modules.setdefault("pandas", types.ModuleType("pandas"))
sys.modules["pandas"].read_sql = _FakePD.read_sql

with open(NOTEBOOK, encoding="utf-8") as f:
    nb = json.load(f)

code_cells = [
    "".join(cell["source"])
    for cell in nb["cells"]
    if cell["cell_type"] == "code"
]

# Las celdas usan rutas relativas al directorio notebooks/
os.chdir(os.path.dirname(NOTEBOOK))
namespace = {"__name__": "__main__"}
for i, code in enumerate(code_cells, 1):
    exec(compile(code, f"01_base_datos.ipynb:cell_{i}", "exec"), namespace)

print(f"\nVerificación: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
print("Productos:", conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0])
for row in conn.execute("SELECT nombre FROM productos WHERE nombre LIKE '%Lasa%'"):
    print(" -", row[0])
conn.close()
