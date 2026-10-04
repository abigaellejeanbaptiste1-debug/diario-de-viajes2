from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from zipfile import ZipFile

from .forms import GastoForm
from .money import format_clp
from .models import Actividad, Dia, Gasto, Photo, Viaje


class PresupuestoViajeTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="prueba-segura-123",
        )
        self.client.force_login(self.usuario)
        self.viaje = Viaje.objects.create(
            titulo="Torres del Paine",
            fecha_fin="2026-12-20",
            pais="Chile",
            ciudad="Puerto Natales",
            presupuesto=Decimal("500000.00"),
        )

    def test_presupuesto_gastado_suma_costos_de_actividades(self):
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("0.00"))

        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
        )
        Actividad.objects.create(
            dia=dia,
            nombre="Hostal",
            hora="14:00",
            costo=Decimal("45000"),
        )
        Actividad.objects.create(
            dia=dia,
            nombre="Cena",
            hora="20:00",
            costo=Decimal("12500"),
        )

        Gasto.objects.create(
            viaje=self.viaje,
            categoria="Otros",
            monto=Decimal("100000.00"),
            fecha="2026-12-10",
            concepto="Registro antiguo",
        )

        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("57500.00"))
        self.assertEqual(dia.gastos_totales, Decimal("57500.00"))
        self.assertEqual(dia.gastos_totales_formateados, "$57.500")

    def test_detalle_no_acepta_registro_de_gasto_por_separado(self):
        response = self.client.post(
            reverse("detalle_viaje", args=[self.viaje.pk]),
            {
                "form_gasto": "1",
                "categoria": "Transporte",
                "monto": "15000",
                "fecha": "2026-12-10",
                "concepto": "Bus",
                "moneda": "CLP",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Gasto.objects.filter(viaje=self.viaje).exists())
        detalle = self.client.get(reverse("detalle_viaje", args=[self.viaje.pk]))
        self.assertNotContains(detalle, "Registrar gasto")

    def test_formulario_acepta_solo_pesos_enteros_y_moneda_clp(self):
        datos = {
            "categoria": "Alojamiento",
            "monto": "45000",
            "fecha": "2026-12-10",
            "concepto": "Hostal",
            "moneda": "CLP",
        }
        self.assertTrue(GastoForm(data=datos).is_valid())

        datos["monto"] = "45000.50"
        self.assertFalse(GastoForm(data=datos).is_valid())

        datos["monto"] = "-1"
        self.assertFalse(GastoForm(data=datos).is_valid())

        datos["monto"] = "45000"
        datos["moneda"] = "USD"
        self.assertFalse(GastoForm(data=datos).is_valid())

    def test_formatea_clp_con_separador_de_miles_chileno(self):
        self.assertEqual(format_clp(Decimal("1234567")), "$1.234.567")

    def test_listado_muestra_enlace_al_detalle_del_viaje(self):
        response = self.client.get(reverse("lista_viajes"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mis Viajes Registrados")
        self.assertContains(
            response, reverse("detalle_viaje", args=[self.viaje.pk])
        )
        self.assertContains(response, self.viaje.titulo)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertNotContains(response, "{% csrf_token")

    def test_listado_vacio_muestra_el_estado_vacio(self):
        self.viaje.delete()

        response = self.client.get(reverse("lista_viajes"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No hay viajes")
        self.assertNotContains(response, "Viaje a Noruega: Tromsø")

    def test_viajes_privados_no_se_muestran_sin_permiso_de_lectura(self):
        self.viaje.publico = False
        self.viaje.save(update_fields=["publico"])
        self.client.logout()

        listado = self.client.get(reverse("lista_viajes"))
        detalle = self.client.get(reverse("detalle_viaje", args=[self.viaje.pk]))

        self.assertNotContains(listado, self.viaje.titulo)
        self.assertEqual(detalle.status_code, 403)

    def test_detalle_muestra_solo_datos_y_actividades_sin_agregar_dia(self):
        detalle_url = reverse("detalle_viaje", args=[self.viaje.pk])
        response = self.client.get(detalle_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/"')
        self.assertContains(response, "Volver al listado")
        self.assertContains(response, self.viaje.titulo)
        self.assertContains(response, "Actividades")
        self.assertNotContains(response, "Agregar actividad")
        self.assertNotContains(
            response,
            reverse("agregar_actividad", args=[self.viaje.pk]),
        )
        self.assertNotContains(response, "Agregar Día")
        self.assertNotContains(response, "Secuencia Temporal")
        self.assertNotContains(response, "Itinerario de Viaje")
        self.assertContains(response, "Todavía no hay imágenes agregadas a este viaje.")

        response = self.client.post(
            detalle_url,
            {
                "form_dia": "1",
                "numero_dia": "1",
                "fecha": "2026-12-10",
                "titulo": "Llegada",
                "descripcion": "Primer día del viaje",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Dia.objects.filter(viaje=self.viaje, titulo="Llegada").exists())

    def test_detalle_muestra_actividades_anteriores_sin_secuencia_de_dias(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
        )
        Actividad.objects.create(
            dia=dia,
            nombre="Caminata",
            hora="09:30",
            ubicacion="Puerto Natales",
            categoria="Excursión",
            costo=Decimal("12500"),
        )
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("12500"))

        detalle = self.client.get(reverse("detalle_viaje", args=[self.viaje.pk]))
        self.assertEqual(detalle.status_code, 200)
        self.assertContains(detalle, "Caminata")
        self.assertContains(detalle, "Excursión")
        self.assertContains(detalle, 'datetime="2026-12-10"')
        self.assertContains(detalle, "$12.500 CLP")
        self.assertContains(detalle, "Gastado en actividades")
        self.assertContains(detalle, "$487.500 CLP")
        self.assertNotContains(detalle, "Llegada")
        self.assertNotContains(detalle, "Día 1")
        self.assertNotContains(detalle, ">Editar<")
        self.assertNotContains(detalle, ">Eliminar<")
        self.assertNotContains(detalle, "Registrar gasto")

    def test_detalle_no_acepta_crear_actividad_asociada_a_un_dia(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
        )

        response = self.client.post(
            reverse("detalle_viaje", args=[self.viaje.pk]),
            {
                "form_actividad": "1",
                "dia_id": str(dia.pk),
                "nombre": "Visita al centro",
                "descripcion": "Recorrido a pie",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Actividad.objects.filter(nombre="Visita al centro").exists())

    def test_pantalla_agregar_actividad_solo_muestra_actividad_fecha_y_monto(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
        )

        response = self.client.get(
            reverse("agregar_actividad", args=[self.viaje.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Actividad")
        self.assertContains(response, "Fecha")
        self.assertContains(response, 'type="date"')
        self.assertContains(response, "Monto gastado (CLP)")
        self.assertEqual(
            set(response.context["form"].fields),
            {"nombre", "fecha", "costo"},
        )

    def test_agregar_actividad_asocia_fecha_y_suma_monto_gastado(self):
        url = reverse("agregar_actividad", args=[self.viaje.pk])

        response = self.client.post(
            url,
            {
                "fecha": "2026-12-10",
                "nombre": "Excursión",
                "costo": "18500",
            },
        )

        self.assertRedirects(response, reverse("editar_viaje", args=[self.viaje.pk]))
        actividad = Actividad.objects.get(nombre="Excursión")
        self.assertEqual(actividad.nombre, "Excursión")
        self.assertEqual(actividad.costo, Decimal("18500"))
        self.assertIsNone(actividad.hora)
        self.assertIsNone(actividad.dia)
        self.assertEqual(actividad.viaje, self.viaje)
        self.assertEqual(actividad.fecha.isoformat(), "2026-12-10")
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("18500"))
        edit_response = self.client.get(
            reverse("editar_viaje", args=[self.viaje.pk])
        )
        self.assertContains(edit_response, "Actividades independientes")
        self.assertContains(edit_response, "Excursión")
        self.assertContains(edit_response, 'datetime="2026-12-10"')
        self.assertContains(
            edit_response,
            reverse("editar_actividad", args=[self.viaje.pk, actividad.pk]),
        )
        self.assertContains(
            edit_response,
            reverse("eliminar_actividad", args=[self.viaje.pk, actividad.pk]),
        )

    def test_agregar_actividad_funciona_sin_dias_registrados(self):
        response = self.client.post(
            reverse("agregar_actividad", args=[self.viaje.pk]),
            {
                "fecha": "2026-12-11",
                "nombre": "Excursión",
                "costo": "18500",
            },
        )

        self.assertRedirects(response, reverse("editar_viaje", args=[self.viaje.pk]))
        actividad = Actividad.objects.get(nombre="Excursión")
        self.assertIsNone(actividad.dia)
        self.assertEqual(actividad.fecha.isoformat(), "2026-12-11")
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("18500"))

    def test_editar_actividad_independiente_actualiza_fecha_y_gasto(self):
        actividad = Actividad.objects.create(
            viaje=self.viaje,
            fecha="2026-12-10",
            nombre="Entrada al museo",
            costo=Decimal("5000"),
        )
        url = reverse(
            "editar_actividad",
            args=[self.viaje.pk, actividad.pk],
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar actividad")
        self.assertEqual(response.context["form"].instance, actividad)

        response = self.client.post(
            url,
            {
                "fecha": "2026-12-11",
                "nombre": "Tour guiado",
                "costo": "12000",
            },
        )

        self.assertRedirects(response, reverse("editar_viaje", args=[self.viaje.pk]))
        actividad.refresh_from_db()
        self.assertEqual(actividad.nombre, "Tour guiado")
        self.assertEqual(actividad.fecha.isoformat(), "2026-12-11")
        self.assertEqual(actividad.costo, Decimal("12000"))
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("12000"))

    def test_eliminar_actividad_independiente_actualiza_gasto(self):
        actividad = Actividad.objects.create(
            viaje=self.viaje,
            fecha="2026-12-10",
            nombre="Entrada al museo",
            costo=Decimal("5000"),
        )

        response = self.client.post(
            reverse(
                "eliminar_actividad",
                args=[self.viaje.pk, actividad.pk],
            )
        )

        self.assertRedirects(response, reverse("editar_viaje", args=[self.viaje.pk]))
        self.assertFalse(Actividad.objects.filter(pk=actividad.pk).exists())
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("0"))

    def test_crud_actividad_independiente_no_permite_otro_viaje(self):
        otro_viaje = Viaje.objects.create(
            titulo="Otro viaje",
            fecha_fin="2026-12-22",
            pais="Chile",
            ciudad="Natales",
            presupuesto=Decimal("100000"),
        )
        actividad = Actividad.objects.create(
            viaje=otro_viaje,
            fecha="2026-12-10",
            nombre="Actividad ajena",
            costo=Decimal("5000"),
        )

        respuestas = [
            self.client.get(
                reverse(
                    "editar_actividad",
                    args=[self.viaje.pk, actividad.pk],
                )
            ),
            self.client.post(
                reverse(
                    "eliminar_actividad",
                    args=[self.viaje.pk, actividad.pk],
                )
            ),
        ]

        self.assertTrue(all(response.status_code == 404 for response in respuestas))
        self.assertTrue(Actividad.objects.filter(pk=actividad.pk).exists())

    def test_crud_actividad_independiente_requiere_permisos(self):
        actividad = Actividad.objects.create(
            viaje=self.viaje,
            fecha="2026-12-10",
            nombre="Entrada al museo",
            costo=Decimal("5000"),
        )
        usuario = get_user_model().objects.create_user(
            username="lector_actividad",
        )
        self.client.force_login(usuario)

        respuestas = [
            self.client.get(
                reverse("editar_actividad", args=[self.viaje.pk, actividad.pk])
            ),
            self.client.post(
                reverse("eliminar_actividad", args=[self.viaje.pk, actividad.pk])
            ),
        ]

        self.assertTrue(all(response.status_code == 302 for response in respuestas))
        self.assertTrue(Actividad.objects.filter(pk=actividad.pk).exists())
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("5000"))

    def test_agregar_actividad_disponible_sin_dias(self):
        response = self.client.get(reverse("agregar_actividad", args=[self.viaje.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Guardar actividad")
        self.assertNotContains(response, "Primero agrega un día")

    def test_detalle_no_permite_editar_dias(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
            descripcion="Descripción anterior",
        )
        detalle_url = reverse("detalle_viaje", args=[self.viaje.pk])

        response = self.client.post(
            detalle_url,
            {
                "form_editar_dia": "1",
                "dia_id": str(dia.pk),
                "numero_dia": "2",
                "fecha": "2026-12-11",
                "titulo": "Llegada actualizada",
                "descripcion": "Descripción nueva",
                "ubicacion_gps": "",
            },
        )

        self.assertEqual(response.status_code, 403)
        dia.refresh_from_db()
        self.assertEqual(dia.numero_dia, 1)
        self.assertEqual(dia.titulo, "Llegada")
        self.assertEqual(dia.descripcion, "Descripción anterior")

    def test_detalle_no_permite_eliminar_dias(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
        )
        actividad = Actividad.objects.create(
            dia=dia,
            nombre="Bus",
            hora="09:30",
            costo=Decimal("12500"),
        )

        response = self.client.post(
            reverse("detalle_viaje", args=[self.viaje.pk]),
            {"eliminar_dia": "1", "dia_id": str(dia.pk)},
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Dia.objects.filter(pk=dia.pk).exists())
        self.assertTrue(Actividad.objects.filter(pk=actividad.pk).exists())
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("12500"))

    def test_detalle_no_permite_editar_actividad(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
        )
        actividad = Actividad.objects.create(
            dia=dia,
            nombre="Bus",
            hora="09:30",
            costo=Decimal("12500"),
        )
        detalle_url = reverse("detalle_viaje", args=[self.viaje.pk])

        response = self.client.get(detalle_url, {"editar_actividad": actividad.pk})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Guardar cambios")
        self.assertNotContains(response, f"?editar_actividad={actividad.pk}")

        response = self.client.post(
            detalle_url,
            {
                "form_editar_actividad": "1",
                "actividad_id": str(actividad.pk),
                "nombre": "Traslado privado",
                "hora": "10:15",
                "ubicacion": "Puerto Natales",
                "categoria": "Transporte",
                "costo": "20000",
                "descripcion": "Traslado al alojamiento",
                "rating": "",
            },
        )

        self.assertEqual(response.status_code, 403)
        actividad.refresh_from_db()
        self.assertEqual(actividad.nombre, "Bus")
        self.assertEqual(actividad.costo, Decimal("12500"))
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("12500"))

    def test_detalle_no_permite_eliminar_actividad(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
        )
        actividad = Actividad.objects.create(
            dia=dia,
            nombre="Bus",
            hora="09:30",
            costo=Decimal("12500"),
        )

        response = self.client.post(
            reverse("detalle_viaje", args=[self.viaje.pk]),
            {"eliminar_actividad": "1", "actividad_id": str(actividad.pk)},
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Actividad.objects.filter(pk=actividad.pk).exists())
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("12500"))

    def test_crud_del_itinerario_rechaza_objetos_de_otro_viaje(self):
        otro_viaje = Viaje.objects.create(
            titulo="Otro viaje",
            fecha_fin="2026-12-22",
            pais="Chile",
            ciudad="Natales",
            presupuesto=Decimal("100000"),
        )
        dia_ajeno = Dia.objects.create(
            viaje=otro_viaje,
            numero_dia=1,
            fecha="2026-12-21",
            titulo="Día ajeno",
        )
        actividad_ajena = Actividad.objects.create(
            dia=dia_ajeno,
            nombre="Actividad ajena",
            hora="09:30",
        )
        detalle_url = reverse("detalle_viaje", args=[self.viaje.pk])

        respuestas = [
            self.client.post(
                detalle_url,
                {
                    "form_editar_dia": "1",
                    "dia_id": str(dia_ajeno.pk),
                    "numero_dia": "2",
                    "fecha": "2026-12-22",
                    "titulo": "Manipulado",
                },
            ),
            self.client.post(
                detalle_url,
                {
                    "eliminar_dia": "1",
                    "dia_id": str(dia_ajeno.pk),
                },
            ),
            self.client.post(
                detalle_url,
                {
                    "form_editar_actividad": "1",
                    "actividad_id": str(actividad_ajena.pk),
                    "nombre": "Manipulada",
                    "hora": "10:00",
                    "costo": "1",
                },
            ),
            self.client.post(
                detalle_url,
                {
                    "eliminar_actividad": "1",
                    "actividad_id": str(actividad_ajena.pk),
                },
            ),
        ]

        self.assertEqual(
            [response.status_code for response in respuestas],
            [403, 403, 403, 403],
        )
        self.assertTrue(Dia.objects.filter(pk=dia_ajeno.pk).exists())
        self.assertTrue(Actividad.objects.filter(pk=actividad_ajena.pk).exists())

    def test_crud_del_itinerario_requiere_permisos_individuales(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
        )
        actividad = Actividad.objects.create(
            dia=dia,
            nombre="Bus",
            hora="09:30",
            costo=Decimal("12500"),
        )
        usuario = get_user_model().objects.create_user(
            username="lector",
            password="clave-segura-123",
        )
        self.client.force_login(usuario)
        detalle_url = reverse("detalle_viaje", args=[self.viaje.pk])
        acciones = [
            {"form_editar_dia": "1", "dia_id": str(dia.pk)},
            {"eliminar_dia": "1", "dia_id": str(dia.pk)},
            {"form_editar_actividad": "1", "actividad_id": str(actividad.pk)},
            {"eliminar_actividad": "1", "actividad_id": str(actividad.pk)},
        ]

        for datos in acciones:
            with self.subTest(accion=next(iter(datos))):
                response = self.client.post(detalle_url, datos)
                self.assertEqual(response.status_code, 403)

        self.assertTrue(Dia.objects.filter(pk=dia.pk).exists())
        self.assertTrue(Actividad.objects.filter(pk=actividad.pk).exists())
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("12500"))

    def test_crear_viaje_desde_el_listado_lo_guarda_y_lo_muestra(self):
        response = self.client.post(
            reverse("lista_viajes"),
            {
                "titulo": "Viaje de prueba",
                "descripcion": "Una escapada",
                "fecha_inicio": "2026-11-01",
                "fecha_fin": "2026-11-05",
                "pais": "Chile",
                "ciudad": "Valdivia",
                "presupuesto": "125000",
                "publico": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        viaje = Viaje.objects.get(titulo="Viaje de prueba")
        listado = self.client.get(reverse("lista_viajes"))
        self.assertContains(listado, reverse("detalle_viaje", args=[viaje.pk]))

    def test_editar_viaje_precarga_datos_y_guarda_cambios(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada a Puerto Natales",
        )
        Actividad.objects.create(
            dia=dia,
            nombre="Traslado al alojamiento",
            hora="09:30",
            ubicacion="Terminal de buses",
            categoria="Transporte",
            costo=Decimal("12500"),
        )
        url = reverse("editar_viaje", args=[self.viaje.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Mis Viajes Registrados")
        self.assertNotContains(response, "Bitácora Personal de Expediciones")
        self.assertNotContains(response, "Presupuesto Global")
        self.assertContains(response, 'value="Torres del Paine"')
        self.assertContains(response, "Actividades del viaje")
        self.assertContains(response, "Agregar actividades")
        self.assertContains(response, "Llegada a Puerto Natales")
        self.assertContains(response, 'datetime="2026-12-10"')
        self.assertContains(response, 'datetime="09:30"')
        self.assertContains(response, "Traslado al alojamiento")
        self.assertContains(response, "Terminal de buses")
        self.assertContains(response, "Total del día: $12.500 CLP")
        self.assertContains(response, "Total gastado: $12.500 CLP")

        response = self.client.post(
            url,
            {
                "titulo": "Torres del Paine actualizado",
                "descripcion": "Descripción actualizada",
                "fecha_inicio": "2026-12-10",
                "fecha_fin": "2026-12-22",
                "pais": "Chile",
                "ciudad": "Natales",
                "presupuesto": "600000",
                "publico": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.viaje.refresh_from_db()
        self.assertEqual(self.viaje.titulo, "Torres del Paine actualizado")

    def test_galeria_muestra_fotos_del_viaje_en_detalle_y_edicion(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
        )
        foto = Photo.objects.create(
            dia=dia,
            imagen=SimpleUploadedFile(
                "foto-viaje.jpg",
                b"contenido de prueba",
                content_type="image/jpeg",
            ),
            descripcion="Vista del destino",
        )
        otro_viaje = Viaje.objects.create(
            titulo="Otro viaje",
            fecha_fin="2026-12-22",
            pais="Chile",
            ciudad="Natales",
            presupuesto=Decimal("100000"),
        )
        otro_dia = Dia.objects.create(
            viaje=otro_viaje,
            numero_dia=1,
            fecha="2026-12-21",
            titulo="Día ajeno",
        )
        otra_foto = Photo.objects.create(
            dia=otro_dia,
            imagen=SimpleUploadedFile(
                "foto-otro-viaje.jpg",
                b"otra imagen",
                content_type="image/jpeg",
            ),
            descripcion="Foto de otro viaje",
        )

        try:
            url = reverse("detalle_viaje", args=[self.viaje.pk])
            detalle = self.client.get(url)
            edicion = self.client.get(
                reverse("editar_viaje", args=[self.viaje.pk])
            )

            for response in (detalle, edicion):
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Imágenes agregadas")
                self.assertContains(response, foto.imagen.url)
                self.assertContains(response, "Vista del destino")
                self.assertNotContains(response, otra_foto.imagen.url)
                self.assertNotContains(response, "Foto de otro viaje")
                self.assertNotContains(response, "Exportar a PDF")

            self.assertNotContains(detalle, "Agregar foto")
            self.assertContains(detalle, "Descargar todas (.zip)")
            self.assertContains(
                detalle,
                reverse("descargar_fotos_viaje", args=[self.viaje.pk]),
            )
            self.assertNotContains(detalle, "Llegada")
            self.assertNotContains(detalle, "Foto del viaje")
            self.assertNotContains(
                detalle,
                reverse("editar_foto_viaje", args=[self.viaje.pk, foto.pk]),
            )
            self.assertNotContains(
                detalle,
                reverse("eliminar_foto_viaje", args=[self.viaje.pk, foto.pk]),
            )
            self.assertNotContains(edicion, "Descargar todas (.zip)")
            self.assertNotContains(
                edicion,
                reverse("descargar_fotos_viaje", args=[self.viaje.pk]),
            )
            self.assertContains(edicion, "Agregar foto", count=1)
            self.assertNotContains(edicion, "Días en Ruta")
            self.assertContains(
                edicion,
                reverse("agregar_foto_viaje", args=[self.viaje.pk]),
            )
            self.assertContains(edicion, "Editar")
            self.assertContains(
                edicion,
                reverse("editar_foto_viaje", args=[self.viaje.pk, foto.pk]),
            )
            self.assertContains(edicion, "Eliminar")
            self.assertContains(
                edicion,
                reverse("eliminar_foto_viaje", args=[self.viaje.pk, foto.pk]),
            )
        finally:
            foto.imagen.delete(save=False)
            otra_foto.imagen.delete(save=False)

    def test_descargar_fotos_comprime_solo_las_imagenes_del_viaje(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
        )
        foto_con_dia = Photo.objects.create(
            dia=dia,
            imagen=SimpleUploadedFile("vista.jpg", b"foto del dia"),
            descripcion="Vista con día",
        )
        foto_independiente = Photo.objects.create(
            viaje=self.viaje,
            imagen=SimpleUploadedFile("playa.png", b"foto independiente"),
            descripcion="Vista independiente",
        )
        otro_viaje = Viaje.objects.create(
            titulo="Viaje ajeno",
            fecha_fin="2026-12-22",
            pais="Chile",
            ciudad="Natales",
        )
        foto_ajena = Photo.objects.create(
            viaje=otro_viaje,
            imagen=SimpleUploadedFile("privada.jpg", b"no incluir"),
        )
        try:
            response = self.client.get(
                reverse("descargar_fotos_viaje", args=[self.viaje.pk])
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/zip")
            self.assertIn("attachment;", response["Content-Disposition"])
            with ZipFile(BytesIO(response.content)) as archivo:
                nombres = archivo.namelist()
                contenidos = {
                    nombre: archivo.read(nombre)
                    for nombre in nombres
                }

            self.assertEqual(len(nombres), 2)
            self.assertTrue(any(nombre.endswith("_vista.jpg") for nombre in nombres))
            self.assertTrue(any(nombre.endswith("_playa.png") for nombre in nombres))
            self.assertCountEqual(
                contenidos.values(),
                [b"foto del dia", b"foto independiente"],
            )
            self.assertFalse(any("privada" in nombre for nombre in nombres))
        finally:
            foto_con_dia.imagen.delete(save=False)
            foto_independiente.imagen.delete(save=False)
            foto_ajena.imagen.delete(save=False)

    def test_descarga_fotos_respeta_acceso_publico_y_privado_y_solo_get(self):
        url = reverse("descargar_fotos_viaje", args=[self.viaje.pk])
        self.client.logout()
        respuesta_publica = self.client.get(url)
        self.assertEqual(respuesta_publica.status_code, 200)

        self.viaje.publico = False
        self.viaje.save(update_fields=["publico"])
        respuesta_privada = self.client.get(url)
        self.assertEqual(respuesta_privada.status_code, 403)

        self.client.force_login(self.usuario)
        respuesta_post = self.client.post(url)
        self.assertEqual(respuesta_post.status_code, 403)

    def test_agregar_foto_directamente_al_viaje_sin_dia(self):
        url = reverse("agregar_foto_viaje", args=[self.viaje.pk])
        formulario = self.client.get(url)
        self.assertEqual(formulario.status_code, 200)
        self.assertContains(formulario, "La imagen se guardará en la galería de este viaje.")
        self.assertContains(formulario, reverse("editar_viaje", args=[self.viaje.pk]))

        image_content = BytesIO()
        Image.new("RGB", (1, 1)).save(image_content, format="JPEG")
        response = self.client.post(
            url,
            {
                "descripcion": "Atardecer en el destino",
                "imagen": SimpleUploadedFile(
                    "atardecer.jpg",
                    image_content.getvalue(),
                    content_type="image/jpeg",
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse("editar_viaje", args=[self.viaje.pk]),
        )
        foto = Photo.objects.get(viaje=self.viaje)
        try:
            self.assertIsNone(foto.dia)
            self.assertEqual(foto.descripcion, "Atardecer en el destino")
            edicion = self.client.get(reverse("editar_viaje", args=[self.viaje.pk]))
            self.assertContains(edicion, "Atardecer en el destino")
            self.assertContains(edicion, foto.imagen.url)
        finally:
            foto.imagen.delete(save=False)

    def test_editar_foto_actualiza_descripcion_y_regresa_a_edicion(self):
        foto = Photo.objects.create(
            viaje=self.viaje,
            imagen=SimpleUploadedFile(
                "foto-editable.jpg",
                b"imagen existente",
                content_type="image/jpeg",
            ),
            descripcion="Descripción anterior",
        )
        try:
            url = reverse("editar_foto_viaje", args=[self.viaje.pk, foto.pk])
            formulario = self.client.get(url)
            self.assertEqual(formulario.status_code, 200)
            self.assertContains(formulario, "Editar foto")

            response = self.client.post(
                url,
                {"descripcion": "Descripción actualizada"},
            )

            self.assertRedirects(response, reverse("editar_viaje", args=[self.viaje.pk]))
            foto.refresh_from_db()
            self.assertEqual(foto.descripcion, "Descripción actualizada")
            detalle = self.client.get(reverse("detalle_viaje", args=[self.viaje.pk]))
            self.assertContains(detalle, "Descripción actualizada")
            self.assertNotContains(
                detalle,
                reverse("editar_foto_viaje", args=[self.viaje.pk, foto.pk]),
            )
            self.assertNotContains(
                detalle,
                reverse("eliminar_foto_viaje", args=[self.viaje.pk, foto.pk]),
            )
        finally:
            foto.imagen.delete(save=False)

    def test_eliminar_foto_solo_desde_edicion(self):
        foto = Photo.objects.create(
            viaje=self.viaje,
            imagen=SimpleUploadedFile(
                "foto-eliminable.jpg",
                b"imagen de prueba",
                content_type="image/jpeg",
            ),
            descripcion="Foto para eliminar",
        )

        response = self.client.post(
            reverse("eliminar_foto_viaje", args=[self.viaje.pk, foto.pk])
        )

        self.assertRedirects(response, reverse("editar_viaje", args=[self.viaje.pk]))
        self.assertFalse(Photo.objects.filter(pk=foto.pk).exists())

    def test_crud_foto_no_permite_fotos_de_otro_viaje(self):
        otro_viaje = Viaje.objects.create(
            titulo="Otro viaje",
            fecha_fin="2026-12-22",
            pais="Chile",
            ciudad="Natales",
            presupuesto=Decimal("100000"),
        )
        foto = Photo.objects.create(
            viaje=otro_viaje,
            imagen=SimpleUploadedFile(
                "foto-ajena.jpg",
                b"foto ajena",
                content_type="image/jpeg",
            ),
        )
        try:
            respuestas = [
                self.client.get(
                    reverse("editar_foto_viaje", args=[self.viaje.pk, foto.pk])
                ),
                self.client.post(
                    reverse("eliminar_foto_viaje", args=[self.viaje.pk, foto.pk])
                ),
            ]

            self.assertEqual([response.status_code for response in respuestas], [404, 404])
            self.assertTrue(Photo.objects.filter(pk=foto.pk).exists())
        finally:
            foto.imagen.delete(save=False)

    def test_crud_fotos_requiere_permisos(self):
        foto = Photo.objects.create(
            viaje=self.viaje,
            imagen=SimpleUploadedFile(
                "foto-sin-permiso.jpg",
                b"foto",
                content_type="image/jpeg",
            ),
            descripcion="Sin cambios",
        )
        usuario = get_user_model().objects.create_user(username="lector_fotos")
        self.client.force_login(usuario)

        respuestas = [
            self.client.get(
                reverse("agregar_foto_viaje", args=[self.viaje.pk])
            ),
            self.client.get(
                reverse("editar_foto_viaje", args=[self.viaje.pk, foto.pk])
            ),
            self.client.post(
                reverse("eliminar_foto_viaje", args=[self.viaje.pk, foto.pk])
            ),
        ]

        self.assertTrue(all(response.status_code == 302 for response in respuestas))
        self.assertTrue(Photo.objects.filter(pk=foto.pk).exists())
        self.assertEqual(foto.descripcion, "Sin cambios")
        foto.imagen.delete(save=False)

    def test_eliminar_viaje_requiere_post_y_confirma(self):
        url = reverse("eliminar_viaje", args=[self.viaje.pk])
        self.assertEqual(self.client.get(url).status_code, 302)

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Viaje.objects.filter(pk=self.viaje.pk).exists())

    def test_crear_editar_y_eliminar_requieren_permisos(self):
        self.client.logout()
        response = self.client.post(
            reverse("lista_viajes"),
            {"titulo": "No autorizado"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

        self.client.force_login(self.usuario)
        self.usuario.is_superuser = False
        self.usuario.is_staff = False
        self.usuario.save()
        self.client.logout()
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("eliminar_viaje", args=[self.viaje.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])
        self.assertTrue(Viaje.objects.filter(pk=self.viaje.pk).exists())

    def test_rechaza_viaje_con_fechas_invertidas(self):
        response = self.client.post(
            reverse("lista_viajes"),
            {
                "titulo": "Viaje inválido",
                "descripcion": "Fechas al revés",
                "fecha_inicio": "2026-12-20",
                "fecha_fin": "2026-12-10",
                "pais": "Chile",
                "ciudad": "Santiago",
                "presupuesto": "100000",
                "publico": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Viaje.objects.filter(titulo="Viaje inválido").exists())

    def test_login_y_logout(self):
        self.client.logout()
        login_url = reverse("login")
        self.assertEqual(self.client.get(login_url).status_code, 200)

        response = self.client.post(
            login_url,
            {"username": "admin", "password": "prueba-segura-123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("lista_viajes"))

        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_csrf_es_obligatorio_en_post(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.usuario)

        response = client.post(
            reverse("lista_viajes"),
            {
                "titulo": "Sin token",
                "fecha_fin": "2026-12-20",
                "pais": "Chile",
                "ciudad": "Santiago",
                "presupuesto": "100000",
                "publico": "on",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Viaje.objects.filter(titulo="Sin token").exists())
