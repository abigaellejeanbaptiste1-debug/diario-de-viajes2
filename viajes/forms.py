from django import forms
from django.core.exceptions import ValidationError

from .models import Actividad, Companion, Dia, Gasto, Photo, Viaje


class ViajeForm(forms.ModelForm):
    class Meta:
        model = Viaje
        fields = [
            "titulo",
            "descripcion",
            "fecha_inicio",
            "fecha_fin",
            "pais",
            "ciudad",
            "presupuesto",
            "publico",
        ]
        widgets = {
            "titulo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. Expedición Torres del Paine",
                }
            ),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "pais": forms.TextInput(attrs={"class": "form-control", "placeholder": "Chile"}),
            "ciudad": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Puerto Natales"}
            ),
            "presupuesto": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Ej. 500000"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        presupuesto = cleaned_data.get("presupuesto")

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            self.add_error("fecha_fin", "La fecha de término debe ser posterior al inicio.")
        if presupuesto is not None and presupuesto < 0:
            self.add_error("presupuesto", "El presupuesto no puede ser negativo.")
        return cleaned_data


class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ["categoria", "monto", "fecha", "concepto", "moneda"]
        widgets = {
            "categoria": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej. Alojamiento, Comida"}
            ),
            "monto": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Monto en pesos chilenos (ej. 45.000)",
                    "step": "1",
                }
            ),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "concepto": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej. Hotel Patagonia"}
            ),
            "moneda": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if monto < 0:
            raise ValidationError("El monto no puede ser negativo.")
        return monto


class DiaForm(forms.ModelForm):
    class Meta:
        model = Dia
        fields = [
            "numero_dia",
            "fecha",
            "titulo",
            "descripcion",
            "ubicacion_gps",
            "foto_principal",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = [
            "nombre",
            "descripcion",
            "hora",
            "ubicacion",
            "categoria",
            "costo",
            "rating",
        ]
        widgets = {
            "hora": forms.TimeInput(attrs={"type": "time"}),
            "costo": forms.NumberInput(
                attrs={"placeholder": "Costo en pesos chilenos", "step": "1"}
            ),
        }

    def clean_costo(self):
        costo = self.cleaned_data["costo"]
        if costo < 0:
            raise ValidationError("El costo no puede ser negativo.")
        return costo


class CompanionForm(forms.ModelForm):
    class Meta:
        model = Companion
        fields = ["nombre", "relacion", "email"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre del acompañante",
                }
            ),
            "relacion": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Amigo, Familiar",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "correo@ejemplo.com",
                }
            ),
        }


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ["imagen", "descripcion"]
        widgets = {
            "imagen": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "descripcion": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Breve descripción de la foto (opcional)",
                }
            ),
        }
