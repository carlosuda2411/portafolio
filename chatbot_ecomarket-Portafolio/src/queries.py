"""
Funciones de consulta a la base de datos EcoMarket.
Estas funciones son invocadas por el agente LLM y el NLP local.
"""
import json
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from .database import get_connection, normalizar_texto


def _similitud_tokens(termino: str, texto: str) -> bool:
    """Coincidencia flexible por palabras (evita pan ⊂ panales, gel ⊂ congelados)."""
    t = normalizar_texto(termino)
    n = normalizar_texto(texto)
    palabras_n = n.split()

    if t == n:
        return True
    if n.startswith(t + ' '):
        return True
    if t in palabras_n:
        return True
    if SequenceMatcher(None, t, n).ratio() >= 0.82:
        return True
    for palabra in palabras_n:
        if len(palabra) >= 4 and SequenceMatcher(None, t, palabra).ratio() >= 0.86:
            return True
    term_palabras = [p for p in t.split() if len(p) >= 3]
    if len(term_palabras) > 1:
        set_n = set(palabras_n)
        if all(
            p in set_n or any(
                len(w) >= 4 and SequenceMatcher(None, p, w).ratio() >= 0.86
                for w in palabras_n
            )
            for p in term_palabras
        ):
            return True
    return False


def _puntuar_relevancia(termino: str, nombre: str) -> tuple:
    t = normalizar_texto(termino)
    n = normalizar_texto(nombre)
    palabras = n.split()
    if n == t:
        return (0, len(n), n)
    if n.startswith(t + ' '):
        return (1, len(n), n)
    if t in palabras:
        return (2, palabras.index(t), len(n), n)
    return (4, len(n), n)


def _filtrar_por_nombre(cursor, nombre: str, columnas: str) -> list[dict]:
    """Filtra productos por nombre ignorando mayúsculas, acentos y pequeñas variaciones."""
    termino = normalizar_texto(nombre)
    cursor.execute(f'SELECT {columnas} FROM productos')
    resultados = [
        dict(row) for row in cursor.fetchall()
        if _similitud_tokens(termino, dict(row)['nombre'])
    ]
    resultados.sort(key=lambda row: _puntuar_relevancia(termino, row['nombre']))
    return resultados


_DIAS_PROMO = {
    'lunes': 0,
    'martes': 1,
    'miercoles': 2,
    'jueves': 3,
    'viernes': 4,
    'sabado': 5,
    'domingo': 6,
}


def _dias_promo_desde_descripcion(descripcion: str) -> list[int]:
    """Extrae días de la semana mencionados en la descripción (ej. 'los martes')."""
    norm = normalizar_texto(descripcion)
    dias = []
    for nombre, num in _DIAS_PROMO.items():
        if re.search(rf'\b{re.escape(nombre)}\b', norm):
            dias.append(num)
    return sorted(set(dias))


def _promo_aplicable_hoy(promo: dict, fecha: datetime | None = None) -> bool:
    """True si la promo aplica hoy (fecha vigente + restricción de día si la hay)."""
    dias = _dias_promo_desde_descripcion(promo.get('descripcion', ''))
    if not dias:
        return True
    fecha = fecha or datetime.now()
    return fecha.weekday() in dias


def _fetch_promo_producto(cursor, producto_id: int) -> dict | None:
    """Promo vigente por fechas, sin filtrar por día de la semana."""
    hoy = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        'SELECT descripcion, descuento_porcentaje FROM promociones '
        'WHERE producto_id = ? AND activa = 1 '
        'AND fecha_inicio <= ? AND fecha_fin >= ?',
        (producto_id, hoy, hoy)
    )
    promo = cursor.fetchone()
    return dict(promo) if promo else None


def _obtener_promo_producto(cursor, producto_id: int) -> dict | None:
    """Promo aplicable hoy (para precios y pedidos)."""
    promo = _fetch_promo_producto(cursor, producto_id)
    if promo and not _promo_aplicable_hoy(promo):
        return None
    return promo


def _aplicar_precio_promo(producto: dict, promo_raw: dict | None) -> dict:
    """Enriquece producto con promo, precio_efectivo y si aplica hoy."""
    if promo_raw:
        producto['promocion'] = promo_raw
        aplicable = _promo_aplicable_hoy(promo_raw)
        producto['promocion_aplicable_hoy'] = aplicable
    else:
        aplicable = False
    producto['precio_efectivo'] = _precio_efectivo(
        producto['precio'],
        promo_raw if promo_raw and aplicable else None,
    )
    return producto


def _precio_efectivo(precio: float, promo: dict | None) -> float:
    if not promo:
        return precio
    return round(precio * (1 - promo['descuento_porcentaje'] / 100), 2)


COSTO_DOMICILIO = 2.00
PROMOS_DESTACADAS = 5


def _preparar_items_pedido(
    cursor, productos_cantidades: list
) -> tuple[list[dict], list[str], float]:
    """Calcula líneas de pedido con promos aplicadas. Devuelve (items, errores, subtotal)."""
    items_pedido = []
    errores = []
    subtotal = 0.0

    for item in productos_cantidades:
        nombre_prod = item.get('nombre', '')
        cantidad = item.get('cantidad', 1)

        coincidencias = _filtrar_por_nombre(
            cursor, nombre_prod, 'id, nombre, precio, stock'
        )
        producto = coincidencias[0] if coincidencias else None

        if not producto:
            errores.append(f'Producto "{nombre_prod}" no encontrado')
            continue

        prod_dict = dict(producto)
        promo = _obtener_promo_producto(cursor, prod_dict['id'])
        precio_unitario = _precio_efectivo(prod_dict['precio'], promo)

        if prod_dict['stock'] < cantidad:
            errores.append(
                f'{prod_dict["nombre"]}: stock insuficiente (disponible: {prod_dict["stock"]})'
            )
            continue

        linea_subtotal = round(precio_unitario * cantidad, 2)
        linea = {
            'producto_id': prod_dict['id'],
            'nombre': prod_dict['nombre'],
            'cantidad': cantidad,
            'precio_catalogo': prod_dict['precio'],
            'precio_unitario': precio_unitario,
            'subtotal': linea_subtotal,
        }
        if promo:
            linea['promocion'] = promo
        items_pedido.append(linea)
        subtotal += linea_subtotal

    subtotal = round(sum(i['subtotal'] for i in items_pedido), 2)
    return items_pedido, errores, subtotal


def _productos_por_categorias(cursor, categorias: list[str]) -> list[dict]:
    """Busca productos cuyo nombre de categoría coincide (exacto o parcial)."""
    if not categorias:
        cursor.execute(
            'SELECT id, nombre, categoria, precio, stock, descripcion, unidad '
            'FROM productos WHERE stock > 0 ORDER BY precio ASC'
        )
        return [dict(row) for row in cursor.fetchall()]
    condiciones = ' OR '.join(['LOWER(categoria) LIKE LOWER(?)'] * len(categorias))
    params = [f'%{cat}%' for cat in categorias]
    cursor.execute(
        f'SELECT id, nombre, categoria, precio, stock, descripcion, unidad '
        f'FROM productos WHERE stock > 0 AND ({condiciones}) '
        f'ORDER BY categoria, nombre',
        params,
    )
    return [dict(row) for row in cursor.fetchall()]


# === Criterios para listas de compra ===
CRITERIOS_LISTA = {
    "saludable": {
        "categorias": ["Frutas y Verduras", "Lacteos"],
        "palabras_clave": ["integral", "natural", "orgánico", "organico", "sin azúcar", "sin azucar", "verde", "fresco", "fresca", "yogur", "almendra"],
        "excluir_palabras": ["coca-cola", "coca cola", "cerveza", "chorizo", "chocolate", "croissant", "mantequilla", "pasta", "atun", "galletas"],
        "descripcion": "Productos frescos, naturales e integrales"
    },
    "vegano": {
        "categorias": ["Frutas y Verduras", "Bebidas", "Despensa"],
        "palabras_clave": ["vegetal", "almendra", "verde", "organico", "orgánico"],
        "excluir_palabras": ["leche entera", "yogur", "queso", "mantequilla", "pollo", "carne", "salmon", "jamon", "chorizo", "atun", "croissant"],
        "descripcion": "Productos de origen 100% vegetal"
    },
    "proteico": {
        "categorias": ["Carnes", "Lacteos"],
        "palabras_clave": ["pollo", "salmon", "carne", "yogur", "queso", "leche", "atun"],
        "excluir_palabras": [],
        "descripcion": "Productos altos en proteína"
    },
    "economico": {
        "categorias": [],  # Todas las categorías
        "palabras_clave": [],
        "excluir_palabras": [],
        "precio_max": 3.0,
        "descripcion": "Productos con mejor precio (menos de 3€)"
    },
    "sin_gluten": {
        "categorias": ["Frutas y Verduras", "Carnes", "Lacteos", "Bebidas"],
        "palabras_clave": ["arroz", "maiz"],
        "excluir_palabras": ["pan ", "baguette", "croissant", "pasta", "galletas", "cereales"],
        "descripcion": "Productos libres de gluten"
    },
    "desayuno": {
        "categorias": ["Lacteos", "Panaderia", "Frutas y Verduras"],
        "palabras_clave": ["leche", "yogur", "pan ", "cafe", "zumo", "cereales", "miel", "galletas", "platano", "manzana"],
        "excluir_palabras": ["cerveza", "detergente", "coca-cola", "coca cola", "pasta", "atun", "chorizo", "carne", "pollo", "salmon", "arroz", "aceite", "baguette", "tortilla", "infantil"],
        "descripcion": "Productos ideales para el desayuno"
    },
    "desayuno_saludable": {
        "categorias": ["Frutas y Verduras", "Lacteos"],
        "palabras_clave": ["yogur", "integral", "cereales", "miel", "cafe", "zumo", "leche de almendra", "platano", "manzana", "naranja", "natural"],
        "excluir_palabras": ["cerveza", "detergente", "coca-cola", "coca cola", "pasta", "atun", "chorizo", "carne", "pollo", "salmon", "arroz", "aceite", "croissant", "mantequilla", "chocolate", "galletas", "tortilla", "baguette", "queso"],
        "descripcion": "Desayuno saludable: frutas, yogur natural, cereales integrales y bebidas sin azúcar"
    },
}


def _relevancia_lista(producto: dict, palabras_clave: list[str]) -> int:
    nombre_lower = producto['nombre'].lower()
    desc_lower = (producto.get('descripcion') or '').lower()
    return sum(
        1 for palabra in palabras_clave
        if palabra.lower().strip() in nombre_lower or palabra.lower().strip() in desc_lower
    )


def _enriquecer_producto_lista(cursor, producto: dict) -> dict:
    promo_raw = _fetch_promo_producto(cursor, producto['id'])
    return _aplicar_precio_promo(producto, promo_raw)


def _seleccionar_productos_lista(
    productos: list[dict],
    presupuesto_max: float | None,
    max_items: int = 10,
) -> list[dict]:
    """Selecciona productos por relevancia respetando presupuesto (precio con promo)."""
    if not presupuesto_max or presupuesto_max <= 0:
        return productos[:max_items]

    seleccionados = []
    total = 0.0
    for producto in productos:
        if len(seleccionados) >= max_items:
            break
        precio = producto['precio_efectivo']
        if round(total + precio, 2) > presupuesto_max:
            continue
        seleccionados.append(producto)
        total += precio
    return seleccionados


def buscar_producto(nombre: str) -> list[dict]:
    """Busca productos por nombre (parcial, ignora mayúsculas y acentos)."""
    conn = get_connection()
    cursor = conn.cursor()
    resultados = _filtrar_por_nombre(
        cursor, nombre,
        'id, nombre, categoria, precio, stock, descripcion, unidad'
    )

    for prod in resultados:
        promo_raw = _fetch_promo_producto(cursor, prod['id'])
        _aplicar_precio_promo(prod, promo_raw)

    conn.close()
    return resultados


# Subcategorías dentro de "Frutas y Verduras" (sin cambiar esquema BD)
_PALABRAS_FRUTA = (
    'manzana', 'platano', 'plátano', 'naranja', 'aguacate', 'pera', 'melon', 'melón',
    'sandia', 'sandía', 'fresa', 'uvas', 'uva', 'limon', 'limón', 'mandarina', 'kiwi',
)
_PALABRAS_VERDURA = (
    'tomate', 'lechuga', 'zanahoria', 'cebolla', 'pimiento', 'pepino', 'calabacin',
    'calabacín', 'brocoli', 'brócoli', 'espinaca', 'acelga', 'patata', 'col', 'apio',
)


def _clasificar_fruta_verdura(nombre: str) -> str | None:
    """Devuelve 'frutas', 'verduras' o None si no aplica."""
    norm = normalizar_texto(nombre)
    palabras = norm.split()
    for p in _PALABRAS_FRUTA:
        p_norm = normalizar_texto(p)
        if p_norm in palabras or norm.startswith(p_norm + ' '):
            return 'frutas'
    for p in _PALABRAS_VERDURA:
        p_norm = normalizar_texto(p)
        if p_norm in palabras or norm.startswith(p_norm + ' '):
            return 'verduras'
    return None


def buscar_por_categoria(categoria: str, subtipo: str = None) -> list[dict]:
    """Lista productos de una categoría. subtipo: 'frutas' o 'verduras' dentro de Frutas y Verduras."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, nombre, categoria, precio, stock, unidad '
        'FROM productos WHERE LOWER(categoria) LIKE LOWER(?) AND stock > 0 '
        'ORDER BY nombre',
        (f'%{categoria}%',)
    )
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if subtipo in ('frutas', 'verduras'):
        resultados = [
            p for p in resultados
            if _clasificar_fruta_verdura(p['nombre']) == subtipo
        ]

    return resultados[:10]


def consultar_pedidos(email: str) -> list[dict]:
    """Obtiene pedidos de un cliente por email."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, fecha_pedido, estado, total, direccion_envio, '
        'fecha_entrega_estimada FROM pedidos '
        'WHERE LOWER(email_cliente) = LOWER(?) ORDER BY fecha_pedido DESC',
        (email,)
    )
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados


def obtener_detalle_pedido(pedido_id: int) -> dict:
    """Detalle completo de un pedido."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pedidos WHERE id = ?', (pedido_id,))
    pedido = cursor.fetchone()
    if not pedido:
        conn.close()
        return {'error': 'Pedido no encontrado'}
    cursor.execute(
        'SELECT p.nombre, dp.cantidad, dp.precio_unitario, '
        '(dp.cantidad * dp.precio_unitario) as subtotal '
        'FROM detalle_pedido dp JOIN productos p ON p.id = dp.producto_id '
        'WHERE dp.pedido_id = ?',
        (pedido_id,)
    )
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {'pedido': dict(pedido), 'items': items}


def _promo_aplicable_en_dia(promo: dict, dia: str) -> bool:
    """True si la promo aplica ese día (sin día en descripción → todos los días)."""
    dias_promo = _dias_promo_desde_descripcion(promo.get('descripcion', ''))
    if not dias_promo:
        return True
    dia_num = _DIAS_PROMO.get(normalizar_texto(dia.strip()))
    return dia_num in dias_promo if dia_num is not None else True


def _promo_exclusiva_dia(promo: dict, dia: str) -> bool:
    """True solo si la promo está ligada a ese día concreto (no promos habituales)."""
    dias_promo = _dias_promo_desde_descripcion(promo.get('descripcion', ''))
    if not dias_promo:
        return False
    dia_num = _DIAS_PROMO.get(normalizar_texto(dia.strip()))
    return dia_num in dias_promo if dia_num is not None else False


def _contar_promos_habituales(promos: list[dict]) -> int:
    return sum(1 for p in promos if not _dias_promo_desde_descripcion(p.get('descripcion', '')))


def _enriquecer_promo(promo: dict) -> dict:
    aplicable = _promo_aplicable_hoy({'descripcion': promo['descripcion']})
    promo['aplicable_hoy'] = aplicable
    promo['precio_hoy'] = (
        promo['precio_con_descuento'] if aplicable else promo['precio_original']
    )
    return promo


def obtener_promociones(
    categoria: str = None,
    producto: str = None,
    dia: str = None,
    solo_aplicables_hoy: bool = False,
    todas: bool = False,
) -> dict:
    """Promociones vigentes. Por defecto top 5; con filtros o todas=True devuelve el listado completo."""
    conn = get_connection()
    cursor = conn.cursor()
    hoy = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        'SELECT pr.id, p.nombre as producto, p.categoria, pr.descripcion, '
        'pr.descuento_porcentaje, pr.fecha_fin, p.precio as precio_original, '
        'ROUND(p.precio * (1 - pr.descuento_porcentaje/100), 2) as precio_con_descuento '
        'FROM promociones pr JOIN productos p ON p.id = pr.producto_id '
        'WHERE pr.activa = 1 AND pr.fecha_inicio <= ? AND pr.fecha_fin >= ? '
        'ORDER BY pr.descuento_porcentaje DESC, p.nombre',
        (hoy, hoy)
    )
    todas_las_promos = [_enriquecer_promo(dict(row)) for row in cursor.fetchall()]
    conn.close()

    filtrado = bool(categoria or producto or dia or solo_aplicables_hoy or todas)
    resultados = todas_las_promos
    promos_habituales = _contar_promos_habituales(todas_las_promos)
    if categoria:
        cat_norm = normalizar_texto(categoria)
        resultados = [
            p for p in resultados
            if cat_norm in normalizar_texto(p['categoria'])
        ]
    if producto:
        termino = normalizar_texto(producto)
        resultados = [
            p for p in resultados
            if _similitud_tokens(termino, p['producto'])
        ]
    if dia:
        resultados = [p for p in resultados if _promo_exclusiva_dia(p, dia)]
    if solo_aplicables_hoy:
        resultados = [p for p in resultados if p['aplicable_hoy']]

    vista_resumida = not filtrado
    if vista_resumida:
        resultados = resultados[:PROMOS_DESTACADAS]

    respuesta = {
        'promociones': resultados,
        'total_disponibles': len(todas_las_promos),
        'mostrando': len(resultados),
        'filtrado': filtrado,
        'vista_resumida': vista_resumida,
        'hay_mas': vista_resumida and len(todas_las_promos) > len(resultados),
    }
    if dia:
        respuesta['filtro_dia_exclusivo'] = True
        respuesta['promos_habituales_vigentes'] = promos_habituales
    return respuesta


def registrar_devolucion(pedido_id: int, email: str, motivo: str) -> dict:
    """Registra solicitud de devolución."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, estado FROM pedidos '
        'WHERE id = ? AND LOWER(email_cliente) = LOWER(?)',
        (pedido_id, email)
    )
    pedido = cursor.fetchone()
    if not pedido:
        conn.close()
        return {'error': 'Pedido no encontrado o no pertenece a este email'}
    if dict(pedido)['estado'] not in ['entregado', 'enviado']:
        conn.close()
        return {'error': f'No se puede devolver un pedido con estado: {dict(pedido)["estado"]}'}
    fecha = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        'INSERT INTO devoluciones (pedido_id, email_cliente, motivo, estado, fecha_solicitud) '
        'VALUES (?, ?, ?, "pendiente", ?)',
        (pedido_id, email, motivo, fecha)
    )
    devolucion_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {'mensaje': 'Devolución registrada', 'devolucion_id': devolucion_id, 'estado': 'pendiente'}


def consultar_devoluciones(email: str) -> list[dict]:
    """Consulta devoluciones de un cliente."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, pedido_id, motivo, estado, fecha_solicitud, comentarios '
        'FROM devoluciones WHERE LOWER(email_cliente) = LOWER(?) '
        'ORDER BY fecha_solicitud DESC',
        (email,)
    )
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados


def crear_ticket_soporte(email: str, asunto: str, descripcion: str, pedido_id: int = None) -> dict:
    """Crea ticket de soporte para derivar a humano."""
    conn = get_connection()
    cursor = conn.cursor()
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO tickets_soporte (email_cliente, asunto, descripcion, estado, fecha_creacion, pedido_id) '
        'VALUES (?, ?, ?, "abierto", ?, ?)',
        (email, asunto, descripcion, fecha, pedido_id)
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {'mensaje': 'Ticket creado. Un agente se pondrá en contacto pronto.', 'ticket_id': ticket_id}


def calcular_total_pedido(
    productos_cantidades: list, incluir_domicilio: bool = True
) -> dict:
    """
    Calcula el total de un pedido sin crearlo (promos y domicilio incluidos).
    Usar SIEMPRE para mostrar resúmenes al cliente.
    """
    conn = get_connection()
    cursor = conn.cursor()
    items, errores, subtotal = _preparar_items_pedido(cursor, productos_cantidades)
    conn.close()

    if not items:
        return {'error': 'No se pudo calcular el total', 'problemas': errores or ['Sin productos válidos']}

    costo_domicilio = COSTO_DOMICILIO if incluir_domicilio else 0.0
    resultado = {
        'items': [
            {
                'nombre': i['nombre'],
                'cantidad': i['cantidad'],
                'precio_catalogo': i['precio_catalogo'],
                'precio_unitario': i['precio_unitario'],
                'subtotal': i['subtotal'],
                **({'promocion': i['promocion']} if i.get('promocion') else {}),
            }
            for i in items
        ],
        'subtotal_productos': subtotal,
        'costo_domicilio': costo_domicilio,
        'total': round(subtotal + costo_domicilio, 2),
    }
    if errores:
        resultado['advertencias'] = errores
    return resultado


def crear_pedido(email: str, productos_cantidades: list, direccion: str) -> dict:
    """
    Crea un nuevo pedido y actualiza el stock.
    
    Args:
        email: Email del cliente
        productos_cantidades: Lista de dicts con 'nombre' y 'cantidad'
                              Ej: [{"nombre": "Leche Entera", "cantidad": 2}, {"nombre": "Pan Integral", "cantidad": 1}]
        direccion: Dirección de entrega (debe incluir ciudad: Madrid, Málaga o Valencia)
    
    Returns:
        Dict con confirmación del pedido o error
    """
    # Validar que la dirección incluya una ciudad dentro de cobertura
    CIUDADES_COBERTURA = ['madrid', 'malaga', 'málaga', 'valencia']
    direccion_lower = direccion.lower()
    ciudad_encontrada = None
    for ciudad in CIUDADES_COBERTURA:
        if ciudad in direccion_lower:
            ciudad_encontrada = ciudad
            break

    if not ciudad_encontrada:
        return {
            'error': 'Dirección fuera de cobertura',
            'mensaje': 'Lo sentimos, solo realizamos envíos a Madrid, Málaga y Valencia. '
                       'Por favor, verifica que tu dirección incluya una de estas ciudades.',
            'ciudades_disponibles': ['Madrid', 'Málaga', 'Valencia']
        }

    conn = get_connection()
    cursor = conn.cursor()

    items_pedido, errores, subtotal = _preparar_items_pedido(cursor, productos_cantidades)

    if errores:
        conn.close()
        return {'error': 'No se pudo crear el pedido', 'problemas': errores}

    if not items_pedido:
        conn.close()
        return {'error': 'No se encontraron productos válidos para el pedido'}

    # Crear el pedido
    fecha = datetime.now().strftime('%Y-%m-%d')
    fecha_entrega = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
    total_con_domicilio = round(subtotal + COSTO_DOMICILIO, 2)

    cursor.execute(
        'INSERT INTO pedidos (email_cliente, fecha_pedido, estado, total, direccion_envio, fecha_entrega_estimada) '
        'VALUES (?, ?, "confirmado", ?, ?, ?)',
        (email, fecha, total_con_domicilio, direccion, fecha_entrega)
    )
    pedido_id = cursor.lastrowid

    # Insertar detalle y actualizar stock
    for item in items_pedido:
        cursor.execute(
            'INSERT INTO detalle_pedido (pedido_id, producto_id, cantidad, precio_unitario) '
            'VALUES (?, ?, ?, ?)',
            (pedido_id, item['producto_id'], item['cantidad'], item['precio_unitario'])
        )
        cursor.execute(
            'UPDATE productos SET stock = stock - ? WHERE id = ?',
            (item['cantidad'], item['producto_id'])
        )

    conn.commit()
    conn.close()

    return {
        'mensaje': 'Pedido creado exitosamente',
        'pedido_id': pedido_id,
        'subtotal_productos': subtotal,
        'costo_domicilio': COSTO_DOMICILIO,
        'total': total_con_domicilio,
        'estado': 'confirmado',
        'metodo_pago': 'Pago contra entrega (se paga al domiciliario)',
        'fecha_entrega_estimada': fecha_entrega,
        'direccion': direccion,
        'items': [
            {
                'nombre': i['nombre'],
                'cantidad': i['cantidad'],
                'precio_unitario': i['precio_unitario'],
                'subtotal': i['subtotal'],
            }
            for i in items_pedido
        ],
    }


def generar_lista_compra(condicion: str, presupuesto_max: float = None) -> dict:
    """
    Genera una lista de compra personalizada según una condición específica.

    Args:
        condicion: Tipo de lista deseada. Opciones: saludable, vegano, proteico, 
                   economico, sin_gluten, desayuno, desayuno_saludable
        presupuesto_max: Presupuesto máximo opcional para filtrar la lista (en euros)

    Returns:
        Dict con la lista de compra sugerida, total estimado y descripción
    """
    condicion_lower = condicion.lower().strip()

    # Verificar si la condición existe
    if condicion_lower not in CRITERIOS_LISTA:
        return {
            'error': f'Condición "{condicion}" no reconocida',
            'condiciones_disponibles': list(CRITERIOS_LISTA.keys()),
            'mensaje': 'Por favor elige una de las condiciones disponibles'
        }

    criterio = CRITERIOS_LISTA[condicion_lower]
    conn = get_connection()
    cursor = conn.cursor()

    # Construir consulta según criterios
    productos_encontrados = []

    if criterio["categorias"]:
        productos_encontrados = _productos_por_categorias(cursor, criterio["categorias"])
    else:
        productos_encontrados = _productos_por_categorias(cursor, [])

    # Agregar productos por palabras clave (de otras categorías)
    if criterio["palabras_clave"]:
        ids_existentes = {p['id'] for p in productos_encontrados}
        for palabra in criterio["palabras_clave"]:
            cursor.execute(
                'SELECT id, nombre, categoria, precio, stock, descripcion, unidad '
                'FROM productos WHERE stock > 0 AND '
                '(LOWER(nombre) LIKE LOWER(?) OR LOWER(descripcion) LIKE LOWER(?))',
                (f'%{palabra}%', f'%{palabra}%')
            )
            for row in cursor.fetchall():
                prod = dict(row)
                if prod['id'] not in ids_existentes:
                    productos_encontrados.append(prod)
                    ids_existentes.add(prod['id'])

    # Excluir productos no deseados
    if criterio["excluir_palabras"]:
        productos_encontrados = [
            p for p in productos_encontrados
            if not any(
                excl.lower() in p['nombre'].lower()
                for excl in criterio["excluir_palabras"]
            )
        ]

    productos_encontrados = [
        _enriquecer_producto_lista(cursor, p) for p in productos_encontrados
    ]

    # Filtrar por precio máximo del criterio (con promos aplicadas)
    precio_max = criterio.get("precio_max")
    if precio_max:
        productos_encontrados = [
            p for p in productos_encontrados if p['precio_efectivo'] <= precio_max
        ]

    # Ordenar por relevancia antes de aplicar presupuesto
    if criterio["palabras_clave"]:
        productos_encontrados.sort(
            key=lambda p: _relevancia_lista(p, criterio["palabras_clave"]),
            reverse=True,
        )

    productos_encontrados = _seleccionar_productos_lista(
        productos_encontrados, presupuesto_max, max_items=10
    )

    conn.close()

    total = round(sum(p['precio_efectivo'] for p in productos_encontrados), 2)

    # Formatear respuesta
    lista_formateada = []
    for p in productos_encontrados:
        item = {
            'nombre': p['nombre'],
            'categoria': p['categoria'],
            'precio': p['precio'],
            'precio_efectivo': p['precio_efectivo'],
            'unidad': p['unidad'],
        }
        if p.get('promocion'):
            item['promocion'] = p['promocion']['descripcion']
            item['promocion_aplicable_hoy'] = p.get('promocion_aplicable_hoy', True)
        lista_formateada.append(item)

    resultado = {
        'condicion': condicion_lower,
        'descripcion': criterio['descripcion'],
        'cantidad_productos': len(lista_formateada),
        'total_estimado': total,
        'productos': lista_formateada,
        'nota': 'Recuerda que el pago es contra entrega. Puedes pedir estos productos directamente.',
    }
    if presupuesto_max and presupuesto_max > 0:
        resultado['presupuesto_max'] = presupuesto_max
        resultado['dentro_presupuesto'] = total <= presupuesto_max
        if not lista_formateada:
            resultado['mensaje'] = (
                f'No hay productos que encajen en el presupuesto de {presupuesto_max:.2f} €. '
                'Prueba con un presupuesto mayor o otra condición.'
            )
    return resultado
