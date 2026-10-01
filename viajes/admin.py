from django.contrib import admin
from .models import Actividad, Dia, Viaje

# Enregistre tes modèles ici :
admin.site.register(Viaje)
admin.site.register(Dia)
admin.site.register(Actividad)