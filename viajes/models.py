from django.db import models

class Viaje(models.Model):
    destino = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    presupuesto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.destino} ({self.fecha_inicio})"

class DiaViaje(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='dias')
    numero_dia = models.IntegerField(verbose_name="Número de día (ej: 1, 2, 3)")
    fecha = models.DateField()
    resumen = models.TextField(blank=True, null=True, verbose_name="Resumen del día")

    def __str__(self):
        return f"Día {self.numero_dia} - {self.viaje.destino}"


class Actividad(models.Model):
    dia = models.ForeignKey(DiaViaje, on_delete=models.CASCADE, related_name='actividades')
    titulo = models.CharField(max_length=150, verbose_name="Nombre de la actividad")
    hora = models.TimeField(blank=True, null=True)
    lugar = models.CharField(max_length=200, blank=True, null=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.titulo} ({self.lugar})"