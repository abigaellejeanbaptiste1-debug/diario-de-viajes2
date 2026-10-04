from django.urls import path
from . import views

urlpatterns = [
    path('cuenta/ingresar/', views.ViajesLoginView.as_view(), name='login'),
    path('cuenta/salir/', views.cerrar_sesion, name='logout'),
    path('', views.lista_viajes, name='lista_viajes'),
    path('viaje/<int:viaje_id>/', views.detalle_viaje, name='detalle_viaje'),
    path('viaje/<int:viaje_id>/editar/', views.editar_viaje, name='editar_viaje'),
    path('viaje/<int:viaje_id>/actividades/nueva/', views.agregar_actividad, name='agregar_actividad'),
    path('viaje/<int:viaje_id>/actividades/<int:actividad_id>/editar/', views.editar_actividad, name='editar_actividad'),
    path('viaje/<int:viaje_id>/actividades/<int:actividad_id>/eliminar/', views.eliminar_actividad, name='eliminar_actividad'),
    path('viaje/<int:viaje_id>/fotos/nueva/', views.agregar_foto_viaje, name='agregar_foto_viaje'),
    path('viaje/<int:viaje_id>/fotos/<int:foto_id>/editar/', views.editar_foto_viaje, name='editar_foto_viaje'),
    path('viaje/<int:viaje_id>/fotos/<int:foto_id>/eliminar/', views.eliminar_foto_viaje, name='eliminar_foto_viaje'),
    path('viaje/<int:viaje_id>/fotos/descargar/', views.descargar_fotos_viaje, name='descargar_fotos_viaje'),
    path('viaje/<int:viaje_id>/eliminar/', views.eliminar_viaje, name='eliminar_viaje'),

    # Ruta para agregar un acompañante a un viaje específico
    path(
        'viaje/<int:viaje_id>/companion/nuevo/',
        views.agregar_companion,
        name='agregar_companion',
    ),
]


   