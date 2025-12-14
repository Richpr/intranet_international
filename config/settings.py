from pathlib import Path
import os
import environ

# Initialize django-environ
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# The SECRET_KEY is now read from an environment variable
SECRET_KEY = env('SECRET_KEY')  #

# SECURITY WARNING: don't run with debug turned on in production!
# The DEBUG setting is now read from an environment variable, defaulting to False
DEBUG = env('DEBUG')  #

# ALLOWED_HOSTS is now read from an environment variable
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')  #


CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS')  #


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",  #
    "django.contrib.auth",  #
    "django.contrib.contenttypes",  #
    "django.contrib.sessions",  #
    "django.contrib.messages",  #
    "django.contrib.staticfiles",  #
    "users.apps.UsersConfig",  #
    "projects.apps.ProjectsConfig",  #
    "core.apps.CoreConfig",  #
    "finance.apps.FinanceConfig",  #
    "crispy_forms",  #
    "crispy_bootstrap5",  #
    "django.contrib.humanize",  #
    "reporting.apps.ReportingConfig",  #
    "inventaire.apps.InventaireConfig",  #
    "logistique.apps.LogistiqueConfig",  #
    "rh.apps.RhConfig",  #
    "data_analytics.apps.DataAnalyticsConfig",  #
    "workflow.apps.WorkflowConfig",  #
    "documentation.apps.DocumentationConfig",  #
    "phonenumber_field",  #
    "django_countries",  #
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",  #
    "whitenoise.middleware.WhiteNoiseMiddleware",  #
    "django.contrib.sessions.middleware.SessionMiddleware",  #
    "django.middleware.common.CommonMiddleware",  #
    "django.middleware.csrf.CsrfViewMiddleware",  #
    "django.contrib.auth.middleware.AuthenticationMiddleware",  #
    "django.contrib.messages.middleware.MessageMiddleware",  #
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  #
]

ROOT_URLCONF = "config.urls"  #

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # 🟢 CORRECTION APPLIQUÉE ICI : Ajout de "core" à la fin du chemin
        "DIRS": [BASE_DIR / "templates", BASE_DIR / "core" / "templates" / "core"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.roles_and_permissions",
                "core.context_processors.user_countries_processor",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"  #


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# Database configuration is now read from the DATABASE_URL environment variable
DATABASES = {
    'default': env.db(),  #
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  #
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",  #
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",  #
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",  #
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"  #

TIME_ZONE = "UTC"  #

USE_I18N = True  #

USE_TZ = True  #

# Configuration pour phonenumber_field - PAS DE RÉGION PAR DÉFAUT
PHONENUMBER_DEFAULT_REGION = None  # Aucune région par défaut  #
PHONENUMBER_DB_FORMAT = "E164"  #

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"  #
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  #
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  #

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"  #
AUTH_USER_MODEL = "users.CustomUser"  #
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"  #
CRISPY_TEMPLATE_PACK = "bootstrap5"  #

# Configuration des Fichiers Médias
MEDIA_URL = "/media/"  #
MEDIA_ROOT = os.path.join(BASE_DIR, "media")  #
TEMP_MEDIA_ROOT = os.path.join(BASE_DIR, "temp_media")  #

# Configuration WhiteNoise pour les fichiers statiques
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  #

# Assure que les dossiers existent (utile pour le développement)
os.makedirs(MEDIA_ROOT, exist_ok=True)  #
os.makedirs(TEMP_MEDIA_ROOT, exist_ok=True)  #