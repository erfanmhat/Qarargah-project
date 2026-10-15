import os
from waitress import serve

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qarargah.settings")

import django
from django.core.management import call_command


def ensure_migrated() -> None:
    django.setup()
    call_command("migrate", interactive=False, verbosity=1)


def ensure_superuser() -> None:
    """
    Create an admin superuser once, if none exists.

    Configure credentials via environment variables:
      DJANGO_SUPERUSER_USERNAME
      DJANGO_SUPERUSER_PASSWORD
      DJANGO_SUPERUSER_EMAIL
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    # اگر حتی یک سوپر یوزر وجود دارد، کاری نکن
    if User.objects.filter(is_superuser=True).exists():
        return

    username = "root"  # os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
    password = "123321"  # os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin12345")
    email = "erfan.mh.at@gmail.com"  # os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")

    # اگر کاربر با این username هست ولی superuser نیست، از ساختن دوباره جلوگیری کن
    if User.objects.filter(username=username).exists():
        u = User.objects.get(username=username)
        if not u.is_superuser:
            u.is_staff = True
            u.is_superuser = True
            u.set_password(password)
            if hasattr(u, "email"):
                u.email = email
            u.save()
        return

    User.objects.create_superuser(username=username, password=password, email=email)


# ---- boot sequence ----
ensure_migrated()
ensure_superuser()

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()

if __name__ == "__main__":
    port = 8000
    print(f"✅ Server is running successfully with Waitress!")
    print(f"🌐 Open your browser and go to: http://127.0.0.1:{port}/")
    print(f"Press CTRL+C to stop.")
    
    serve(app, host='0.0.0.0', port=port)
