from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ActividadForm,
    CompanionForm,
    DiaForm,
    GastoForm,
    PhotoForm,
    ViajeForm,
)
from .money import format_clp
from .models import Dia, Viaje


def lista_viajes(request):
    if request.method == "POST":
        form = ViajeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Viaje registrado exitosamente.")
            return redirect("lista_viajes")
    else:
        form = ViajeForm()

    viajes = Viaje.objects.all().order_by("-fecha_inicio")
    return render(request, "viajes/detalle_viaje.html", {"form": form, "viajes": viajes})


def detalle_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    dias = viaje.dias.all().order_by("numero_dia")
    gastos = viaje.gastos.all().order_by("-fecha")

    form_gasto = GastoForm()
    form_dia = DiaForm()
    form_actividad = ActividadForm()

    if request.method == "POST" and "form_gasto" in request.POST:
        form_gasto = GastoForm(request.POST)
        if form_gasto.is_valid():
            nuevo_gasto = form_gasto.save(commit=False)
            nuevo_gasto.viaje = viaje
            nuevo_gasto.save()
            messages.success(request, "Gasto registrado correctamente en el presupuesto.")
            return redirect("detalle_viaje", viaje_id=viaje.id)
    elif request.method == "POST" and "form_dia" in request.POST:
        form_dia = DiaForm(request.POST, request.FILES)
        if form_dia.is_valid():
            nuevo_dia = form_dia.save(commit=False)
            nuevo_dia.viaje = viaje
            nuevo_dia.save()
            messages.success(request, "Día registrado correctamente.")
            return redirect("detalle_viaje", viaje_id=viaje.id)
    elif request.method == "POST" and "form_actividad" in request.POST:
        form_actividad = ActividadForm(request.POST)
        if form_actividad.is_valid():
            dia = get_object_or_404(
                viaje.dias, pk=request.POST.get("dia_id")
            )
            nueva_actividad = form_actividad.save(commit=False)
            nueva_actividad.dia = dia
            nueva_actividad.save()
            messages.success(request, "Actividad registrada correctamente.")
            return redirect("detalle_viaje", viaje_id=viaje.id)

    context = {
        "viaje": viaje,
        "dias": dias,
        "gastos": gastos,
        "form_gasto": form_gasto,
        "form_dia": form_dia,
        "form_actividad": form_actividad,
        "presupuesto_total": viaje.presupuesto,
        "presupuesto_gastado": viaje.presupuesto_gastado,
        "presupuesto_disponible": viaje.presupuesto - viaje.presupuesto_gastado,
        "presupuesto_total_formateado": format_clp(viaje.presupuesto),
        "presupuesto_gastado_formateado": format_clp(viaje.presupuesto_gastado),
        "presupuesto_disponible_formateado": format_clp(
            viaje.presupuesto - viaje.presupuesto_gastado
        ),
    }
    return render(request, "viajes/lista_viajes.html", context)


def agregar_companion(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    if request.method == "POST":
        form = CompanionForm(request.POST)
        if form.is_valid():
            companion = form.save(commit=False)
            companion.viaje = viaje
            companion.save()
            messages.success(request, "Acompañante registrado correctamente.")
            return redirect("detalle_viaje", viaje_id=viaje.id)
    else:
        form = CompanionForm()
    return render(
        request, "viajes/agregar_companion.html", {"form": form, "viaje": viaje}
    )


def agregar_photo(request, dia_id):
    dia = get_object_or_404(Dia, pk=dia_id)
    if request.method == "POST":
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.dia = dia
            photo.save()
            messages.success(request, "Foto agregada correctamente.")
            return redirect("detalle_viaje", viaje_id=dia.viaje.id)
    else:
        form = PhotoForm()
    return render(request, "viajes/agregar_photo.html", {"form": form, "dia": dia})
