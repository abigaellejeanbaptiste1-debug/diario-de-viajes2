from django.contrib import admin

from .forms import ViajeForm
from .money import format_clp
from .models import Actividad, Companion, Dia, Gasto, Photo, Viaje


@admin.register(Viaje)
class ViajeAdmin(admin.ModelAdmin):
    form = ViajeForm
    list_display = ("titulo", "ciudad", "pais", "fecha_inicio", "presupuesto", "publico")
    search_fields = ("titulo", "ciudad", "pais")
    list_filter = ("pais", "publico", "fecha_inicio")


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ("concepto", "viaje", "categoria", "monto_formato", "fecha")
    search_fields = ("concepto", "categoria")
    list_filter = ("categoria", "fecha")

    @admin.display(description="Monto (CLP)")
    def monto_formato(self, obj):
        return f"{format_clp(obj.monto)} {obj.moneda}"


admin.site.register(Dia)
admin.site.register(Actividad)
admin.site.register(Companion)
admin.site.register(Photo)
