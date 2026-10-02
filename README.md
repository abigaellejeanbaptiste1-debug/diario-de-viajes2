# Diario de Viajes

Aplicación Django para registrar viajes, organizar días y actividades, controlar
gastos en pesos chilenos y administrar los datos desde Django Admin.

En el detalle de cada viaje, el itinerario y el control de gastos están
integrados: puedes registrar gastos reales dentro del día correspondiente y
compararlos con los costos estimados de las actividades. Los gastos existentes
sin un día asociado siguen visibles y pueden asociarse a uno.

## Requisitos

- Python 3.14 o una versión compatible con Django indicada en `requirements.txt`.
- pip.

## Instalación y ejecución

Desde la carpeta del proyecto, en Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/` para consultar los viajes y
`http://127.0.0.1:8000/admin/` para administrar el sitio.

Para producción, configura `DJANGO_DEBUG=false`, `DJANGO_SECRET_KEY` con una
clave aleatoria privada y `DJANGO_ALLOWED_HOSTS` con los dominios autorizados.
Con `DJANGO_DEBUG=false` la aplicación requiere la clave y activa redirección
HTTPS y cookies seguras.

## Acceso y permisos

La lectura del listado y del detalle es pública. Para crear, editar o eliminar
viajes, y para agregar días, actividades o gastos, inicia sesión con una cuenta
que tenga el permiso Django correspondiente. `createsuperuser` crea una cuenta
con acceso completo. Las operaciones de escritura usan POST, CSRF y formularios
con validación del servidor.

## Migraciones y pruebas

Después de actualizar el proyecto, aplica las migraciones:

```powershell
python manage.py migrate
```

Ejecuta las pruebas y verificaciones:

```powershell
python manage.py test viajes
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Git y publicación

El repositorio incluye `.gitignore` para entornos virtuales, cachés de Python,
base de datos local y variables de entorno. Para publicar el proyecto, agrega un
remoto GitHub, revisa los cambios antes de cada commit y no subas claves,
contraseñas ni la base de datos local.
