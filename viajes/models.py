from django.db import models

class Viaje(models.Model):
    destino = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField()
    presupuesto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.destino} - Termina: {self.fecha_fin}"

class DiaViaje(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='dias')
    numero_dia = models.IntegerField()
    fecha = models.DateField()
    descripcion = models.TextField(blank=True, null=True)

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

class Companion(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='companions')
    nombre = models.CharField(max_length=100)
    relacion = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return f"{self.nombre} ({self.relacion}) - {self.viaje.destino}"

class Photo(models.Model):
    dia = models.ForeignKey(DiaViaje, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='viajes/fotos/')
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto de {self.dia.viaje.destino} - Día {self.dia.numero_dia}"

