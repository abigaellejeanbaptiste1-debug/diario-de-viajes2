from django import forms

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
