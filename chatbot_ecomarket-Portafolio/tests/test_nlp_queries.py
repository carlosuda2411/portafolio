"""Tests de NLP local y búsqueda de productos."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('LOCAL_NLP_ENABLED', 'true')

from src.intent_router import clasificar_intencion, _extraer_por_patrones, PATRONES_PRODUCTO
from src.local_responder import responder_local
from src.queries import buscar_producto
from src.database import obtener_info_bd


class TestNLP(unittest.TestCase):
    def test_leche_generica(self):
        i = clasificar_intencion('tienen leche?')
        self.assertEqual(i.nombre, 'buscar_producto')
        self.assertEqual(i.entidades['nombre'], 'leche')

    def test_tipos_de_leche(self):
        for q in ('que tipos de leche tienes', 'que tipos de leche hay', 'qué tipos de leche hayç'):
            i = clasificar_intencion(q)
            self.assertEqual(i.nombre, 'buscar_producto', msg=q)
            self.assertEqual(i.entidades['nombre'], 'leche', msg=q)
        r = responder_local('que tipos de leche hay')
        self.assertIsNotNone(r)
        self.assertIn('Leche Entera', r)
        self.assertIn('Leche de Almendra', r)
        self.assertIn('Leche Infantil', r)
        self.assertNotIn('Mantequilla', r)
        self.assertNotIn('Yogur', r)

    def test_leche_especifica(self):
        i = clasificar_intencion('quiero leche entera')
        self.assertEqual(i.entidades['nombre'], 'Leche Entera')

    def test_congelados_categoria(self):
        i = clasificar_intencion('tienes congelados')
        self.assertEqual(i.nombre, 'buscar_categoria')
        self.assertEqual(i.entidades['categoria'], 'Congelados')

    def test_snacks_categoria(self):
        i = clasificar_intencion('hay snacks')
        self.assertEqual(i.nombre, 'buscar_categoria')

    def test_bebidas_categoria(self):
        i = clasificar_intencion('bebidas')
        self.assertEqual(i.nombre, 'buscar_categoria')

    def test_patron_de_huevos(self):
        termino = _extraer_por_patrones('stock de huevos', PATRONES_PRODUCTO)
        self.assertEqual(termino, 'huevos')

    def test_mis_pedidos_pide_email(self):
        i = clasificar_intencion('mis pedidos')
        self.assertEqual(i.nombre, 'pedir_email')
        r = responder_local('mis pedidos')
        self.assertIsNotNone(r)
        self.assertIn('email', r.lower())

    def test_crear_pedido_va_a_llm(self):
        consultas = (
            'quiero hacer un pedido',
            'hacer pedido de 2 leches',
            'confirmo el pedido',
            'quiero comprar leche entera',
            'pedir 2 leches enteras a domicilio',
            'ignacio.ros@email.com',
            'ignacio.ros@email.com, Calle Mayor 15, Madrid',
            '20 yogures y dos de aceite',
            '2 aceites de oliva',
        )
        for q in consultas:
            self.assertIsNone(clasificar_intencion(q), msg=q)
            self.assertIsNone(responder_local(q), msg=q)

    def test_pedidos_de_email_consulta(self):
        i = clasificar_intencion('pedidos de ignacio.ros@email.com')
        self.assertEqual(i.nombre, 'consultar_pedidos')
        self.assertEqual(i.entidades['email'], 'ignacio.ros@email.com')

    def test_promociones_top_cinco(self):
        from src.queries import obtener_promociones, PROMOS_DESTACADAS
        from src.local_responder import responder_local
        r = obtener_promociones()
        self.assertEqual(r['mostrando'], PROMOS_DESTACADAS)
        self.assertTrue(r['hay_mas'])
        self.assertTrue(r['vista_resumida'])
        self.assertGreater(r['total_disponibles'], PROMOS_DESTACADAS)
        texto = responder_local('que promociones hay')
        self.assertIsNotNone(texto)
        self.assertIn('Principales promociones', texto)
        self.assertIn('Todas las promociones', texto)

    def test_promociones_todas(self):
        from src.queries import obtener_promociones
        i = clasificar_intencion('todas las promociones')
        self.assertEqual(i.nombre, 'promociones')
        self.assertTrue(i.entidades.get('todas'))
        r = obtener_promociones(todas=True)
        self.assertEqual(r['mostrando'], r['total_disponibles'])
        self.assertFalse(r.get('hay_mas'))

    def test_promociones_filtro_categoria(self):
        from src.queries import obtener_promociones
        i = clasificar_intencion('promociones de lacteos')
        self.assertEqual(i.nombre, 'promociones')
        self.assertEqual(i.entidades.get('categoria'), 'Lacteos')
        r = obtener_promociones(categoria='Lacteos')
        self.assertTrue(r['filtrado'])
        self.assertTrue(all('Lacteos' in p['categoria'] for p in r['promociones']))

    def test_promociones_filtro_martes(self):
        from src.queries import obtener_promociones
        from src.local_responder import responder_local
        i = clasificar_intencion('promociones del martes')
        self.assertEqual(i.entidades.get('dia'), 'martes')
        r = obtener_promociones(dia='martes')
        self.assertTrue(r['filtrado'])
        self.assertTrue(r.get('filtro_dia_exclusivo'))
        productos = [p['producto'] for p in r['promociones']]
        self.assertIn('Pan Integral', productos)
        self.assertNotIn('Leche Entera', productos)
        self.assertGreater(r.get('promos_habituales_vigentes', 0), 0)
        texto = responder_local('promociones del martes')
        self.assertIn('exclusivas del martes', texto)
        self.assertIn('habituales', texto.lower())

    def test_frutas_listado(self):
        i = clasificar_intencion('que frutas hay')
        self.assertEqual(i.nombre, 'buscar_categoria')
        self.assertEqual(i.entidades['categoria'], 'Frutas y Verduras')
        self.assertEqual(i.entidades.get('subtipo'), 'frutas')
        r = responder_local('que frutas hay?')
        self.assertIsNotNone(r)
        self.assertIn('Frutas', r)
        self.assertIn('Manzana', r)
        self.assertNotIn('Papillas', r)
        self.assertNotIn('Lechuga', r)
        self.assertNotIn('Tomate', r)

    def test_verduras_listado(self):
        i = clasificar_intencion('que verduras hay')
        self.assertEqual(i.nombre, 'buscar_categoria')
        self.assertEqual(i.entidades['categoria'], 'Frutas y Verduras')
        self.assertEqual(i.entidades.get('subtipo'), 'verduras')
        r = responder_local('que verduras hay?')
        self.assertIsNotNone(r)
        self.assertIn('Verduras', r)
        self.assertIn('Lechuga', r)
        self.assertNotIn('Manzana', r)
        self.assertNotIn('Platano', r)

    def test_devolucion_va_a_llm(self):
        self.assertIsNone(clasificar_intencion('devolver pedido'))


class TestQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not obtener_info_bd().get('existe'):
            raise unittest.SkipTest('BD no encontrada; ejecuta scripts/regenerate_db.py')

    def test_pan_sin_falsos_positivos(self):
        nombres = [p['nombre'] for p in buscar_producto('pan')]
        self.assertIn('Pan Integral', nombres)
        self.assertNotIn('Panales Talla 3', nombres)
        self.assertNotIn('Pescado Empanado', nombres)

    def test_lasagna_fuzzy(self):
        self.assertTrue(buscar_producto('lasagna'))

    def test_lista_saludable_respeta_presupuesto(self):
        from src.queries import generar_lista_compra
        r = generar_lista_compra('saludable', presupuesto_max=30)
        self.assertNotIn('error', r)
        self.assertLessEqual(r['total_estimado'], 30)
        self.assertTrue(r['dentro_presupuesto'])
        suma = round(sum(p['precio_efectivo'] for p in r['productos']), 2)
        self.assertEqual(r['total_estimado'], suma)

    def test_promo_pienso_no_en_gel(self):
        gel = buscar_producto('Gel de Bano')
        self.assertTrue(gel)
        promo = gel[0].get('promocion')
        self.assertTrue(promo is None or 'pienso' not in promo['descripcion'].lower())

    def test_pan_integral_promo_solo_martes(self):
        from datetime import datetime
        from src.queries import _fetch_promo_producto, _promo_aplicable_hoy, _precio_efectivo, buscar_producto
        from src.database import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, precio FROM productos WHERE nombre='Pan Integral'")
        pan_id, precio = cursor.fetchone()
        promo = _fetch_promo_producto(cursor, pan_id)
        conn.close()

        self.assertIsNotNone(promo)
        martes = datetime(2026, 6, 16, 12, 0, 0)
        miercoles = datetime(2026, 6, 17, 12, 0, 0)
        self.assertTrue(_promo_aplicable_hoy(promo, martes))
        self.assertFalse(_promo_aplicable_hoy(promo, miercoles))
        self.assertEqual(_precio_efectivo(precio, promo), 1.05)
        self.assertEqual(_precio_efectivo(precio, promo if _promo_aplicable_hoy(promo, miercoles) else None), precio)

        pan = buscar_producto('Pan Integral')[0]
        if datetime.now().weekday() == 1:
            self.assertEqual(pan['precio_efectivo'], 1.05)
            self.assertTrue(pan.get('promocion_aplicable_hoy'))
        else:
            self.assertEqual(pan['precio_efectivo'], precio)
            self.assertFalse(pan.get('promocion_aplicable_hoy'))

    def test_precio_efectivo_con_promo(self):
        from src.queries import _precio_efectivo, calcular_total_pedido, buscar_producto
        self.assertEqual(_precio_efectivo(1.20, {'descuento_porcentaje': 20.0}), 0.96)
        self.assertEqual(_precio_efectivo(1.20, None), 1.20)

        leche = buscar_producto('Leche Entera')
        self.assertTrue(leche)
        if leche[0].get('promocion'):
            self.assertEqual(leche[0]['precio_efectivo'], 0.96)

        total = calcular_total_pedido([
            {'nombre': 'Leche Entera', 'cantidad': 2},
            {'nombre': 'Pan Integral', 'cantidad': 1},
        ])
        self.assertNotIn('error', total)
        suma_lineas = round(sum(i['subtotal'] for i in total['items']), 2)
        self.assertEqual(total['subtotal_productos'], suma_lineas)
        self.assertEqual(total['costo_domicilio'], 2.0)
        self.assertEqual(total['total'], round(suma_lineas + 2.0, 2))


if __name__ == '__main__':
    unittest.main()
