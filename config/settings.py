"""
Configuracion de Django para el CRM de GAVI PERU.
Ver el DAS completo en Drive (carpeta 04. Arquitectura) para el detalle
de cada decision reflejada aqui.
"""

from pathlib import Path
import sys
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
# Lee variables desde .env en local. En produccion (EC2) se configuran
# como variables de entorno reales, nunca hardcodeadas -- ver DAS seccion 8.
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Integracion opcional con Twilio. Sin estas credenciales el CRM conserva el
# modo local actual, util mientras GAVI termina de habilitar sus cuentas.
TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID", default="")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN", default="")
TWILIO_WEBHOOK_BASE_URL = env("TWILIO_WEBHOOK_BASE_URL", default="").rstrip("/")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps del CRM -- una por dominio, segun el DAS (monolito modular)
    "usuarios",
    "clientes",
    "cotizaciones",
    "whatsapp",
    "oportunidades",
    "tareas",
]

AUTH_USER_MODEL = "usuarios.Usuario"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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


# Base de datos -- PostgreSQL via DATABASE_URL (ver DAS seccion 3.3).
# Cae a sqlite si no hay DATABASE_URL, solo para poder correr el proyecto
# sin Postgres instalado en una maquina nueva -- no usar sqlite en producción.
_database_url = env("DATABASE_URL", default="") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
DATABASES = {"default": env.db_url_config(_database_url)}

# Cache / sesiones -- Redis (ver DAS seccion 3.4). Redis es cache, no
# fuente de verdad: si se cae, el sistema debe seguir funcionando mas lento,
# nunca roto -- por eso IGNORE_EXCEPTIONS esta en True.
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    }
}

# En desarrollo local y pruebas no dependemos de Redis. Mantener las pruebas
# autocontenidas evita que fallen solo porque no hay un servicio externo activo.
if DEBUG or "test" in sys.argv:
    SESSION_ENGINE = "django.contrib.sessions.backends.db"
else:
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login/logout redirects.
# La redirección real por rol la maneja usuarios/views.py (RedireccionPorRolView).
# Esta URL es el fallback de Django si algo falla antes de llegar a esa vista.
LOGIN_REDIRECT_URL = "/usuarios/redirigir/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# Solo aplica cuando DEBUG=False (produccion) -- HTTPS/TLS obligatorio,
# ver DAS seccion 4 (cumplimiento Ley 29733).
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
