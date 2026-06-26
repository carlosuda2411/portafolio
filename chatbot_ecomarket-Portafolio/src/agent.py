"""
Agente LLM para EcoMarket.
Conecta OpenAI con las funciones de consulta.
Todas las tools están disponibles en cada turno; el modelo decide cuál usar.
"""
import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from .database import obtener_categorias
from .queries import (
    buscar_producto,
    buscar_por_categoria,
    consultar_pedidos,
    obtener_detalle_pedido,
    obtener_promociones,
    registrar_devolucion,
    consultar_devoluciones,
    crear_ticket_soporte,
    crear_pedido,
    calcular_total_pedido,
    generar_lista_compra,
)

load_dotenv()

# Días de la semana y meses en español para la fecha dinámica
_DIAS_SEMANA = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
_MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
           'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def _obtener_fecha_actual() -> str:
    """Retorna la fecha actual formateada en español."""
    ahora = datetime.now()
    dia_semana = _DIAS_SEMANA[ahora.weekday()]
    mes = _MESES[ahora.month - 1]
    return f"{dia_semana} {ahora.day} de {mes} de {ahora.year}"


# ══════════════════════════════════════════════
# SYSTEM PROMPT
# ══════════════════════════════════════════════

SYSTEM_PROMPT_TEMPLATE = """Eres EcoBot, asistente virtual de EcoMarket. Amable, conciso y servicial.
FECHA: {fecha_actual}

REGLAS GENERALES:
- Responde en español, sé conciso
- Precios en EUROS: número seguido del símbolo (ej. 112.28 €, nunca €112.28 ni $)
- Si un producto tiene promoción, menciónala. Algunas solo aplican ciertos días (ej. martes); precio_efectivo y calcular_total_pedido ya respetan el día actual.
- No inventes información, solo usa datos reales de las tools
- Usa emojis moderadamente

UNIDADES Y CANTIDADES:
- Los productos tienen una unidad definida (kg, unidad, litro, paquete, docena, etc.)
- Cada producto se vende en la unidad indicada en su descripción. Ejemplo: "Manzana Roja, 1kg" significa que 1 unidad = 1kg.
- NUNCA preguntes al cliente por peso o medida. Pregunta solo CUÁNTAS UNIDADES quiere (ej: "¿Cuántas quieres?" no "¿cuántos kg?").
- Si el cliente dice "quiero manzanas", asume 1 unidad salvo que indique otra cantidad.

STOCK Y ALTERNATIVAS:
- Si un producto tiene stock = 0 o stock insuficiente, usa buscar_por_categoria con la categoría EXACTA del producto sin stock para ofrecer alternativas disponibles.
- Categorías en la BD: {categorias}
- Para frutas o verduras usa buscar_por_categoria con subtipo "frutas" o "verduras". Para ambos juntos usa categoría "Frutas y Verduras" sin subtipo.
- Muestra las alternativas con precio para que el cliente elija.

PAGOS: Solo contra entrega. Domicilio: 2€ extra. No se aceptan pagos online.

CÁLCULO DE TOTALES (OBLIGATORIO):
- NUNCA calcules sumas manualmente. USA calcular_total_pedido para el resumen antes de confirmar.
- El precio real es precio_efectivo de buscar_producto (incluye promos activas), NO el precio de catálogo si hay descuento.
- calcular_total_pedido ya incluye los 2€ de domicilio por defecto.
- Tras crear_pedido, muestra al cliente los importes EXACTOS del JSON devuelto por la tool (subtotal_productos, costo_domicilio, total).

═══════════════════════════════════════
TOOLS DISPONIBLES Y CUÁNDO USARLAS:
═══════════════════════════════════════

1. buscar_producto(nombre) → Busca productos en la base de datos por nombre.
   ÚSALA SIEMPRE que el usuario mencione un producto, ya sea para consultar precio, disponibilidad, o para hacer un pedido.

2. buscar_por_categoria(categoria) → Lista productos de una categoría.
   Úsala cuando pregunten por una categoría o cuando necesites ofrecer alternativas a un producto sin stock.

3. consultar_pedidos(email) → Consulta pedidos existentes de un cliente.
   Úsala cuando pregunten por el estado de un pedido.

4. obtener_detalle_pedido(pedido_id) → Detalle completo de un pedido específico.
   Úsala después de consultar_pedidos si quieren más detalle.

5. calcular_total_pedido(productos_cantidades) → Calcula subtotales y total con promos y domicilio.
   OBLIGATORIO usarla en el Paso 6 del flujo de pedidos. NO sumes precios tú mismo.

6. crear_pedido(email, productos_cantidades, direccion) → Crea un nuevo pedido.
   SOLO úsala DESPUÉS de haber buscado los productos con buscar_producto y tener confirmación del cliente.

7. obtener_promociones(categoria, producto, dia, solo_aplicables_hoy, todas) → Promociones vigentes.
   Sin filtros: muestra las 5 principales (mayor descuento) e invita a ver más.
   Usa todas=true si piden el listado completo. Filtra por categoría, producto o solo_aplicables_hoy cuando lo indiquen.
   Si piden promociones de un día (ej. martes): muestra SOLO las exclusivas de ese día e indica que las promociones habituales también siguen vigentes.

8. registrar_devolucion(pedido_id, email, motivo) → Registra una devolución.
   Úsala cuando quieran devolver un producto.

9. consultar_devoluciones(email) → Estado de devoluciones del cliente.

10. crear_ticket_soporte(email, asunto, descripcion) → Escala a agente humano.
    Úsala cuando no puedas resolver algo o el cliente lo pida.

11. generar_lista_compra(condicion, presupuesto_max) → Genera lista de compra temática.
    Si el cliente indica presupuesto (ej. 30€), pásalo como presupuesto_max. Muestra total_estimado y dentro_presupuesto de la tool; no recalcules el total manualmente.

═══════════════════════════════════════
FLUJO OBLIGATORIO PARA PEDIDOS:
═══════════════════════════════════════
Paso 1: El cliente menciona que quiere pedir/comprar algo → USA buscar_producto para verificar que existe en la BD y mostrarle opciones con precios reales.
Paso 2: Si hay varias coincidencias, pregunta cuál quiere exactamente.
Paso 3: Si el cliente YA indicó cantidades (ej. "30 yogures y 2 aceites", o "20 yogures y dos de aceite"), NO vuelvas a preguntar cuántas quiere. Usa esas cantidades y continúa el pedido.
Paso 4: Pide email + dirección completa CON CIUDAD.
Paso 5: COBERTURA: Solo Madrid, Málaga y Valencia. Otra ciudad → informa que está fuera de cobertura.
Paso 6: USA calcular_total_pedido y muestra su resultado (líneas, subtotal, domicilio, total). Pide confirmación.
Paso 7: Solo con confirmación explícita, llama crear_pedido con el nombre EXACTO que devolvió buscar_producto.

NUNCA llames crear_pedido sin haber usado buscar_producto antes. El nombre del producto en crear_pedido DEBE coincidir con lo que existe en la base de datos."""

# ══════════════════════════════════════════════
# TOOLS (todas disponibles siempre)
# ══════════════════════════════════════════════

ALL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_producto",
            "description": "Busca productos por nombre en la base de datos. OBLIGATORIO usarla ANTES de crear_pedido para verificar disponibilidad y obtener el nombre exacto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre o parte del nombre del producto a buscar"}
                },
                "required": ["nombre"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_por_categoria",
            "description": "Lista productos de una categoría. Categorías en BD: {categorias}. Para solo frutas o solo verduras usa subtipo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {"type": "string", "description": "Nombre de la categoría"},
                    "subtipo": {
                        "type": "string",
                        "enum": ["frutas", "verduras"],
                        "description": "Dentro de Frutas y Verduras: filtrar solo frutas o solo verduras"
                    }
                },
                "required": ["categoria"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_pedidos",
            "description": "Consulta los pedidos de un cliente por su email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email del cliente"}
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_detalle_pedido",
            "description": "Obtiene el detalle completo de un pedido específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pedido_id": {"type": "integer", "description": "ID del pedido"}
                },
                "required": ["pedido_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_total_pedido",
            "description": "Calcula el total de un pedido SIN crearlo. Aplica promociones vigentes y 2€ de domicilio. OBLIGATORIO para mostrar resúmenes; no calcules totales manualmente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "productos_cantidades": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "nombre": {"type": "string", "description": "Nombre EXACTO del producto"},
                                "cantidad": {"type": "integer", "description": "Cantidad a pedir"}
                            },
                            "required": ["nombre", "cantidad"]
                        },
                        "description": "Lista de productos con cantidades"
                    },
                    "incluir_domicilio": {
                        "type": "boolean",
                        "description": "Si incluir 2€ de domicilio (por defecto true)"
                    }
                },
                "required": ["productos_cantidades"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_pedido",
            "description": "Crea un nuevo pedido. REQUISITOS PREVIOS: 1) Haber usado buscar_producto para verificar existencia. 2) Tener email del cliente. 3) Tener dirección CON ciudad (solo Madrid, Málaga, Valencia). 4) Confirmación explícita del cliente. El campo 'nombre' DEBE ser el nombre exacto devuelto por buscar_producto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email del cliente"},
                    "productos_cantidades": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "nombre": {"type": "string", "description": "Nombre EXACTO del producto como aparece en buscar_producto"},
                                "cantidad": {"type": "integer", "description": "Cantidad a pedir"}
                            },
                            "required": ["nombre", "cantidad"]
                        },
                        "description": "Lista de productos con cantidades"
                    },
                    "direccion": {"type": "string", "description": "Dirección completa incluyendo ciudad (solo Madrid, Málaga o Valencia)"}
                },
                "required": ["email", "productos_cantidades", "direccion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_promociones",
            "description": "Lista promociones vigentes. Por defecto devuelve las 5 principales. Usa todas=true para el listado completo, o filtra por categoría, producto, día o solo_aplicables_hoy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {
                        "type": "string",
                        "description": "Filtrar por categoría (ej. Lacteos, Panaderia)"
                    },
                    "producto": {
                        "type": "string",
                        "description": "Filtrar por nombre de producto"
                    },
                    "dia": {
                        "type": "string",
                        "description": "Filtrar promos exclusivas de ese día (lunes, martes, ...). No incluye promos habituales."
                    },
                    "solo_aplicables_hoy": {
                        "type": "boolean",
                        "description": "Si true, solo promos aplicables hoy"
                    },
                    "todas": {
                        "type": "boolean",
                        "description": "Si true, devuelve todas las promociones vigentes"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_devolucion",
            "description": "Registra una solicitud de devolución de un pedido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pedido_id": {"type": "integer", "description": "ID del pedido a devolver"},
                    "email": {"type": "string", "description": "Email del cliente"},
                    "motivo": {"type": "string", "description": "Motivo de la devolución"}
                },
                "required": ["pedido_id", "email", "motivo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_devoluciones",
            "description": "Consulta el estado de devoluciones de un cliente por email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email del cliente"}
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_ticket_soporte",
            "description": "Crea un ticket de soporte para escalar a un agente humano.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email del cliente"},
                    "asunto": {"type": "string", "description": "Asunto del ticket"},
                    "descripcion": {"type": "string", "description": "Descripción del problema"},
                    "pedido_id": {"type": "integer", "description": "ID del pedido relacionado (opcional)"}
                },
                "required": ["email", "asunto", "descripcion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_lista_compra",
            "description": "Genera una lista de compra personalizada respetando presupuesto si se indica. Opciones: saludable, vegano, proteico, economico, sin_gluten, desayuno, desayuno_saludable. Aplica promociones al total_estimado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "condicion": {
                        "type": "string",
                        "enum": ["saludable", "vegano", "proteico", "economico", "sin_gluten", "desayuno", "desayuno_saludable"],
                        "description": "Tipo de lista de compra"
                    },
                    "presupuesto_max": {
                        "type": "number",
                        "description": "Presupuesto máximo en euros. La lista no superará este importe (promos incluidas)."
                    }
                },
                "required": ["condicion"]
            }
        }
    },
]

# ══════════════════════════════════════════════
# FUNCIONES DISPONIBLES PARA EJECUCIÓN
# ══════════════════════════════════════════════

FUNCIONES_DISPONIBLES = {
    'buscar_producto': buscar_producto,
    'buscar_por_categoria': buscar_por_categoria,
    'consultar_pedidos': consultar_pedidos,
    'obtener_detalle_pedido': obtener_detalle_pedido,
    'obtener_promociones': obtener_promociones,
    'registrar_devolucion': registrar_devolucion,
    'consultar_devoluciones': consultar_devoluciones,
    'crear_ticket_soporte': crear_ticket_soporte,
    'crear_pedido': crear_pedido,
    'calcular_total_pedido': calcular_total_pedido,
    'generar_lista_compra': generar_lista_compra,
}


# ══════════════════════════════════════════════
# CLASE PRINCIPAL DEL BOT
# ══════════════════════════════════════════════

class EcoMarketBot:
    """Chatbot EcoMarket con function calling (OpenAI) + historial compacto."""

    MODEL = 'gpt-4o-mini'
    MAX_HISTORIAL_TURNOS = 6
    MAX_TOOL_ITERATIONS = 5

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.historial = []
        self.actualizar_catalogo()

    def actualizar_catalogo(self):
        """Actualiza categorías dinámicas en prompt y tools."""
        self.categorias = obtener_categorias()
        cats = ', '.join(self.categorias)
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            fecha_actual=_obtener_fecha_actual(),
            categorias=cats,
        )
        self.tools = json.loads(json.dumps(ALL_TOOLS))
        for tool in self.tools:
            if tool['function']['name'] == 'buscar_por_categoria':
                tool['function']['description'] = tool['function']['description'].format(categorias=cats)

    def resetear_conversacion(self):
        self.historial = []
        self.actualizar_catalogo()

    def registrar_turno(self, mensaje: str, respuesta: str) -> None:
        """Registra turno del NLP local para mantener contexto en el LLM."""
        self.historial.append({'role': 'user', 'content': mensaje})
        self.historial.append({'role': 'assistant', 'content': respuesta})
        self._recortar_historial()

    def _recortar_historial(self):
        """Mantiene solo los últimos MAX_HISTORIAL_TURNOS turnos.
        Se asegura de no cortar entre un assistant con tool_calls y sus respuestas tool."""
        if len(self.historial) <= self.MAX_HISTORIAL_TURNOS * 3:
            return
        corte = len(self.historial) - (self.MAX_HISTORIAL_TURNOS * 3)
        while corte < len(self.historial):
            msg = self.historial[corte]
            if msg['role'] == 'user':
                if corte > 0 and self.historial[corte - 1]['role'] == 'tool':
                    corte += 1
                    continue
                break
            corte += 1
        if corte < len(self.historial):
            self.historial = self.historial[corte:]

    def responder(self, mensaje_usuario: str) -> str:
        """Procesa mensaje del usuario y genera respuesta usando function calling."""
        self.historial.append({'role': 'user', 'content': mensaje_usuario})
        self._recortar_historial()

        mensajes = [{'role': 'system', 'content': self.system_prompt}] + self.historial

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=mensajes,
                tools=self.tools,
                tool_choice='auto',
                max_tokens=512,
                temperature=0.2,
            )
        except Exception as e:
            error = str(e).lower()
            if '401' in error or 'invalid' in error and 'api' in error:
                raise RuntimeError(
                    'API key de OpenAI inválida. Revisa OPENAI_API_KEY en tu archivo .env.'
                ) from e
            if '429' in error or 'rate limit' in error or 'quota' in error:
                raise RuntimeError(
                    'Límite de uso de OpenAI alcanzado. Espera un momento o revisa tu cuota.'
                ) from e
            raise RuntimeError(f'Error al conectar con OpenAI: {e}') from e

        message = response.choices[0].message

        # Ciclo de function calling (con límite para evitar loops)
        iteration = 0
        pedido_creado = False

        while message.tool_calls and iteration < self.MAX_TOOL_ITERATIONS:
            iteration += 1
            self.historial.append({
                'role': 'assistant',
                'content': message.content,
                'tool_calls': [
                    {
                        'id': tc.id,
                        'type': 'function',
                        'function': {
                            'name': tc.function.name,
                            'arguments': tc.function.arguments
                        }
                    } for tc in message.tool_calls
                ]
            })

            for tool_call in message.tool_calls:
                nombre_fn = tool_call.function.name
                args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                resultado = self._ejecutar_funcion(nombre_fn, args)

                if nombre_fn == 'crear_pedido':
                    pedido_creado = True

                self.historial.append({
                    'role': 'tool',
                    'tool_call_id': tool_call.id,
                    'content': resultado
                })

            mensajes = [{'role': 'system', 'content': self.system_prompt}] + self.historial
            try:
                kwargs = {
                    'model': self.MODEL,
                    'messages': mensajes,
                    'max_tokens': 512,
                    'temperature': 0.2,
                    'tools': self.tools,
                    'tool_choice': 'none' if pedido_creado else 'auto',
                }
                response = self.client.chat.completions.create(**kwargs)
                message = response.choices[0].message
            except Exception as e:
                raise RuntimeError(f'Error al conectar con OpenAI: {e}') from e

        respuesta = message.content
        self.historial.append({'role': 'assistant', 'content': respuesta})
        return respuesta

    def _ejecutar_funcion(self, nombre: str, args: dict) -> str:
        """Ejecuta una función por nombre con los argumentos dados."""
        if nombre not in FUNCIONES_DISPONIBLES:
            return json.dumps({'error': f'Función {nombre} no encontrada'})
        if not args:
            args = {}
        # Corrección: el modelo a veces usa 'tipo' en vez de 'condicion'
        if nombre == 'generar_lista_compra' and 'tipo' in args and 'condicion' not in args:
            args['condicion'] = args.pop('tipo')
        if nombre == 'generar_lista_compra':
            for alias in ('presupuesto', 'presupuesto_maximo', 'budget'):
                if alias in args and 'presupuesto_max' not in args:
                    args['presupuesto_max'] = args.pop(alias)
        try:
            resultado = FUNCIONES_DISPONIBLES[nombre](**args)
            return json.dumps(resultado, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({'error': f'Error ejecutando {nombre}: {str(e)}'}, ensure_ascii=False)
