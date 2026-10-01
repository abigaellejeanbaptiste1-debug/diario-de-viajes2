from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_viajes, name='lista_viajes'),
    path('viaje/<int:viaje_id>/', views.detalle_viaje, name='detalle_viaje'),
]