from django.contrib import admin
from .models import Actividad, Dia, Viaje, Photo, Companion


admin.site.register(Viaje)
admin.site.register(Dia)
admin.site.register(Actividad)
admin.site.register(Photo)
admin.site.register(Companion)