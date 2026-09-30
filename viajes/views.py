from django.shortcuts import render, redirect
from .models import Viaje
from .forms import ViajeForm

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
