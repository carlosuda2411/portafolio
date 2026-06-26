"""
Respuestas locales sin LLM para consultas sencillas.
Usa la BD directamente y ahorra tokens de OpenAI.
"""
import os

from .intent_router import clasificar_intencion
from .queries import (
    buscar_producto,
    buscar_por_categoria,
    consultar_pedidos,
    obtener_promociones,
)


def _formato_euro(cantidad: float) -> str:
    return f"{cantidad:.2f} €"


def _formato_producto(prod: dict) -> str:
    precio = prod.get('precio_efectivo', prod['precio'])
    linea = (
        f"- **{prod['nombre']}** ({prod['categoria']}): "
        f"{_formato_euro(precio)} — stock: {prod['stock']} {prod.get('unidad', 'u.')}"
    )
    promo = prod.get('promocion')
    if promo and prod.get('promocion_aplicable_hoy') is False:
        linea += f" 🏷️ {promo['descripcion']} (no aplicable hoy)"
    elif promo and precio != prod['precio']:
        linea += f" (antes {_formato_euro(prod['precio'])})"
        linea += f" 🏷️ {promo['descripcion']} (-{promo['descuento_porcentaje']}%)"
    elif promo:
        linea += f" 🏷️ {promo['descripcion']} (-{promo['descuento_porcentaje']}%)"
    return linea


def _responder_producto(nombre: str) -> str | None:
    resultados = buscar_producto(nombre)
    if not resultados:
        return None
    lineas = [_formato_producto(p) for p in resultados[:8]]
    extra = f"\n\n_(Mostrando {len(lineas)} de {len(resultados)} resultados)_" if len(resultados) > 8 else ''
    return "🔍 Esto es lo que encontré:\n\n" + "\n".join(lineas) + extra


def _responder_categoria(categoria: str, subtipo: str | None = None) -> str | None:
    resultados = buscar_por_categoria(categoria, subtipo=subtipo)
    if not resultados:
        return None
    if subtipo == 'frutas':
        titulo = 'Frutas'
    elif subtipo == 'verduras':
        titulo = 'Verduras'
    else:
        titulo = resultados[0]['categoria']
    lineas = [
        f"- **{p['nombre']}**: {_formato_euro(p['precio'])} (stock: {p['stock']})"
        for p in resultados[:10]
    ]
    extra = f"\n\n_(Mostrando {len(lineas)} de {len(resultados)} productos)_" if len(resultados) > 10 else ''
    return f"📂 Productos en **{titulo}**:\n\n" + "\n".join(lineas) + extra


def _formato_linea_promo(promo: dict) -> str:
    linea = (
        f"- **{promo['producto']}**: {promo['descripcion']} — "
        f"{_formato_euro(promo['precio_hoy'])}"
    )
    if not promo.get('aplicable_hoy'):
        return linea + f" (promo en días indicados: {_formato_euro(promo['precio_con_descuento'])})"
    return linea + f" (antes {_formato_euro(promo['precio_original'])})"


def _responder_promociones(filtros: dict | None = None) -> str:
    filtros = filtros or {}
    datos = obtener_promociones(
        categoria=filtros.get('categoria'),
        producto=filtros.get('producto'),
        dia=filtros.get('dia'),
        solo_aplicables_hoy=filtros.get('solo_hoy'),
        todas=filtros.get('todas', False),
    )
    promos = datos.get('promociones', datos) if isinstance(datos, dict) else datos
    dia_filtro = filtros.get('dia')
    habituales = datos.get('promos_habituales_vigentes', 0)

    if not promos:
        if dia_filtro:
            if habituales:
                return (
                    f"🏷️ No hay promociones **exclusivas del {dia_filtro}** en este momento.\n\n"
                    f"_ℹ️ Sí hay **{habituales}** promociones habituales (válidas todos los días) "
                    f"vigentes. Pregunta *¿Qué promociones hay?* para ver las principales._"
                )
            return f"🏷️ No hay promociones exclusivas del {dia_filtro} ni otras vigentes."
        if datos.get('filtrado'):
            return "🏷️ No hay promociones vigentes con ese filtro."
        return "🏷️ No hay promociones vigentes en este momento."

    if filtros.get('todas'):
        titulo = "🏷️ **Todas las promociones vigentes:**"
    elif filtros.get('categoria'):
        titulo = f"🏷️ **Promociones vigentes en {filtros['categoria']}:**"
    elif filtros.get('producto'):
        titulo = f"🏷️ **Promociones vigentes de {filtros['producto']}:**"
    elif dia_filtro:
        titulo = f"🏷️ **Promociones exclusivas del {dia_filtro}:**"
    elif filtros.get('solo_hoy'):
        titulo = "🏷️ **Promociones aplicables hoy:**"
    else:
        titulo = "🏷️ **Principales promociones vigentes:**"

    lineas = [_formato_linea_promo(p) for p in promos]
    extra = ''
    if dia_filtro and habituales:
        extra = (
            f"\n\n_ℹ️ Además, hay **{habituales}** promociones habituales (válidas todos los días) "
            f"también vigentes. Pregunta *¿Qué promociones hay?* para ver las principales._"
        )
    elif datos.get('hay_mas'):
        total = datos['total_disponibles']
        extra = (
            f"\n\n_(Hay **{total}** promociones activas. ¿Quieres ver más? Pregunta por:_\n"
            "- *Todas las promociones*\n"
            "- *Promociones de [categoría]* (ej. lácteos, panadería)\n"
            "- *Promociones aplicables hoy*\n"
            "- *Promociones del martes* (u otro día)_"
        )
    elif datos.get('filtrado') and datos['mostrando'] < datos['total_disponibles']:
        extra = (
            f"\n\n_(Mostrando {datos['mostrando']} de {datos['total_disponibles']} "
            f"promociones vigentes)_"
        )
    return titulo + "\n\n" + "\n".join(lineas) + extra


def _responder_pedidos(email: str) -> str:
    pedidos = consultar_pedidos(email)
    if not pedidos:
        return f"📦 No encontré pedidos para **{email}**."
    lineas = [
        f"- Pedido #{p['id']}: {p['estado']} — {_formato_euro(p['total'])} ({p['fecha_pedido']})"
        for p in pedidos[:8]
    ]
    extra = f"\n\n_(Mostrando {len(lineas)} de {len(pedidos)} pedidos)_" if len(pedidos) > 8 else ''
    return f"📦 **Pedidos de {email}:**\n\n" + "\n".join(lineas) + extra


def _plantillas_fijas(intencion: str) -> str:
    if intencion == 'saludo':
        return (
            "¡Hola! 👋 Soy **EcoBot**. Puedo buscar productos, promociones y pedidos.\n\n"
            "Prueba: *¿Tienen leche?*, *¿Qué promociones hay?* o *Mis pedidos: tu@email.com*"
        )
    if intencion == 'despedida':
        return "¡Hasta pronto! 👋 Si necesitas algo más de EcoMarket, aquí estaré."
    if intencion == 'ayuda':
        return (
            "Puedo ayudarte con:\n"
            "- 🔍 Productos: *¿Tienen lasaña?*, *precio de leche entera*\n"
            "- 📂 Categorías: *¿Qué hay en congelados?*, *¿Qué frutas hay?*\n"
            "- 🏷️ *¿Qué promociones hay?*\n"
            "- 📦 Pedidos: *pedidos de maria.garcia@email.com*\n"
            "- 🛒 Pedidos nuevos, devoluciones y listas de compra → asistente avanzado"
        )
    return ""


def responder_local(mensaje: str) -> str | None:
    """Intenta responder sin OpenAI. Devuelve None si debe usarse el LLM."""
    if os.getenv('LOCAL_NLP_ENABLED', 'true').lower() not in ('1', 'true', 'yes', 'si', 'sí'):
        return None

    intencion = clasificar_intencion(mensaje)
    if not intencion or intencion.confianza < 0.68:
        return None

    nombre = intencion.nombre
    ent = intencion.entidades

    if nombre in ('saludo', 'despedida', 'ayuda'):
        return _plantillas_fijas(nombre)

    if nombre == 'promociones':
        return _responder_promociones(ent)

    if nombre == 'consultar_pedidos':
        return _responder_pedidos(ent['email'])

    if nombre == 'pedir_email':
        ctx = ent.get('contexto', 'consulta')
        if ctx == 'pedidos':
            return (
                "📦 Para consultar tus pedidos necesito tu **email**.\n\n"
                "Ejemplo: *pedidos de maria.garcia@email.com*"
            )
        return "Necesito tu **email** para continuar. ¿Cuál es?"

    if nombre == 'buscar_categoria':
        return _responder_categoria(ent['categoria'], ent.get('subtipo'))

    if nombre == 'buscar_producto':
        return _responder_producto(ent['nombre'])

    return None
