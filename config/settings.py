"""
configuración del proyecto INICNE.

esta configuración sirve para DOS entornos con el mismo código:
- en local (desarrollo): DEBUG=True en el archivo .env
- en Render (producción): DEBUG=False y las claves vienen de variables de entorno

los secretos (SECRET_KEY, contraseñas) se leen del entorno con python-decouple
no se suben a GitHub
"""

from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Seguridad básica -------------------------------------------------------

# la clave secreta firma las sesiones y los tokens
# se lee del entorno y no se escribe en el código
SECRET_KEY = config("SECRET_KEY")

# DEBUG por defecto es False para que el sitio sea seguro
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

# nombre del sitio que me da Render para producción
RENDER_EXTERNAL_HOSTNAME = config("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS = [f"https://{RENDER_EXTERNAL_HOSTNAME}"]

# --- Aplicaciones -----------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # librería para construir la API que consume React
    "rest_framework",
    # una app propia por cada área del sistema
    "personal",
    "equipamiento",
    "tareas",
    "acuicultura",
    "tablero",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise entrega los archivos estáticos (CSS, JS de React) desde la
    # propia aplicación, sin necesitar un servidor aparte. Tiene que ir
    # justo después de SecurityMiddleware.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # carpeta templates/ de la raíz: base.html, login, página 403, etc.
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Base de datos ----------------------------------------------------------

# Si existe la variable DATABASE_URL (en Render) usa PostgreSQL; si no, usa
# SQLite local. Así el mismo código funciona en mi PC y en producción.
# conn_max_age mantiene la conexión abierta unos minutos en lugar de abrir
# una nueva en cada pedido, que es más lento.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Idioma y hora ----------------------------------------------------------

LANGUAGE_CODE = "es-ar"
# Corrientes usa la zona horaria de Córdoba
TIME_ZONE = "America/Argentina/Cordoba"
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos -----------------------------------------------------

STATIC_URL = "static/"
# carpeta donde "collectstatic" junta todos los archivos estáticos del
# proyecto para entregarlos. No se sube a GitHub: se genera en cada despliegue.
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
if not DEBUG:
    # En producción, WhiteNoise comprime los archivos y les agrega un código
    # en el nombre (tablero.3f9a2b.js). Así, cuando cambia React, el navegador
    # descarga la versión nueva en lugar de usar una vieja guardada.
    STORAGES["staticfiles"][
        "BACKEND"
    ] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Login ------------------------------------------------------------------

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "inicio"
LOGOUT_REDIRECT_URL = "inicio"

# --- Seguridad en producción ------------------------------------------------
# solo se activa con DEBUG=False: en local trabajo con http y no con https.
if not DEBUG:
    # Render recibe el pedido por HTTPS y se lo pasa a mi app por HTTP.
    # Este encabezado le avisa a Django que el pedido original era seguro.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Redirige todo pedido http:// a https://
    SECURE_SSL_REDIRECT = True
    # Las cookies de sesión y CSRF solo viajan por HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Le pide al navegador que use siempre HTTPS con este sitio.
    # Empiezo con una hora: si algo saliera mal, el efecto dura poco.
    # Se puede subir a un año.
    SECURE_HSTS_SECONDS = 3600

    # NO activo CSRF_COOKIE_HTTPONLY. React necesita leer la cookie del
    # token CSRF con JavaScript para poder hacer POST a la API.
