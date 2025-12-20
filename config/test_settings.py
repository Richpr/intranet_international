from .settings import *
import os

TEMPLATES[0]['DIRS'] = [
    os.path.join(BASE_DIR, 'core', 'templates'),
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
