# سامانه مدیریت خدمت سربازان

سیستم جامع مدیریت اطلاعات سربازان و مرخصی‌های آن‌ها برای ناحیه مقاومت بسیج استان اردبیل

## ویژگی‌ها

- مدیریت کامل اطلاعات سربازان (اطلاعات هویتی، خدمت، تماس)
- مدیریت مرخصی‌ها (استعلاجی، تشویقی، استحقاقی، اضطراری)
- محاسبه خودکار تاریخ پایان خدمت با در نظر گیری کسر خدمت
- داشبورد آماری با نمودارهای تعاملی
- جستجوی پیشرفته سربازان
- سیستم مدیریت کسر خدمت
- پشتیبانی از تاریخ شمسی (جلالی)
- رابط کاربری فارسی و RTL

## پیش‌نیازها

- Python 3.12+
- PostgreSQL 15+
- Docker و Docker Compose (برای اجرای با Docker)

## نصب و راه‌اندازی

### روش 1: استفاده از Docker (توصیه می‌شود)

1. کلون کردن پروژه:
```bash
git clone <repository-url>
cd soldier-management
```

2. ایجاد فایل `.env`:
```bash
cp .env.example .env
# ویرایش فایل .env و تنظیم مقادیر مناسب
```

3. اجرای با Docker Compose:
```bash
docker-compose up -d
```

4. اجرای migrations:
```bash
docker-compose exec web python manage.py migrate
```

5. ایجاد کاربر ادمین:
```bash
docker-compose exec web python manage.py createsuperuser
```

6. جمع‌آوری فایل‌های استاتیک:
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

سیستم در آدرس `http://localhost:8000` در دسترس خواهد بود.

### روش 2: نصب محلی

1. ایجاد محیط مجازی:
```bash
python -m venv venv
source venv/bin/activate  # در Windows: venv\Scripts\activate
```

2. نصب وابستگی‌ها:
```bash
pip install -r requirements.txt
```

3. تنظیم پایگاه داده PostgreSQL و ایجاد فایل `.env`

4. اجرای migrations:
```bash
python manage.py migrate
```

5. ایجاد کاربر ادمین:
```bash
python manage.py createsuperuser
```

6. جمع‌آوری فایل‌های استاتیک:
```bash
python manage.py collectstatic
```

7. اجرای سرور توسعه:
```bash
python manage.py runserver
```

## متغیرهای محیطی

فایل `.env.example` را کپی کرده و به `.env` تغییر نام دهید، سپس مقادیر زیر را تنظیم کنید:

- `SECRET_KEY`: کلید مخفی Django (برای تولید از `django.core.management.utils.get_random_secret_key()` استفاده کنید)
- `DEBUG`: `True` برای توسعه، `False` برای تولید
- `ALLOWED_HOSTS`: لیست هاست‌های مجاز (با کاما جدا شده)
- `POSTGRES_DB`: نام پایگاه داده
- `POSTGRES_USER`: نام کاربری پایگاه داده
- `POSTGRES_PASSWORD`: رمز عبور پایگاه داده
- `POSTGRES_HOST`: آدرس هاست پایگاه داده
- `POSTGRES_PORT`: پورت پایگاه داده

## ساختار پروژه

```
soldier-management/
├── core/                    # اپلیکیشن اصلی
│   ├── models.py           # مدل‌های داده
│   ├── views.py            # ویوها
│   ├── forms.py            # فرم‌ها
│   ├── admin.py            # تنظیمات ادمین
│   ├── templates/          # قالب‌های HTML
│   └── static/             # فایل‌های استاتیک
├── soldier_management/      # تنظیمات پروژه
│   ├── settings.py         # تنظیمات Django
│   └── urls.py             # URLهای اصلی
├── docker-compose.yml      # تنظیمات Docker Compose
├── Dockerfile              # تصویر Docker
└── requirements.txt        # وابستگی‌های Python
```

## استفاده

### ورود به سیستم

1. به آدرس `/dashboard/login/` بروید
2. با نام کاربری و رمز عبور ادمین وارد شوید

### مدیریت سربازان

- مشاهده لیست سربازان: `/dashboard/soldiers/`
- افزودن سرباز جدید: از طریق لینک "افزودن سرباز جدید" یا پنل ادمین
- مشاهده جزئیات سرباز: کلیک روی آیکون چشم در لیست سربازان
- ویرایش سرباز: کلیک روی آیکون ویرایش

### مدیریت مرخصی‌ها

- مشاهده لیست مرخصی‌ها: `/dashboard/leaves/`
- ثبت مرخصی جدید: از طریق لینک "ثبت مرخصی جدید" یا پنل ادمین
- تأیید مرخصی: از طریق پنل ادمین یا لینک تأیید در لیست

### جستجوی پیشرفته

- استفاده از صفحه `/dashboard/search/` برای جستجوی پیشرفته با فیلترهای مختلف

## تست

برای اجرای تست‌ها:

```bash
python manage.py test
```

یا با Docker:

```bash
docker-compose exec web python manage.py test
```

## توسعه

### افزودن ویژگی جدید

1. ایجاد migration برای تغییرات مدل:
```bash
python manage.py makemigrations
python manage.py migrate
```

2. اجرای تست‌ها پس از تغییرات

### لاگ‌ها

لاگ‌های سیستم در پوشه `logs/soldier_management.log` ذخیره می‌شوند.

## مجوز

این پروژه برای استفاده داخلی ناحیه مقاومت بسیج استان اردبیل توسعه یافته است.

## پشتیبانی

برای گزارش باگ یا درخواست ویژگی جدید، لطفاً با تیم توسعه تماس بگیرید.

