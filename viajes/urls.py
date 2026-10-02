from django.urls import path
from . import views

urlpatterns = [
    path('cuenta/ingresar/', views.ViajesLoginView.as_view(), name='login'),
    path('cuenta/salir/', views.cerrar_sesion, name='logout'),
    path('', views.lista_viajes, name='lista_viajes'),
    path('viaje/<int:viaje_id>/', views.detalle_viaje, name='detalle_viaje'),
    path('viaje/<int:viaje_id>/editar/', views.editar_viaje, name='editar_viaje'),
    path('viaje/<int:viaje_id>/eliminar/', views.eliminar_viaje, name='eliminar_viaje'),

    # Ruta para agregar un acompañante a un viaje específico
    path(
        'viaje/<int:viaje_id>/companion/nuevo/',
        views.agregar_companion,
        name='agregar_companion',
    ),
    # Ruta para subir una foto a un día específico del itinerario
    path(
        'dia/<int:dia_id>/foto/nueva/',
        views.agregar_photo,
        name='agregar_photo',
    ),
]


   