from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from .money import format_clp


class Viaje(models.Model):
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField()
    pais = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    presupuesto = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
    )
    publico = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.titulo} - {self.ciudad}, {self.pais}"

    @property
    def presupuesto_gastado(self):
        total = self.gastos.aggregate(models.Sum("monto"))["monto__sum"]
        return total if total is not None else Decimal("0.00")

    @property
    def presupuesto_formateado(self):
        return format_clp(self.presupuesto)


class Dia(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name="dias")
    numero_dia = models.IntegerField()
    fecha = models.DateField()
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    ubicacion_gps = models.CharField(max_length=100, blank=True, null=True)
    foto_principal = models.ImageField(upload_to="dias/", blank=True, null=True)

    def __str__(self):
        return f"Día {self.numero_dia}: {self.titulo}"


class Actividad(models.Model):
    dia = models.ForeignKey(Dia, on_delete=models.CASCADE, related_name="actividades")
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    hora = models.TimeField()
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    costo = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
    )
    rating = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    @property
    def costo_formateado(self):
        return format_clp(self.costo)


class Gasto(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name="gastos")
    categoria = models.CharField(max_length=100)
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )
    fecha = models.DateField()
    concepto = models.CharField(max_length=200)
    moneda = models.CharField(
        max_length=10,
        default="CLP",
        choices=[("CLP", "Peso chileno (CLP)")],
    )

    def __str__(self):
        return f"{self.concepto} - {format_clp(self.monto)} CLP"

    @property
    def monto_formateado(self):
        return format_clp(self.monto)


class Companion(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name="companions")
    nombre = models.CharField(max_length=100)
    relacion = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return f"{self.nombre} ({self.relacion})"


class Photo(models.Model):
    dia = models.ForeignKey(Dia, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to="viajes/fotos/")
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto de {self.dia.viaje.titulo} - Día {self.dia.numero_dia}"
