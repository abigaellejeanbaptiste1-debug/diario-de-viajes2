from django.db import models

class Viaje(models.Model):
    destino = models.CharField(max_length=100)
    fecha_fin = models.DateField()

    def __str__(self):
        return f"{self.destino} - Termina: {self.fecha_fin}"


class Companion(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='companions')
    nombre = models.CharField(max_length=100)
    relacion = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return f"{self.nombre} ({self.relacion}) - {self.viaje.destino}"


class Photo(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='viajes/fotos/')
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto de {self.viaje.destino} - {self.descripcion[:20] if self.descripcion else 'Sin título'}"
