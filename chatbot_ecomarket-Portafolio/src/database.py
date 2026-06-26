"""
Módulo de base de datos para EcoMarket.
Gestiona la conexión y creación de la BD SQLite.
"""
import sqlite3
import os
import unicodedata
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ecomarket.db')


def normalizar_texto(texto: str) -> str:
    """Quita acentos y pasa a minúsculas para búsquedas flexibles."""
    texto = unicodedata.normalize('NFD', (texto or '').lower())
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn')


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Obtiene conexión a la base de datos."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def obtener_categorias() -> list[str]:
    """Devuelve las categorías disponibles en la BD."""
    conn = get_connection()
    categorias = [
        row[0] for row in conn.execute(
            'SELECT DISTINCT categoria FROM productos ORDER BY categoria'
        )
    ]
    conn.close()
    return categorias


def obtener_info_bd() -> dict:
    """Resumen de la BD para comprobar que Streamlit lee los datos actuales."""
    path = os.path.abspath(DB_PATH)
    if not os.path.exists(path):
        return {'path': path, 'existe': False}

    conn = get_connection(path)
    info = {
        'path': path,
        'existe': True,
        'productos': conn.execute('SELECT COUNT(*) FROM productos').fetchone()[0],
        'pedidos': conn.execute('SELECT COUNT(*) FROM pedidos').fetchone()[0],
        'modificado': datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S'),
        'categorias': obtener_categorias(),
    }
    conn.close()
    return info
