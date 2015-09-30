import os, sys
CURRENT_DIR = os.path.dirname(__file__)
sys.path.append(CURRENT_DIR)

os.environ['PYTHON_EGG_CACHE'] = '/tmp/python-egg'
os.environ['DJANGO_SETTINGS_MODULE'] = 'tomato.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
