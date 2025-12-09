# راهنمای استقرار (Deployment Guide)

این راهنما مراحل استقرار سامانه مدیریت خدمت سربازان در محیط تولید را شرح می‌دهد.

## پیش‌نیازها

- سرور لینوکس با دسترسی root یا sudo
- Docker و Docker Compose نصب شده
- PostgreSQL (در صورت عدم استفاده از Docker)
- دامنه یا IP عمومی (برای دسترسی از اینترنت)

## مراحل استقرار

### 1. آماده‌سازی سرور

```bash
# به‌روزرسانی سیستم
sudo apt update && sudo apt upgrade -y

# نصب Docker و Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# نصب Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. کلون کردن پروژه

```bash
cd /opt
git clone <repository-url> soldier-management
cd soldier-management
```

### 3. تنظیم متغیرهای محیطی

```bash
# ایجاد فایل .env
cp .env.example .env
nano .env
```

مقادیر مهم برای تولید:

```env
SECRET_KEY=<generate-a-secure-secret-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
POSTGRES_PASSWORD=<strong-password>
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

**تولید SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. تنظیم Docker Compose برای تولید

ایجاد فایل `docker-compose.prod.yml`:

```yaml
version: '3.9'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: .
    command: gunicorn soldier_management.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      db:
        condition: service_healthy
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/var/www/static
      - media_volume:/var/www/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### 5. تنظیم Nginx

ایجاد فایل `nginx.conf`:

```nginx
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/static/;
    }

    location /media/ {
        alias /var/www/media/;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. راه‌اندازی اولیه

```bash
# ساخت و اجرای کانتینرها
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# اجرای migrations
docker-compose exec web python manage.py migrate

# ایجاد کاربر ادمین
docker-compose exec web python manage.py createsuperuser

# جمع‌آوری فایل‌های استاتیک
docker-compose exec web python manage.py collectstatic --noinput
```

### 7. تنظیم SSL (Let's Encrypt)

```bash
# نصب Certbot
sudo apt install certbot python3-certbot-nginx

# دریافت گواهینامه
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## پشتیبان‌گیری (Backup)

### پشتیبان‌گیری دستی

```bash
# پشتیبان‌گیری از پایگاه داده
docker-compose exec db pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup_$(date +%Y%m%d_%H%M%S).sql

# بازگردانی
docker-compose exec -T db psql -U ${POSTGRES_USER} ${POSTGRES_DB} < backup_file.sql
```

### پشتیبان‌گیری خودکار

ایجاد اسکریپت `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker-compose exec -T db pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# حذف پشتیبان‌های قدیمی‌تر از 30 روز
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

اضافه کردن به crontab:

```bash
# پشتیبان‌گیری روزانه در ساعت 2 صبح
0 2 * * * /opt/soldier-management/backup.sh
```

## به‌روزرسانی

```bash
# دریافت آخرین تغییرات
git pull origin main

# بازسازی کانتینرها
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# اجرای migrations جدید
docker-compose exec web python manage.py migrate

# جمع‌آوری فایل‌های استاتیک جدید
docker-compose exec web python manage.py collectstatic --noinput

# راه‌اندازی مجدد
docker-compose restart web
```

## مانیتورینگ

### بررسی لاگ‌ها

```bash
# لاگ‌های وب
docker-compose logs -f web

# لاگ‌های پایگاه داده
docker-compose logs -f db

# لاگ‌های Nginx
docker-compose logs -f nginx
```

### بررسی وضعیت کانتینرها

```bash
docker-compose ps
docker stats
```

## عیب‌یابی

### مشکل اتصال به پایگاه داده

```bash
# بررسی وضعیت پایگاه داده
docker-compose exec db pg_isready -U ${POSTGRES_USER}

# اتصال به پایگاه داده
docker-compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

### مشکل فایل‌های استاتیک

```bash
# جمع‌آوری مجدد فایل‌های استاتیک
docker-compose exec web python manage.py collectstatic --noinput --clear
```

### مشکل permissions

```bash
# تنظیم مجوزهای صحیح
sudo chown -R www-data:www-data /opt/soldier-management/staticfiles
sudo chmod -R 755 /opt/soldier-management/staticfiles
```

## امنیت

1. **فایروال**: فقط پورت‌های 80 و 443 را باز کنید
2. **SSL**: همیشه از HTTPS استفاده کنید
3. **رمزهای عبور**: از رمزهای قوی استفاده کنید
4. **به‌روزرسانی**: سیستم و Docker را به‌روز نگه دارید
5. **پشتیبان‌گیری**: پشتیبان‌گیری منظم انجام دهید

## نکات مهم

- هرگز `DEBUG=True` را در تولید تنظیم نکنید
- `SECRET_KEY` را محرمانه نگه دارید
- از رمزهای قوی برای پایگاه داده استفاده کنید
- پشتیبان‌گیری منظم انجام دهید
- لاگ‌ها را به صورت منظم بررسی کنید

