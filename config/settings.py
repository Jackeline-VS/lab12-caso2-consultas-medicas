"""Configuración base - Caso 2: Consultas Médicas (Semana 12, Desarrollo de Aplicaciones Web)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "clave-solo-para-laboratorio-cambiar-en-produccion"
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "consultas",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "consultas.middleware.AuditoriaMedicaMiddleware",
    "consultas.middleware.HorarioAtencionMiddleware",
    "consultas.middleware.AlertasMedicoMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "consultas.context.perfiles",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

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
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Autenticación, sesiones y seguridad  (dev/integrante-2)
# ---------------------------------------------------------------------------
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "inicio"
LOGOUT_REDIRECT_URL = "login"

# Contraseñas hasheadas con PBKDF2 (hasher por defecto de Django).
# Timeout por inactividad: 20 minutos. SAVE_EVERY_REQUEST renueva la
# caducidad en cada petición, de modo que solo expira si NO hay actividad.
SESSION_COOKIE_AGE = 1200  # 20 min * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Cookies seguras
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Logging de auditoría: consola (para la captura) + archivo logs/auditoria.log
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "auditoria": {
            "format": "[{asctime}] {levelname} {name} | {message}",
            "style": "{",
        },
    },
    "handlers": {
        "consola": {"class": "logging.StreamHandler", "formatter": "auditoria"},
        "archivo": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "auditoria.log",
            "encoding": "utf-8",
            "formatter": "auditoria",
        },
    },
    "loggers": {
        "auditoria": {
            "handlers": ["consola", "archivo"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
