from .base import *
from dotenv import load_dotenv

load_dotenv('.env')

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = os.environ["DEBUG"]

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost,http://127.0.0.1").split(",")

# INSTALLED_APPS += ["debug_toolbar"]

# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"], 
        "HOST": "localhost",
        "PORT": "5433",
    }
}

