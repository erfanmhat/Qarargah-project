import os
from waitress import serve

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "soldier_management.settings")
from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000, threads=8)
