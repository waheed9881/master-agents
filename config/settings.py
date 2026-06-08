"""
Django settings for AI Agent OS.
Environment-based configuration using django-environ.
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    AI_PROVIDER=(str, "mock"),
    AI_MODEL_NAME=(str, ""),
    AI_MAX_TOKENS=(int, 800),
    AI_TEMPERATURE=(float, 0.3),
    AI_FALLBACK_PROVIDER=(str, "mock"),
    AI_DAILY_TOKEN_BUDGET=(str, ""),
    AI_MONTHLY_TOKEN_BUDGET=(str, ""),
    INTEGRATIONS_MOCK_MODE=(bool, True),
)

environ.Env.read_env(BASE_DIR / ".env")

# SECRET_KEY: use SECRET_KEY or DJANGO_SECRET_KEY (CI/deploy tools)
SECRET_KEY = env("SECRET_KEY", default=None) or env(
    "DJANGO_SECRET_KEY", default="dev-insecure-key-change-in-production"
)
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "django_celery_beat",
    "channels",
    # Core apps
    "apps.accounts",
    "apps.tenants",
    "apps.agents",
    "apps.crm",
    "apps.inbox",
    "apps.integrations",
    "apps.knowledge",
    "apps.agent_engine",
    "apps.analytics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.TenantMiddleware",
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
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.accounts.context_processors.tenant_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

def _database_config():
    """Support DATABASE_URL or individual DB_* environment variables."""
    if env.str("DATABASE_URL", default=""):
        return env.db("DATABASE_URL")
    if env.str("DB_NAME", default=""):
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER", default="aiagent"),
            "PASSWORD": env("DB_PASSWORD", default="aiagent"),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default="5432"),
        }
    return env.db(
        "DATABASE_URL",
        default="postgres://aiagent:aiagent@localhost:5432/ai_agent_os",
    )


DATABASES = {"default": _database_config()}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:index"
LOGOUT_REDIRECT_URL = "accounts:login"

# Redis
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    },
}

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

# AI Provider
AI_PROVIDER = env("AI_PROVIDER")
AI_MODEL_NAME = env("AI_MODEL_NAME", default="")
AI_MAX_TOKENS = env("AI_MAX_TOKENS")
AI_TEMPERATURE = env("AI_TEMPERATURE")
AI_FALLBACK_PROVIDER = env("AI_FALLBACK_PROVIDER")
AI_DAILY_TOKEN_BUDGET = env("AI_DAILY_TOKEN_BUDGET", default="")
AI_MONTHLY_TOKEN_BUDGET = env("AI_MONTHLY_TOKEN_BUDGET", default="")
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
GROQ_API_KEY = env("GROQ_API_KEY", default="")
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")

# Credentials encryption
CREDENTIALS_ENCRYPTION_KEY = env("CREDENTIALS_ENCRYPTION_KEY", default="")

# Meta / WhatsApp / Instagram integrations
META_VERIFY_TOKEN = env("META_VERIFY_TOKEN", default="ai-agent-os-verify")
META_APP_SECRET = env("META_APP_SECRET", default="")
META_ACCESS_TOKEN = env("META_ACCESS_TOKEN", default="")
WHATSAPP_PHONE_NUMBER_ID = env("WHATSAPP_PHONE_NUMBER_ID", default="")
INSTAGRAM_PAGE_ID = env("INSTAGRAM_PAGE_ID", default="")
INTEGRATIONS_MOCK_MODE = env("INTEGRATIONS_MOCK_MODE")

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    # Production/staging hardening (override via env if needed)
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
    SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
    CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
