from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify

from .forms import (
    CompanionForm,
    PhotoForm,
    RegistroActividadForm,
    ViajeForm,
)
from .money import format_clp
from .models import Actividad, Dia, Photo, Viaje


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
            "dias_viaje_en_edicion": (
                viaje_en_edicion.dias.prefetch_related(
                    Prefetch(
                        "actividades",
                        queryset=Actividad.objects.order_by("hora"),
                    )
                ).order_by("numero_dia")
                if viaje_en_edicion
                else ()
            ),
            "actividades_sin_dia_en_edicion": (
                viaje_en_edicion.actividades.filter(dia__isnull=True).order_by(
                    "fecha", "hora", "pk"
                )
                if viaje_en_edicion
                else ()
            ),
            "fotos_viaje_en_edicion": (
                _fotos_viaje(viaje_en_edicion) if viaje_en_edicion else ()
            ),
            "presupuesto_gastado_viaje_en_edicion": (
                format_clp(viaje_en_edicion.presupuesto_gastado)
                if viaje_en_edicion
                else None
            ),
            "cantidad_viajes": Viaje.objects.count(),
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


def _fotos_viaje(viaje):
    return (
        Photo.objects.filter(Q(viaje=viaje) | Q(dia__viaje=viaje))
        .select_related("viaje", "dia")
        .order_by("fecha_subida", "pk")
    )


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


@permission_required("viajes.add_actividad", login_url="login")
def agregar_actividad(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if not viaje.publico and not request.user.has_perm("viajes.view_viaje"):
        raise PermissionDenied("No tienes permiso para agregar actividades a este viaje.")

    form = RegistroActividadForm(
        request.POST or None,
        viaje=viaje,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Actividad registrada correctamente.")
        return redirect("editar_viaje", viaje_id=viaje.pk)

    return render(
        request,
        "viajes/agregar_actividad.html",
        {
            "form": form,
            "viaje": viaje,
            "presupuesto_gastado": format_clp(viaje.presupuesto_gastado),
        },
    )


@permission_required("viajes.change_actividad", login_url="login")
def editar_actividad(request, viaje_id, actividad_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if not viaje.publico and not request.user.has_perm("viajes.view_viaje"):
        raise PermissionDenied("No tienes permiso para editar actividades de este viaje.")
    actividad = get_object_or_404(
        Actividad.objects.filter(viaje=viaje, dia__isnull=True),
        pk=actividad_id,
    )
    form = RegistroActividadForm(
        request.POST or None,
        instance=actividad,
        viaje=viaje,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Actividad actualizada correctamente.")
        return redirect("editar_viaje", viaje_id=viaje.pk)

    return render(
        request,
        "viajes/agregar_actividad.html",
        {
            "form": form,
            "viaje": viaje,
            "actividad": actividad,
            "presupuesto_gastado": format_clp(viaje.presupuesto_gastado),
        },
    )


@permission_required("viajes.delete_actividad", login_url="login")
def eliminar_actividad(request, viaje_id, actividad_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if not viaje.publico and not request.user.has_perm("viajes.view_viaje"):
        raise PermissionDenied("No tienes permiso para eliminar actividades de este viaje.")
    if request.method != "POST":
        return redirect("editar_viaje", viaje_id=viaje.pk)

    actividad = get_object_or_404(
        Actividad.objects.filter(viaje=viaje, dia__isnull=True),
        pk=actividad_id,
    )
    nombre = actividad.nombre
    actividad.delete()
    messages.success(request, f"La actividad «{nombre}» se eliminó correctamente.")
    return redirect("editar_viaje", viaje_id=viaje.pk)


def detalle_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if not viaje.publico and not request.user.has_perm("viajes.view_viaje"):
        raise PermissionDenied("No tienes permiso para ver este viaje.")
    if request.method != "GET":
        return HttpResponseForbidden("Esta vista solo permite consultar los detalles.")

    gastado = viaje.presupuesto_gastado
    context = {
        "viaje": viaje,
        "actividades": (
            Actividad.objects.filter(
                Q(viaje=viaje) | Q(dia__viaje=viaje)
            )
            .select_related("dia")
            .annotate(fecha_actividad=Coalesce("fecha", "dia__fecha"))
            .order_by("fecha_actividad", "hora", "pk")
        ),
        "fotos_viaje": _fotos_viaje(viaje),
        "presupuesto_total": viaje.presupuesto,
        "presupuesto_gastado": gastado,
        "presupuesto_disponible": viaje.presupuesto - gastado,
        "presupuesto_total_formateado": format_clp(viaje.presupuesto),
        "presupuesto_gastado_formateado": format_clp(gastado),
        "presupuesto_disponible_formateado": format_clp(viaje.presupuesto - gastado),
    }
    return render(request, "viajes/ver_detalle_viaje.html", context)


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
def agregar_foto_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if not viaje.publico and not request.user.has_perm("viajes.view_viaje"):
        raise PermissionDenied("No tienes permiso para agregar fotos a este viaje.")

    if request.method == "POST":
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.viaje = viaje
            foto.dia = None
            foto.save()
            messages.success(request, "Foto agregada correctamente.")
            return redirect("editar_viaje", viaje_id=viaje.pk)
    else:
        form = PhotoForm()

    return render(
        request,
        "viajes/agregar_foto_viaje.html",
        {"form": form, "viaje": viaje},
    )


@permission_required("viajes.change_photo", login_url="login")
def editar_foto_viaje(request, viaje_id, foto_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if not viaje.publico and not request.user.has_perm("viajes.view_viaje"):
        raise PermissionDenied("No tienes permiso para editar fotos de este viaje.")
    foto = get_object_or_404(
        Photo.objects.filter(Q(viaje=viaje) | Q(dia__viaje=viaje)),
        pk=foto_id,
    )
    form = PhotoForm(request.POST or None, request.FILES or None, instance=foto)
    if request.method == "POST" and form.is_valid():
        imagen_anterior = foto.imagen
        foto = form.save()
        if imagen_anterior and imagen_anterior.name != foto.imagen.name:
            imagen_anterior.delete(save=False)
        messages.success(request, "Foto actualizada correctamente.")
        return redirect("editar_viaje", viaje_id=viaje.pk)

    return render(
        request,
        "viajes/agregar_foto_viaje.html",
        {"form": form, "viaje": viaje, "foto": foto},
    )


@permission_required("viajes.delete_photo", login_url="login")
def eliminar_foto_viaje(request, viaje_id, foto_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if not viaje.publico and not request.user.has_perm("viajes.view_viaje"):
        raise PermissionDenied("No tienes permiso para eliminar fotos de este viaje.")
    if request.method != "POST":
        return redirect("editar_viaje", viaje_id=viaje.pk)

    foto = get_object_or_404(
        Photo.objects.filter(Q(viaje=viaje) | Q(dia__viaje=viaje)),
        pk=foto_id,
    )
    imagen = foto.imagen
    foto.delete()
    if imagen:
        imagen.delete(save=False)
    messages.success(request, "Foto eliminada correctamente.")
    return redirect("editar_viaje", viaje_id=viaje.pk)


def descargar_fotos_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if not viaje.publico and not request.user.has_perm("viajes.view_viaje"):
        raise PermissionDenied("No tienes permiso para descargar fotos de este viaje.")
    if request.method != "GET":
        return HttpResponseForbidden("La descarga solo permite solicitudes GET.")

    fotos = _fotos_viaje(viaje)
    archivo_zip = BytesIO()
    with ZipFile(archivo_zip, "w", compression=ZIP_DEFLATED) as zip_file:
        for index, foto in enumerate(fotos, start=1):
            nombre_archivo = PurePosixPath(foto.imagen.name).name
            ruta_en_zip = f"{index:03d}_{nombre_archivo}"
            with foto.imagen.open("rb") as imagen:
                zip_file.writestr(ruta_en_zip, imagen.read())

    nombre_viaje = slugify(viaje.titulo) or f"viaje-{viaje.pk}"
    response = HttpResponse(archivo_zip.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = (
        f'attachment; filename="{nombre_viaje}-fotos.zip"'
    )
    return response


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
