"""
Router/Orquestador del chatbot EcoMarket.
Consultas sencillas → NLP local (sin tokens).
Consultas complejas → OpenAI con herramientas.
"""
from .agent import EcoMarketBot
from .intent_router import invalidar_cache_catalogo
from .local_responder import responder_local


class EcoMarketRouter:
    """Orquesta respuestas locales y respuestas con LLM."""

    def __init__(self):
        self.bot = EcoMarketBot()
        self.ultima_fuente = 'llm'  # 'local' | 'llm'

    def resetear_conversacion(self):
        self.bot.resetear_conversacion()
        self.ultima_fuente = 'llm'

    def recargar_catalogo(self):
        invalidar_cache_catalogo()
        self.bot.actualizar_catalogo()

    def responder(self, mensaje: str) -> str:
        respuesta_local = responder_local(mensaje)
        if respuesta_local is not None:
            self.ultima_fuente = 'local'
            self.bot.registrar_turno(mensaje, respuesta_local)
            return respuesta_local

        self.ultima_fuente = 'llm'
        return self.bot.responder(mensaje)


def crear_bot() -> EcoMarketBot:
    """Compatibilidad con código que instancia el bot directamente."""
    return EcoMarketBot()


def crear_router() -> EcoMarketRouter:
    """Crea el orquestador recomendado."""
    return EcoMarketRouter()
