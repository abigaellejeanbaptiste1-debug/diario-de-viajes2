from django.contrib import admin
from .models import Actividad, DiaViaje, Viaje

# Enregistre tes modèles ici :
admin.site.register(Viaje)
admin.site.register(DiaViaje)
admin.site.register(Actividad)