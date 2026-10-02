from decimal import Decimal

from django.test import Client
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import GastoForm
from .money import format_clp
from .models import Dia, Gasto, Viaje


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

    def test_presupuesto_gastado_suma_gastos_y_devuelve_cero_si_no_hay(self):
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("0.00"))

        Gasto.objects.create(
            viaje=self.viaje,
            categoria="Alojamiento",
            monto=Decimal("45000.00"),
            fecha="2026-12-10",
            concepto="Hostal",
        )
        Gasto.objects.create(
            viaje=self.viaje,
            categoria="Comida",
            monto=Decimal("12500.00"),
            fecha="2026-12-10",
            concepto="Cena",
        )

        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("57500.00"))

    def test_detalle_registra_gasto_asociado_al_viaje(self):
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

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"], reverse("detalle_viaje", args=[self.viaje.pk])
        )
        gasto = Gasto.objects.get(viaje=self.viaje)
        self.assertEqual(gasto.monto, Decimal("15000.00"))
        self.assertEqual(self.viaje.presupuesto_gastado, Decimal("15000.00"))
        detalle = self.client.get(reverse("detalle_viaje", args=[self.viaje.pk]))
        self.assertContains(detalle, "Control de gastos")
        self.assertContains(detalle, "$15.000 CLP")

    def test_gasto_se_asocia_a_un_dia_y_se_muestra_en_el_itinerario(self):
        dia = Dia.objects.create(
            viaje=self.viaje,
            numero_dia=1,
            fecha="2026-12-10",
            titulo="Llegada",
        )

        response = self.client.post(
            reverse("detalle_viaje", args=[self.viaje.pk]),
            {
                "form_gasto": "1",
                "dia": str(dia.pk),
                "categoria": "Alojamiento",
                "monto": "45000",
                "fecha": "2026-12-10",
                "concepto": "Hostal",
                "moneda": "CLP",
            },
        )

        self.assertEqual(response.status_code, 302)
        gasto = Gasto.objects.get(viaje=self.viaje)
        self.assertEqual(gasto.dia, dia)

        detalle = self.client.get(reverse("detalle_viaje", args=[self.viaje.pk]))
        self.assertContains(detalle, "Gastos reales del día")
        self.assertContains(detalle, "Hostal")
        self.assertContains(detalle, "$45.000 CLP")

    def test_gasto_no_puede_asociarse_a_un_dia_de_otro_viaje(self):
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

        response = self.client.post(
            reverse("detalle_viaje", args=[self.viaje.pk]),
            {
                "form_gasto": "1",
                "dia": str(dia_ajeno.pk),
                "categoria": "Comida",
                "monto": "5000",
                "fecha": "2026-12-10",
                "concepto": "Almuerzo",
                "moneda": "CLP",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("dia", response.context["form_gasto"].errors)
        self.assertFalse(Gasto.objects.filter(viaje=self.viaje).exists())

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

    def test_detalle_muestra_volver_al_listado_y_agrega_dia(self):
        detalle_url = reverse("detalle_viaje", args=[self.viaje.pk])
        response = self.client.get(detalle_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/"')
        self.assertContains(response, "Volver al listado")
        self.assertContains(response, self.viaje.titulo)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertNotContains(response, "{% csrf_token")

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

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Dia.objects.filter(viaje=self.viaje, titulo="Llegada").exists())

    def test_detalle_registra_actividad_en_el_dia_del_viaje(self):
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
                "nombre": "Caminata",
                "hora": "09:30",
                "ubicacion": "Puerto Natales",
                "categoria": "Excursión",
                "costo": "12500",
                "descripcion": "Recorrido por el centro",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(dia.actividades.get().nombre, "Caminata")

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
        url = reverse("editar_viaje", args=[self.viaje.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Torres del Paine"')

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
