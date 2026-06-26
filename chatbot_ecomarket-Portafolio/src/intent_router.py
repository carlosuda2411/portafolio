"""
Clasificador de intenciones flexible (sin LLM).
Combina sinónimos, coincidencia difusa y señales del catálogo.
"""
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from .database import get_connection, normalizar_texto, obtener_categorias

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')

STOPWORDS = {
    'a', 'al', 'algo', 'algun', 'alguna', 'algunos', 'algunas', 'como', 'con', 'de', 'del', 'la', 'las',
    'el', 'los', 'en', 'es', 'esta', 'este', 'estoy', 'hay', 'lo', 'me', 'mi', 'mis', 'mucho', 'muy',
    'no', 'nos', 'o', 'para', 'por', 'porfavor', 'que', 'qué', 'se', 'si', 'sí', 'sin', 'sobre', 'su',
    'sus', 'te', 'teneis', 'tenéis', 'tengo', 'tenemos', 'tiene', 'tienen', 'tienes', 'todo', 'toda', 'un', 'una',
    'uno', 'unos', 'unas', 'y', 'yo', 'vosotros', 'u', 'usted', 'ecobot', 'ecomarket', 'favor', 'please',
    'hola', 'buenas', 'podria', 'podría', 'puedes', 'puede', 'puedo', 'quisiera', 'gustaria', 'gustaría',
    'saber', 'dime', 'decir', 'ver', 'mostrar', 'mostrarme', 'listar', 'consultar', 'buscar', 'encuentro',
}

SALUDOS = {
    'hola', 'hey', 'buenas', 'buenos dias', 'buenas tardes', 'buenas noches', 'saludos',
    'que tal', 'qué tal', 'buen dia', 'buen día', 'hello', 'hi',
}

DESPEDIDAS = {
    'adios', 'adiós', 'chao', 'hasta luego', 'hasta pronto', 'nos vemos', 'bye', 'gracias', 'muchas gracias',
}

AYUDA = {
    'ayuda', 'help', 'que puedes hacer', 'qué puedes hacer', 'que sabes hacer', 'qué sabes hacer',
    'que haces', 'qué haces', 'como funciona', 'cómo funciona', 'capacidades', 'para que sirves',
    'para qué sirves', 'que me puedes', 'qué me puedes',
}

PROMOCIONES = {
    'promocion', 'promociones', 'promo', 'promos', 'oferta', 'ofertas', 'descuento', 'descuentos',
    'rebaja', 'rebajas', 'chollo', 'chollos', 'gangas', 'ganga', 'en oferta', 'precios rebajados',
}

PEDIDOS = {
    'pedido', 'pedidos', 'orden', 'ordenes', 'órdenes', 'compra', 'compras', 'envio', 'envío',
    'entrega', 'entregas', 'seguimiento', 'estado del pedido', 'estado de mi pedido', 'mis pedidos',
    'mi pedido', 'donde esta mi pedido', 'dónde está mi pedido', 'tracking',
}

CONSULTAR_PEDIDOS = {
    'mis pedidos', 'mi pedido', 'estado del pedido', 'estado de mi pedido', 'estado de pedido',
    'donde esta mi pedido', 'dónde está mi pedido', 'donde esta el pedido', 'dónde está el pedido',
    'seguimiento del pedido', 'seguimiento de mi pedido', 'tracking',
}

VERBOS_CREAR_PEDIDO = {
    'comprar', 'pedir', 'encargar', 'solicitar', 'confirmar', 'confirmo',
}

_NUMEROS_CANTIDAD_RE = (
    r'\d+|uno|una|un|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|'
    r'once|doce|trece|catorce|quince|veinte|treinta|cuarenta|cincuenta'
)
_PATRON_CANTIDAD_PEDIDO = re.compile(
    rf'(?:^|\s)(?:{_NUMEROS_CANTIDAD_RE})\s+(?:de\s+)?[\w]',
    re.I,
)

VERBOS_PRODUCTO = {
    'tienen', 'teneis', 'tenéis', 'tienes', 'venden', 'vendeis', 'vendéis', 'hay', 'busco', 'buscar', 'necesito',
    'quiero', 'me interesa', 'me gustaria', 'me gustaría', 'disponible', 'disponibilidad', 'stock',
    'precio', 'cuesta', 'cuestan', 'vale', 'valen', 'coste', 'cuanto', 'cuánto', 'informacion', 'información',
    'vende', 'vender', 'comprar', 'encontrar', 'localizar', 'existencia',
}

SEÑALES_CATEGORIA = {
    'productos', 'producto', 'cosas', 'articulos', 'artículos', 'items', 'catalogo', 'catálogo',
    'categoria', 'categoría', 'seccion', 'sección', 'linea', 'línea', 'hay en', 'tienen en', 'venden en',
    'disponible en', 'que hay', 'qué hay', 'mostrar', 'listar',
}

PATRONES_LISTADO = [
    r'(?:que|qué)\s+(.+?)\s+hay',
    r'(?:que|qué)\s+hay\s+(?:de\s+)?(.+)',
]

MODIFICADORES_PLURAL = {
    'tipos', 'tipo', 'clases', 'clase', 'variantes', 'variante',
    'modelos', 'modelo', 'marcas', 'marca', 'sorts',
}

ALIAS_CATEGORIAS = {
    'lacteo': 'Lacteos', 'lacteos': 'Lacteos', 'lacteos y derivados': 'Lacteos',
    'leche': 'Lacteos', 'derivados lacteos': 'Lacteos',
    'congelado': 'Congelados', 'congelados': 'Congelados', 'frozen': 'Congelados',
    'frescos': 'Frutas y Verduras', 'frutas y verduras': 'Frutas y Verduras',
    'carne': 'Carnes', 'carnes': 'Carnes', 'embutido': 'Carnes', 'embutidos': 'Carnes',
    'pan': 'Panaderia', 'panaderia': 'Panaderia', 'panadería': 'Panaderia', 'bolleria': 'Panaderia',
    'bebida': 'Bebidas', 'bebidas': 'Bebidas', 'refresco': 'Bebidas', 'refrescos': 'Bebidas',
    'limpieza': 'Limpieza y Hogar', 'hogar': 'Limpieza y Hogar', 'limpieza del hogar': 'Limpieza y Hogar',
    'despensa': 'Despensa', 'almacen': 'Despensa', 'almacén': 'Despensa', 'basicos': 'Despensa',
    'snack': 'Snacks', 'snacks': 'Snacks', 'aperitivo': 'Snacks', 'aperitivos': 'Snacks',
    'mascota': 'Mascotas', 'mascotas': 'Mascotas', 'perro': 'Mascotas', 'gato': 'Mascotas',
    'bebe': 'Infantil', 'bebé': 'Infantil', 'bebes': 'Infantil', 'bebés': 'Infantil', 'infantil': 'Infantil',
    'cuidado personal': 'Cuidado Personal', 'higiene': 'Cuidado Personal', 'cosmetica': 'Cuidado Personal',
}

# Consultas que deben ir al LLM aunque parezcan simples
PALABRAS_COMPLEJAS = {
    'devolver', 'devolucion', 'devolución', 'reembolso', 'reembolsar', 'cancelar', 'cancelacion', 'cancelación',
    'ticket', 'humano', 'agente', 'queja', 'quejar', 'reclamar', 'reclamacion', 'reclamación', 'factura',
    'facturas', 'cobro', 'cobros', 'duplicado', 'problema', 'incidencia', 'hablar con', 'derivar',
}

_ARTICULO = r'(?:de\s+(?:la|el)|del|de|el|la|los|las|un|una)\s+'

# Caché del catálogo (se invalida al recargar BD)
_catalogo_cache: tuple[list[str], list[str], dict[str, str]] | None = None

PATRONES_PRODUCTO = [
    rf'(?:precio|stock|cuesta|cuestan|vale|valen|coste)\s+(?:{_ARTICULO})?(.+)',
    rf'(?:tienen|teneis|tenéis|tienes|venden|vendeis|vendéis|hay|existe|existen)\s+(?:{_ARTICULO})?(.+)',
    rf'(?:busco|necesito|quiero|me interesa|me gustaria|me gustaría)\s+(?:comprar|ver|saber sobre\s+)?(?:{_ARTICULO})?(.+)',
    rf'(?:informacion|información|datos|detalles)\s+(?:{_ARTICULO})?(.+)',
    rf'(?:disponibilidad|disponible)\s+(?:{_ARTICULO})?(.+)',
    rf'(?:cuanto|cuánto)\s+(?:cuesta|cuestan|vale|valen|es|son)\s+(?:{_ARTICULO})?(.+)',
]

PATRONES_CATEGORIA = [
    r'(?:que|qué)\s+(?:productos|cosas|articulos|artículos)\s+(?:teneis|tenéis|tienen|hay|venden|ofreceis|ofrecéis)?\s*(?:en|de)\s+(?:la\s+(?:categoria|seccion|sección|parte)\s+(?:de\s+)?)?(.+)',
    r'(?:productos|cosas|articulos|artículos)\s+(?:en|de|del)\s+(?:la\s+(?:categoria|seccion|sección)\s+(?:de\s+)?)?(.+)',
    r'(?:mostrar|listar|ver|mostrarme)\s+(?:los\s+)?(?:productos|cosas)\s+(?:de|en|del)\s+(.+)',
    r'(?:categoria|categoría|seccion|sección)\s+(?:de\s+)?(.+)',
    r'(?:en|de)\s+(?:la\s+)?(?:seccion|sección|categoria|categoría)\s+(?:de\s+)?(.+)',
]

PATRONES_DISPONIBILIDAD = [
    rf'(?:tienen|teneis|tenéis|tienes|venden|vendeis|vendéis|hay|existe|existen)\s+(?:{_ARTICULO})?(.+)',
]

PATRONES_TIPOS = [
    rf'(?:que|qué)\s+(?:tipos?|clases?|variantes?|modelos?|marcas?)\s+(?:{_ARTICULO})?(.+?)(?:\s+(?:tienes|teneis|tenéis|tienen|hay|venden|vendeis|vendéis))?\s*$',
    rf'(?:tipos?|clases?|variantes?|modelos?)\s+(?:{_ARTICULO})?(.+?)(?:\s+(?:tienes|teneis|tenéis|tienen|hay|venden|vendeis|vendéis))?\s*$',
]

PATRONES_PEDIDOS = [
    r'(?:pedidos|compras|ordenes|órdenes|envios|envíos)\s+(?:de|para|del)\s+(' + EMAIL_RE.pattern + r')',
    r'(' + EMAIL_RE.pattern + r')\s+(?:pedidos|compras|ordenes|órdenes)',
    r'(?:estado|seguimiento)\s+(?:de\s+)?(?:mi\s+)?(?:pedido|compra|orden)\s*(?:de|para|del)?\s*(' + EMAIL_RE.pattern + r')?',
]

PATRONES_PROMOCIONES_FILTRO = [
    r'(?:promociones|promos|ofertas|descuentos|rebajas)\s+(?:de|en|del|para)\s+(?:la\s+(?:categoria|categoría|seccion|sección)\s+(?:de\s+)?)?(.+)',
    r'(?:que|qué)\s+(?:promociones|promos|ofertas|descuentos)\s+(?:hay|teneis|tenéis|tienen)\s+(?:de|en|del|para)\s+(?:la\s+(?:categoria|categoría)\s+(?:de\s+)?)?(.+)',
]


@dataclass
class Intencion:
    nombre: str
    confianza: float
    entidades: dict


def _similitud(a: str, b: str) -> float:
    return SequenceMatcher(None, normalizar_texto(a), normalizar_texto(b)).ratio()


def _tokens(texto: str) -> list[str]:
    norm = normalizar_texto(texto)
    return [t for t in re.split(r'[^\w]+', norm) if t and t not in STOPWORDS]


def _contiene_frase(norm: str, frases: set[str]) -> bool:
    if norm in frases:
        return True
    return any(norm.startswith(f + ' ') or f' {f} ' in f' {norm} ' for f in frases)


def _es_consultar_pedidos(norm: str) -> bool:
    if _contiene_frase(norm, CONSULTAR_PEDIDOS):
        return True
    if 'pedido' not in norm and 'pedidos' not in norm:
        return False
    return any(p in norm for p in ('estado', 'seguimiento', 'tracking', 'donde esta', 'dónde está'))


def _es_crear_pedido(norm: str, tokens: list[str]) -> bool:
    """Pedido nuevo / confirmación → LLM con crear_pedido."""
    if _es_consultar_pedidos(norm):
        return False
    if any(f in norm for f in (
        'hacer un pedido', 'hacer pedido', 'realizar pedido', 'nuevo pedido',
        'realizar compra', 'hacer compra', 'confirmo el pedido', 'confirmar pedido',
        'confirmo', 'confirmación', 'confirmacion',
    )):
        return True
    if 'pedido' in tokens or 'pedidos' in tokens:
        if any(v in tokens for v in ('hacer', 'realizar', 'nuevo', 'confirmar', 'confirmo')):
            return True
        if any(v in tokens for v in ('quiero', 'quisiera', 'necesito', 'gustaria', 'gustaría')):
            if 'mis' not in tokens:
                return True
    return any(v in tokens for v in VERBOS_CREAR_PEDIDO)


_DIAS_SEMANA = (
    'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo',
)


def _extraer_filtro_promociones(
    texto: str, tokens: list[str], categorias: list[str]
) -> dict:
    """Filtros opcionales: categoría, producto, día o solo aplicables hoy."""
    ent: dict = {}
    norm = normalizar_texto(texto)

    if any(t in tokens for t in ('todas', 'todos', 'completas', 'restantes', 'mas')) and any(
        t in tokens for t in ('promociones', 'promo', 'promos', 'ofertas', 'descuentos')
    ):
        ent['todas'] = True
        return ent

    for dia_nombre in _DIAS_SEMANA:
        if re.search(
            rf'(?:promociones|promos|ofertas|descuentos).*\b{dia_nombre}\b|\b{dia_nombre}\b.*(?:promociones|promos|ofertas)',
            norm,
        ):
            ent['dia'] = dia_nombre
            return ent

    if 'hoy' in tokens and any(
        t in tokens for t in ('promociones', 'promo', 'promos', 'ofertas', 'descuentos')
    ):
        ent['solo_hoy'] = True
        return ent

    termino = _extraer_por_patrones(texto, PATRONES_PROMOCIONES_FILTRO)
    if termino:
        termino_limpio = _limpiar_termino(termino)
        for dia_nombre in _DIAS_SEMANA:
            if termino_limpio == dia_nombre or termino_limpio.startswith(dia_nombre + ' '):
                ent['dia'] = dia_nombre
                return ent
        categoria, score_cat = _es_termino_categoria(termino_limpio, categorias)
        if categoria and score_cat >= 0.72:
            ent['categoria'] = categoria
        elif len(termino_limpio) >= 3:
            ent['producto'] = termino_limpio
    return ent


def _subtipo_frutas_verduras(texto: str, tokens: list[str]) -> str | None:
    """'frutas' o 'verduras' por separado; None si pide ambos o categoría completa."""
    norm = normalizar_texto(texto)
    if 'frutas' in norm and 'verduras' in norm:
        return None
    if any(t in tokens for t in ('frutas', 'fruta')) or re.search(r'\bfrutas?\b', norm):
        return 'frutas'
    if any(t in tokens for t in ('verduras', 'verdura', 'hortalizas', 'hortaliza')):
        return 'verduras'
    return None


def _intentar_frescos_subcategoria(texto: str, tokens: list[str]) -> Intencion | None:
    subtipo = _subtipo_frutas_verduras(texto, tokens)
    if subtipo:
        return Intencion('buscar_categoria', 0.96, {
            'categoria': 'Frutas y Verduras',
            'subtipo': subtipo,
        })
    return None


def _es_mensaje_cantidades_pedido(texto: str, tokens: list[str]) -> bool:
    """'20 yogures y 2 aceites' → continuar pedido en LLM, no búsqueda local."""
    if any(t in MODIFICADORES_PLURAL for t in tokens):
        return False
    if any(t in tokens for t in ('precio', 'cuesta', 'cuestan', 'cuanto', 'stock', 'tienen', 'teneis', 'tenéis', 'hay')):
        return False
    norm = normalizar_texto(texto)
    if _PATRON_CANTIDAD_PEDIDO.search(norm):
        return True
    if ' y ' in norm and any(re.fullmatch(_NUMEROS_CANTIDAD_RE, t, re.I) for t in tokens):
        return True
    return False


def _limpiar_termino(texto: str) -> str:
    texto = texto.strip(' ?!.,"\';:')
    texto = re.sub(
        rf'^(?:{_ARTICULO})',
        '', texto, flags=re.I,
    )
    texto = re.sub(
        r'\s+(?:por favor|gracias|hoy|ahora|disponible|disponibles)$',
        '', texto, flags=re.I,
    )
    texto = re.sub(
        r'\s+(?:hay|tienes|teneis|tenéis|tienen|venden|vendeis|vendéis)\w*$',
        '', texto, flags=re.I,
    )
    return texto.strip()


def _cache_catalogo() -> tuple[list[str], list[str], dict[str, str]]:
    global _catalogo_cache
    if _catalogo_cache is not None:
        return _catalogo_cache
    conn = get_connection()
    filas = conn.execute('SELECT nombre, categoria FROM productos ORDER BY LENGTH(nombre) DESC').fetchall()
    conn.close()
    productos = [row[0] for row in filas]
    categorias = obtener_categorias()
    categorias_por_producto = {row[0]: row[1] for row in filas}
    _catalogo_cache = (productos, categorias, categorias_por_producto)
    return _catalogo_cache


def invalidar_cache_catalogo() -> None:
    global _catalogo_cache
    _catalogo_cache = None


def _palabras_de_texto(norm_texto: str) -> set[str]:
    return {p for p in re.split(r'[^\w]+', norm_texto) if len(p) >= 2}


def _es_termino_categoria(termino: str, categorias: list[str]) -> tuple[str | None, float]:
    termino = _limpiar_termino(termino)
    if not termino:
        return None, 0.0
    norm = normalizar_texto(termino)
    for alias, categoria in ALIAS_CATEGORIAS.items():
        if norm == alias and categoria in categorias:
            return categoria, 0.94
    for categoria in categorias:
        if norm == normalizar_texto(categoria):
            return categoria, 0.95
    return _resolver_categoria(termino, categorias)


def _extraer_por_patrones(texto: str, patrones: list[str]) -> str | None:
    for patron in patrones:
        match = re.search(patron, texto, flags=re.I)
        if match:
            termino = _limpiar_termino(match.group(1))
            if len(termino) >= 2:
                return termino
    return None


def _resolver_categoria(texto: str, categorias: list[str]) -> tuple[str | None, float]:
    norm_texto = normalizar_texto(texto)
    candidatos: list[tuple[str, float]] = []

    for categoria in categorias:
        norm_cat = normalizar_texto(categoria)
        if norm_cat in norm_texto:
            candidatos.append((categoria, 0.95))

    for alias, categoria in ALIAS_CATEGORIAS.items():
        if alias in norm_texto and categoria in categorias:
            candidatos.append((categoria, 0.88))

    for categoria in categorias:
        ratio = _similitud(texto, categoria)
        if ratio >= 0.72:
            candidatos.append((categoria, ratio))

    for token in _tokens(texto):
        if len(token) < 4:
            continue
        for categoria in categorias:
            if token in normalizar_texto(categoria):
                candidatos.append((categoria, 0.8))

    if not candidatos:
        return None, 0.0
    candidatos.sort(key=lambda x: x[1], reverse=True)
    return candidatos[0]


def _resolver_producto(texto: str, productos: list[str]) -> tuple[str | None, float]:
    norm_texto = normalizar_texto(texto)
    palabras_texto = _palabras_de_texto(norm_texto)
    candidatos: list[tuple[str, float]] = []

    for producto in productos:
        norm_prod = normalizar_texto(producto)
        if norm_prod in norm_texto:
            candidatos.append((producto, 0.96 + len(norm_prod) * 0.001))

    for producto in productos:
        norm_prod = normalizar_texto(producto)
        palabras = [p for p in norm_prod.split() if len(p) >= 3]
        coincidencias = sum(1 for p in palabras if p in palabras_texto)
        if coincidencias and palabras:
            score = coincidencias / len(palabras)
            if score >= 0.5:
                candidatos.append((producto, 0.75 + score * 0.2))

    termino_patron = _extraer_por_patrones(texto, PATRONES_PRODUCTO)
    if termino_patron:
        for producto in productos:
            ratio = _similitud(termino_patron, producto)
            if ratio >= 0.55:
                candidatos.append((producto, ratio))
        if len(_tokens(termino_patron)) >= 1:
            candidatos.append((_limpiar_termino(termino_patron), 0.72))

    if not candidatos:
        return None, 0.0
    candidatos.sort(key=lambda x: x[1], reverse=True)
    return candidatos[0]


def _priorizar_categoria_sobre_producto(
    termino: str,
    productos: list[str],
    categorias_por_producto: dict[str, str],
) -> bool:
    """True si el término es claramente una categoría (p. ej. snacks, bebidas)."""
    norm = normalizar_texto(_limpiar_termino(termino))
    if norm not in ALIAS_CATEGORIAS:
        return False
    categoria_esperada = ALIAS_CATEGORIAS[norm]
    coincidencias = _contar_coincidencias(norm, productos)
    if not coincidencias:
        return True
    en_categoria = [
        p for p in coincidencias
        if categorias_por_producto.get(p) == categoria_esperada
    ]
    if not en_categoria:
        return True
    if len(en_categoria) >= 2:
        return False
    return normalizar_texto(en_categoria[0]) != norm


def _contar_coincidencias(termino: str, productos: list[str]) -> list[str]:
    """Productos cuyo nombre contiene el término de búsqueda."""
    norm_t = normalizar_texto(termino)
    return [p for p in productos if norm_t in normalizar_texto(p)]


def _termino_generico_desde_tokens(
    tokens: list[str], productos: list[str]
) -> tuple[str, float] | tuple[None, float]:
    """Si un token del mensaje coincide con varios productos, devuelve el término genérico."""
    for token in reversed(tokens):
        if token in MODIFICADORES_PLURAL or len(token) < 3:
            continue
        coincidencias = _contar_coincidencias(token, productos)
        if len(coincidencias) > 1:
            return token, 0.91
    return None, 0.0


def _intentar_buscar_tipos_producto(
    texto: str, tokens: list[str], productos: list[str]
) -> Intencion | None:
    """'qué tipos de leche hay' → productos de leche, no categoría Lácteos."""
    tiene_modificador = any(t in MODIFICADORES_PLURAL for t in tokens)
    termino = _extraer_por_patrones(texto, PATRONES_TIPOS)
    if not termino and not tiene_modificador:
        return None
    if not termino:
        sub = [t for t in tokens if t not in MODIFICADORES_PLURAL]
        termino = sub[-1] if sub else None
    if not termino:
        return None

    termino = _limpiar_termino(termino)
    if len(termino) < 2:
        return None

    sub_tokens = _tokens(termino)
    generico, score = _termino_generico_desde_tokens(sub_tokens or tokens, productos)
    if generico:
        return Intencion('buscar_producto', score, {'nombre': generico})

    coincidencias = _contar_coincidencias(termino, productos)
    if len(coincidencias) > 1:
        return Intencion('buscar_producto', 0.9, {'nombre': termino})
    if len(coincidencias) == 1:
        return Intencion('buscar_producto', 0.93, {'nombre': coincidencias[0]})

    for token in reversed(sub_tokens or tokens):
        if token in MODIFICADORES_PLURAL or len(token) < 3:
            continue
        c = _contar_coincidencias(token, productos)
        if len(c) > 1:
            return Intencion('buscar_producto', 0.91, {'nombre': token})
    return None


def _termino_busqueda_producto(
    texto: str,
    tokens: list[str],
    productos: list[str],
    categorias_por_producto: dict[str, str] | None = None,
) -> tuple[str, float] | tuple[None, float]:
    """Extrae el término a buscar; si hay varios productos posibles, no elige uno solo."""
    termino = _extraer_por_patrones(texto, PATRONES_TIPOS)
    if not termino:
        termino = _extraer_por_patrones(texto, PATRONES_PRODUCTO)
    if not termino and tokens:
        termino = ' '.join(tokens[-3:])
    if not termino:
        termino = _limpiar_termino(texto)
    termino = _limpiar_termino(termino)
    if len(termino) < 2:
        return None, 0.0

    if any(t in MODIFICADORES_PLURAL for t in tokens):
        generico, score_g = _termino_generico_desde_tokens(tokens, productos)
        if generico:
            return generico, score_g

    coincidencias = _contar_coincidencias(termino, productos)
    if len(coincidencias) > 1:
        return termino, 0.9
    if len(coincidencias) == 1:
        unico = coincidencias[0]
        if categorias_por_producto and _coincidencia_espuria_categoria(
            termino, unico, categorias_por_producto
        ):
            return termino, 0.88
        return unico, 0.93

    producto, score = _resolver_producto(texto, productos)
    if producto and score >= 0.85:
        generico, score_g = _termino_generico_desde_tokens(tokens, productos)
        if generico:
            return generico, score_g
        return producto, score
    return termino, 0.78


def _tiene_verbo_producto(norm: str, tokens: list[str]) -> bool:
    return any(v in norm for v in VERBOS_PRODUCTO) or any(t in VERBOS_PRODUCTO for t in tokens)


def _tiene_señal_categoria(norm: str) -> bool:
    padded = f' {norm} '
    for s in SEÑALES_CATEGORIA:
        if len(s) <= 4:
            if f' {s} ' in padded:
                return True
        elif s in norm:
            return True
    return False


def _coincidencia_espuria_categoria(
    termino: str,
    producto: str,
    categorias_por_producto: dict[str, str],
) -> bool:
    """True si el producto no pertenece a la categoría del alias buscado."""
    norm_t = normalizar_texto(_limpiar_termino(termino))
    if norm_t not in ALIAS_CATEGORIAS:
        return False
    cat_esperada = ALIAS_CATEGORIAS[norm_t]
    return categorias_por_producto.get(producto) != cat_esperada


def clasificar_intencion(mensaje: str) -> Intencion | None:
    """Devuelve intención detectada o None si conviene usar el LLM."""
    texto = mensaje.strip()
    if not texto:
        return None

    norm = normalizar_texto(texto)
    tokens = _tokens(texto)
    productos, categorias, categorias_por_producto = _cache_catalogo()

    if any(p in norm for p in PALABRAS_COMPLEJAS):
        return None

    if _es_crear_pedido(norm, tokens):
        return None

    if _es_mensaje_cantidades_pedido(texto, tokens):
        return None

    if _contiene_frase(norm, SALUDOS) and len(tokens) <= 6:
        return Intencion('saludo', 0.95, {})

    if _contiene_frase(norm, DESPEDIDAS) and len(tokens) <= 8:
        return Intencion('despedida', 0.93, {})

    if _contiene_frase(norm, AYUDA):
        return Intencion('ayuda', 0.9, {})

    if _contiene_frase(norm, PROMOCIONES):
        ent = _extraer_filtro_promociones(texto, tokens, categorias)
        return Intencion('promociones', 0.92, ent)

    email = EMAIL_RE.search(texto)
    if email:
        if _es_crear_pedido(norm, tokens):
            return None
        if _es_consultar_pedidos(norm) or _extraer_por_patrones(texto, PATRONES_PEDIDOS):
            return Intencion('consultar_pedidos', 0.91, {'email': email.group(0)})
        return None

    if _contiene_frase(norm, PEDIDOS) and not email:
        if _es_consultar_pedidos(norm) or norm in ('pedidos', 'pedido'):
            return Intencion('pedir_email', 0.85, {'contexto': 'pedidos'})
        return None

    # --- "qué tipos de leche hay" → productos (antes que categoría Lácteos) ---
    intent_tipos = _intentar_buscar_tipos_producto(texto, tokens, productos)
    if intent_tipos:
        return intent_tipos

    # --- "qué frutas hay" / "qué verduras hay" → subcategoría ---
    termino_listado = _extraer_por_patrones(texto, PATRONES_LISTADO)
    if termino_listado:
        termino_limpio = _limpiar_termino(termino_listado)
        intent_frescos = _intentar_frescos_subcategoria(termino_limpio, _tokens(termino_limpio))
        if intent_frescos:
            return intent_frescos
        if any(t in MODIFICADORES_PLURAL for t in _tokens(termino_limpio)):
            intent_tipos = _intentar_buscar_tipos_producto(texto, tokens, productos)
            if intent_tipos:
                return intent_tipos
        categoria, score_cat = _es_termino_categoria(termino_limpio, categorias)
        if categoria and score_cat >= 0.72:
            return Intencion('buscar_categoria', min(0.97, score_cat + 0.05), {'categoria': categoria})

    # --- "tienes congelados" / "hay snacks" → categoría si aplica ---
    termino_disp = _extraer_por_patrones(texto, PATRONES_DISPONIBILIDAD)
    if termino_disp:
        termino_limpio = _limpiar_termino(termino_disp)
        intent_frescos = _intentar_frescos_subcategoria(termino_limpio, _tokens(termino_limpio))
        if intent_frescos:
            return intent_frescos
        if _priorizar_categoria_sobre_producto(termino_limpio, productos, categorias_por_producto):
            categoria, score_cat = _es_termino_categoria(termino_limpio, categorias)
            if categoria and score_cat >= 0.72:
                return Intencion('buscar_categoria', min(0.97, score_cat + 0.03), {'categoria': categoria})
        coincidencias_prod = _contar_coincidencias(termino_limpio, productos)
        if not coincidencias_prod:
            categoria, score_cat = _es_termino_categoria(termino_limpio, categorias)
            if categoria and score_cat >= 0.72:
                return Intencion('buscar_categoria', min(0.97, score_cat + 0.03), {'categoria': categoria})

    # --- Categoría (prioritaria si el mensaje lo indica claramente) ---
    if _tiene_señal_categoria(norm):
        termino_cat = _extraer_por_patrones(texto, PATRONES_CATEGORIA)
        categoria, score_cat = _resolver_categoria(termino_cat or texto, categorias)
        if categoria and score_cat >= 0.72:
            confianza = min(0.97, score_cat + (0.08 if termino_cat else 0.05))
            return Intencion('buscar_categoria', confianza, {'categoria': categoria})

    # --- Producto ---
    termino, score_prod = _termino_busqueda_producto(
        texto, tokens, productos, categorias_por_producto
    )
    if termino and _priorizar_categoria_sobre_producto(termino, productos, categorias_por_producto):
        categoria, score_cat = _es_termino_categoria(termino, categorias)
        if categoria and score_cat >= 0.72:
            return Intencion('buscar_categoria', min(0.97, score_cat + 0.05), {'categoria': categoria})
    if termino and score_prod >= 0.72:
        confianza = min(0.97, score_prod + (0.06 if _tiene_verbo_producto(norm, tokens) else 0))
        return Intencion('buscar_producto', confianza, {'nombre': termino})

    # --- Categoría (sin señal explícita) ---
    termino_cat = _extraer_por_patrones(texto, PATRONES_CATEGORIA)
    categoria, score_cat = _resolver_categoria(termino_cat or texto, categorias)
    if categoria and score_cat >= 0.72:
        confianza = score_cat
        if _tiene_señal_categoria(norm):
            confianza = min(0.97, confianza + 0.08)
        if termino_cat:
            confianza = min(0.97, confianza + 0.05)
        return Intencion('buscar_categoria', confianza, {'categoria': categoria})

    # Mensaje corto (p. ej. "bebidas", "pan")
    if len(tokens) <= 5 and not _contiene_frase(norm, PEDIDOS | PROMOCIONES):
        termino_corto = _limpiar_termino(texto)
        intent_frescos = _intentar_frescos_subcategoria(termino_corto, _tokens(termino_corto))
        if intent_frescos:
            return intent_frescos
        if _priorizar_categoria_sobre_producto(termino_corto, productos, categorias_por_producto):
            categoria, score_cat = _es_termino_categoria(termino_corto, categorias)
            if categoria and score_cat >= 0.72:
                return Intencion('buscar_categoria', min(0.97, score_cat + 0.05), {'categoria': categoria})
        termino_final, score_corto = _termino_busqueda_producto(
            termino_corto, _tokens(termino_corto), productos, categorias_por_producto
        )
        if termino_final and score_corto >= 0.65:
            return Intencion('buscar_producto', score_corto, {'nombre': termino_final})
        if len(termino_corto) >= 3:
            return Intencion('buscar_producto', 0.7, {'nombre': termino_corto})

    return None
