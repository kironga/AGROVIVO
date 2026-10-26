import os
from pathlib import Path
import dj_database_url
BASE_DIR = Path(__file__).resolve().parent.parent
file_env = {}
if (BASE_DIR / ".env").exists():
    for line in (BASE_DIR / ".env").read_text().splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "=" in line:
            key,value=line.split("=",1); file_env[key.strip()]=value.strip().strip("\"'")
def setting(name, default=None): return os.getenv(name, file_env.get(name, default))
SECRET_KEY = setting("SECRET_KEY", "unsafe-development-key-change-before-deploy")
debug_setting = str(setting("DEBUG", "True")).strip().lower()
if debug_setting not in {"true", "false", "1", "0", "yes", "no", "on", "off"}:
    debug_setting = str(file_env.get("DEBUG", "True")).strip().lower()
DEBUG = debug_setting in {"true", "1", "yes", "on"}
ALLOWED_HOSTS = [x.strip() for x in setting("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")]
for platform_host in (setting("RENDER_EXTERNAL_HOSTNAME", ""), setting("VERCEL_URL", ""), setting("VERCEL_PROJECT_PRODUCTION_URL", "")):
    platform_host = platform_host.strip().removeprefix("https://").removeprefix("http://")
    if platform_host and platform_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(platform_host)
INSTALLED_APPS = ["django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles","django.contrib.sitemaps","core","catalog","cart","orders","payments","accounts"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","accounts.middleware.RoleBasedSessionTimeoutMiddleware","django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
ROOT_URLCONF = "agrofields_planet.urls"
TEMPLATES = [{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[BASE_DIR/"templates"],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages","cart.context_processors.cart_summary"]}}]
WSGI_APPLICATION = "agrofields_planet.wsgi.application"
DATABASES = {"default":dj_database_url.config(default=setting("DATABASE_URL",f"sqlite:///{BASE_DIR/'db.sqlite3'}"),conn_max_age=int(setting("CONN_MAX_AGE",0)))}
AUTH_PASSWORD_VALIDATORS = [{"NAME":"django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},{"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator"},{"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},{"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"}]
LANGUAGE_CODE = "en-ke"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR/"staticfiles"
STATICFILES_DIRS = [BASE_DIR/"static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR/"media"
SESSION_COOKIE_AGE = 20 * 60
STORAGES = {"default":{"BACKEND":"django.core.files.storage.FileSystemStorage"},"staticfiles":{"BACKEND":"django.contrib.staticfiles.storage.StaticFilesStorage" if DEBUG else "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_REDIRECT_URL = "account"
LOGOUT_REDIRECT_URL = "home"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend" if DEBUG else "anymail.backends.resend.EmailBackend"
DEFAULT_FROM_EMAIL = setting("DEFAULT_FROM_EMAIL","orders@agrofields.example")
ANYMAIL = {"RESEND_API_KEY":setting("RESEND_API_KEY","")}
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO","https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
