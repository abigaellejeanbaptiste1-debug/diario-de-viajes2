from django.shortcuts import render, get_object_or_404, redirect
from .models import Viaje, Dia, Actividad, Photo, Companion
from .forms import ViajeForm, DiaForm, ActividadForm, PhotoForm, CompanionForm

def lista_viajes(request):
    if request.method == 'POST':
        form = ViajeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_viajes')
    else:
        form = ViajeForm()

    viajes = Viaje.objects.all().order_by('-fecha_inicio')
    return render(request, 'viajes/lista_viajes.html', {'form': form, 'viajes': viajes})

def detalle_viaje(request, viaje_id):
    """
    Affiche les détails d'un voyage, la liste de ses jours et permet d'ajouter un jour ou une activité.
    """
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    dias = viaje.dias.all().order_by('numero_dia')


    if 'form_dia' in request.POST:
        form_dia = DiaForm(request.POST, request.FILES)
        if form_dia.is_valid():
            nuevo_dia = form_dia.save(commit=False)
            nuevo_dia.viaje = viaje
            nuevo_dia.save()
            return redirect('detalle_viaje', viaje_id=viaje.id)
    else:
        form_dia = DiaForm()


    if 'form_actividad' in request.POST:
        form_actividad = ActividadForm(request.POST)
        if form_actividad.is_valid():
            nueva_actividad = form_actividad.save(commit=False)
            # Récupérer l'ID du jour depuis le formulaire ou la requête
            dia_id = request.POST.get('dia_id')
            nueva_actividad.dia = get_object_or_404(Dia, pk=dia_id)
            nueva_actividad.save()
            return redirect('detalle_viaje', viaje_id=viaje.id)
    else:
        form_actividad = ActividadForm()

    context = {
        'viaje': viaje,
        'dias': dias,
        'form_dia': form_dia,
        'form_actividad': form_actividad,
    }
    return render(request, 'viajes/detalle_viaje.html', context)

def agregar_companion(request, viaje_id):
  viaje = get_object_or_404(Viaje, pk=viaje_id)
  if request.method == 'POST':
    form = CompanionForm(request.POST)
    if form.is_valid():
      companion = form.save(commit=False)
      companion.viaje = viaje
      companion.save()
      return redirect('detalle_viaje', viaje_id=viaje.id)
  else:
    form = CompanionForm()
  return render(
      request, 'viajes/agregar_companion.html', {'form': form, 'viaje': viaje}
  )


def agregar_photo(request, dia_id):
  dia = get_object_or_404(Dia, pk=dia_id)
  if request.method == 'POST':
    form = PhotoForm(request.POST, request.FILES)
    if form.is_valid():
      photo = form.save(commit=False)
      photo.dia = dia
      photo.save()
      return redirect('detalle_viaje', viaje_id=dia.viaje.id)
  else:
    form = PhotoForm()
  return render(
      request, 'viajes/agregar_photo.html', {'form': form, 'dia': dia}
  )