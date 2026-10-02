from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    ActividadForm,
    CompanionForm,
    DiaForm,
    GastoForm,
    PhotoForm,
    ViajeForm,
)
from .money import format_clp
from .models import Dia, Photo, Viaje


def _render_viajes(request, form=None, editing=False, viaje_en_edicion=None):
    if form is None:
        form = ViajeForm()
    viajes = Viaje.objects.order_by("-fecha_inicio", "-pk")
    if not request.user.has_perm("viajes.view_viaje"):
        viajes = viajes.filter(publico=True)
    page = Paginator(viajes, 10).get_page(request.GET.get("page"))
    presupuesto_global = Viaje.objects.aggregate(total=Sum("presupuesto"))["total"]
    return render(
        request,
        "viajes/detalle_viaje.html",
        {
            "form": form,
            "viajes": page,
            "editing": editing,
            "viaje_en_edicion": viaje_en_edicion,
            "cantidad_viajes": Viaje.objects.count(),
            "dias_registrados": Dia.objects.count(),
            "presupuesto_global_formateado": format_clp(presupuesto_global or 0),
            "cantidad_fotos": Photo.objects.count(),
        },
    )


def _check_permission(request, permission):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    if not request.user.has_perm(permission):
        raise PermissionDenied("No tienes permiso para realizar esta acción.")
    return None


def lista_viajes(request):
    if request.method == "POST":
        denied = _check_permission(request, "viajes.add_viaje")
        if denied:
            return denied
        form = ViajeForm(request.POST)
        if form.is_valid():
            if (
                not form.cleaned_data["publico"]
                and not request.user.has_perm("viajes.view_viaje")
            ):
                form.add_error(
                    "publico",
                    "Necesitas permiso de lectura para crear un viaje privado.",
                )
                return _render_viajes(request, form=form)
            form.save()
            messages.success(request, "Viaje registrado exitosamente.")
            return redirect("lista_viajes")
        return _render_viajes(request, form=form)

    return _render_viajes(request)


@permission_required("viajes.change_viaje", login_url="login")
def editar_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if not viaje.publico and not request.user.has_perm("viajes.view_viaje"):
        raise PermissionDenied("No tienes permiso para editar este viaje privado.")
    if request.method == "POST":
        form = ViajeForm(request.POST, instance=viaje)
        if form.is_valid():
            if (
                not form.cleaned_data["publico"]
                and not request.user.has_perm("viajes.view_viaje")
            ):
                form.add_error(
                    "publico",
                    "Necesitas permiso de lectura para mantener un viaje privado.",
                )
                return _render_viajes(
                    request, form=form, editing=True, viaje_en_edicion=viaje
                )
            form.save()
            messages.success(request, "Viaje actualizado exitosamente.")
            return redirect("detalle_viaje", viaje_id=viaje.pk)
    else:
        form = ViajeForm(instance=viaje)

    return _render_viajes(
        request, form=form, editing=True, viaje_en_edicion=viaje
    )


@permission_required("viajes.delete_viaje", login_url="login")
def eliminar_viaje(request, viaje_id):
    if request.method != "POST":
        return redirect("lista_viajes")

    viaje = get_object_or_404(Viaje, pk=viaje_id)
    titulo = viaje.titulo
    viaje.delete()
    messages.success(request, f"El viaje «{titulo}» se eliminó correctamente.")
    return redirect("lista_viajes")


def detalle_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if not viaje.publico and not request.user.has_perm("viajes.view_viaje"):
        raise PermissionDenied("No tienes permiso para ver este viaje.")
    dias = viaje.dias.prefetch_related("actividades").order_by("numero_dia")
    gastos = viaje.gastos.all().order_by("-fecha")

    form_gasto = GastoForm()
    form_dia = DiaForm()
    form_actividad = ActividadForm()
    dia_id_formulario = None

    if request.method == "POST":
        permission_map = {
            "form_gasto": "viajes.add_gasto",
            "form_dia": "viajes.add_dia",
            "form_actividad": "viajes.add_actividad",
        }
        permission = next(
            (perm for marker, perm in permission_map.items() if marker in request.POST),
            None,
        )
        if permission is None:
            return HttpResponseForbidden("Acción no permitida.")
        denied = _check_permission(request, permission)
        if denied:
            return denied

    if request.method == "POST" and "form_gasto" in request.POST:
        form_gasto = GastoForm(request.POST)
        if form_gasto.is_valid():
            nuevo_gasto = form_gasto.save(commit=False)
            nuevo_gasto.viaje = viaje
            nuevo_gasto.save()
            messages.success(request, "Gasto registrado correctamente en el presupuesto.")
            return redirect("detalle_viaje", viaje_id=viaje.pk)
    elif request.method == "POST" and "form_dia" in request.POST:
        form_dia = DiaForm(request.POST, request.FILES)
        if form_dia.is_valid():
            nuevo_dia = form_dia.save(commit=False)
            nuevo_dia.viaje = viaje
            nuevo_dia.save()
            messages.success(request, "Día registrado correctamente.")
            return redirect("detalle_viaje", viaje_id=viaje.pk)
    elif request.method == "POST" and "form_actividad" in request.POST:
        dia = get_object_or_404(viaje.dias, pk=request.POST.get("dia_id"))
        dia_id_formulario = dia.pk
        form_actividad = ActividadForm(request.POST)
        if form_actividad.is_valid():
            nueva_actividad = form_actividad.save(commit=False)
            nueva_actividad.dia = dia
            nueva_actividad.save()
            messages.success(request, "Actividad registrada correctamente.")
            return redirect("detalle_viaje", viaje_id=viaje.pk)

    gastado = viaje.presupuesto_gastado
    context = {
        "viaje": viaje,
        "dias": dias,
        "gastos": gastos,
        "form_gasto": form_gasto,
        "form_dia": form_dia,
        "form_actividad": form_actividad,
        "dia_id_formulario": dia_id_formulario,
        "presupuesto_total": viaje.presupuesto,
        "presupuesto_gastado": gastado,
        "presupuesto_disponible": viaje.presupuesto - gastado,
        "presupuesto_total_formateado": format_clp(viaje.presupuesto),
        "presupuesto_gastado_formateado": format_clp(gastado),
        "presupuesto_disponible_formateado": format_clp(viaje.presupuesto - gastado),
    }
    return render(request, "viajes/lista_viajes.html", context)


@permission_required("viajes.add_companion", login_url="login")
def agregar_companion(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if request.method == "POST":
        form = CompanionForm(request.POST)
        if form.is_valid():
            companion = form.save(commit=False)
            companion.viaje = viaje
            companion.save()
            messages.success(request, "Acompañante registrado correctamente.")
            return redirect("detalle_viaje", viaje_id=viaje.pk)
    else:
        form = CompanionForm()
    return render(
        request, "viajes/agregar_companion.html", {"form": form, "viaje": viaje}
    )


@permission_required("viajes.add_photo", login_url="login")
def agregar_photo(request, dia_id):
    dia = get_object_or_404(Dia, pk=dia_id)
    if request.method == "POST":
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.dia = dia
            photo.save()
            messages.success(request, "Foto agregada correctamente.")
            return redirect("detalle_viaje", viaje_id=dia.viaje_id)
    else:
        form = PhotoForm()
    return render(request, "viajes/agregar_photo.html", {"form": form, "dia": dia})


class ViajesLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True


def cerrar_sesion(request):
    if request.method != "POST":
        return redirect("lista_viajes")
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect("lista_viajes")
