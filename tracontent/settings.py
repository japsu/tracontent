import os

import django.conf.global_settings as defaults


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def mkpath(*parts):
    return os.path.abspath(os.path.join(BASE_DIR, *parts))

SECRET_KEY = '9()(lzm)jdr$szjfdx8^^#j_6efj@d&$9pb6l2h&=udxom3(bn'

DEBUG = True

ALLOWED_HOSTS = ['ssoexample.tracon.fi']

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'ckeditor',
    'ckeditor_uploader',
    'crispy_forms',
    'reversion',

    'kompassi_oauth2',
    'content',
    'ads',
    'resources',
    'users',

    'site_specific.traconx',
    'site_specific.tracon11',
    'site_specific.aicon',
    'site_specific.hitpoint2015',
    'site_specific.animecon2016',

    'site_specific.japsufi',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'kompassi_oauth2.backends.KompassiOAuth2AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [mkpath('tracontent','templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.request',
                'content.context_processors.content_context',
                'users.context_processors.users_context',
            ],
            'loaders': [
                # PyJade part:   ##############################
                ('pyjade.ext.django.Loader', (
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ))
            ],
            'builtins': ['pyjade.ext.django.templatetags'],
        },
    },
]

if 'ads' in INSTALLED_APPS:
    TEMPLATES[0]['OPTIONS']['context_processors'] += [
        'ads.context_processors.ads_context',
    ]

ROOT_URLCONF = 'tracontent.urls'

WSGI_APPLICATION = 'tracontent.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'tracontent.sqlite3'),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': True
        },
        'kompassi_oauth2': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': True
        },
        'resources': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': True
        }
    }
}

LANGUAGE_CODE = 'fi-fi'

TIME_ZONE = 'Europe/Helsinki'

USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = mkpath('static')

MEDIA_URL = '/media/'
MEDIA_ROOT = mkpath('media')

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_JQUERY_URL = '/static/common/js/jquery.min.js'
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': [
            ['Format', 'Bold', 'Italic', 'Underline', 'Strike', 'SpellChecker'],
            ['NumberedList', 'BulletedList', 'Indent', 'Outdent', 'JustifyLeft', 'JustifyCenter', 'JustifyRight'],
            ['Image', 'Table', 'Link', 'Unlink', 'Anchor', 'SectionLink', 'Subscript', 'Superscript'],
            ['Undo', 'Redo'],
            ['Source'],
            ['Maximize']
        ],
        'extraPlugins': 'image2',
    },
}

KOMPASSI_INSTALLATION_SLUG = 'turskadev'
KOMPASSI_HOST = 'https://kompassi.eu'
KOMPASSI_OAUTH2_AUTHORIZATION_URL = '{KOMPASSI_HOST}/oauth2/authorize'.format(**locals())
KOMPASSI_OAUTH2_TOKEN_URL = '{KOMPASSI_HOST}/oauth2/token'.format(**locals())
KOMPASSI_OAUTH2_CLIENT_ID = 'kompassi_insecure_test_client_id'
KOMPASSI_OAUTH2_CLIENT_SECRET = 'kompassi_insecure_test_client_secret'
KOMPASSI_OAUTH2_SCOPE = ['read']
KOMPASSI_API_V2_USER_INFO_URL = '{KOMPASSI_HOST}/api/v2/people/me'.format(**locals())
KOMPASSI_API_V2_EVENT_INFO_URL_TEMPLATE = '{kompassi_host}/api/v2/events/{event_slug}'
KOMPASSI_ADMIN_GROUP = 'admins'
KOMPASSI_EDITOR_GROUP = 'tracontent-staff'
KOMPASSI_PROGRAMME_EXPIRY_SECONDS = 300

LOGIN_URL = '/oauth2/login' if 'kompassi_oauth2' in INSTALLED_APPS else '/admin/login/'
LOGOUT_URL = '/logout/'
LOGOUT_REDIRECT_URL = '{KOMPASSI_HOST}/logout'.format(**locals())

TRACONTENT_BLOG_AUTO_EXCERPT_MAX_CHARS = 300
TRACONTENT_BLOG_COMMENT_MODERATORS = []

CRISPY_TEMPLATE_PACK = 'bootstrap3'

