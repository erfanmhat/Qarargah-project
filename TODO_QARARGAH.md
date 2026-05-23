# TODO: سیستم مدیریت نگهبانی قرارگاه

## معماری کلی
- پروژه Django مستقل (جدا از سیستم نیروی انسانی)
- تک‌کاربره، آفلاین
- رابط کاربری فارسی RTL ساده
- یک اپ واحد: `core`

---

## ساختار اپ `core`

### مدل‌ها (`core/models.py`)
```python
# مدل پایه
- TimeStampedModel (created_at, updated_at)

# مدل‌های اصلی
- Soldier (نام، نام خانوادگی، کد ملی، تاریخ ورود، نقش، وضعیت فعال)
- SoldierRole (نام نقش، اولویت)
- Leave (سرباز، تاریخ شروع، تاریخ پایان، نوع، توضیحات)
- ShiftConfig (نام شیفت، ساعت شروع، ساعت پایان، ترتیب)
- PostType (نام پست، تعداد نفرات مورد نیاز، نقش‌های مجاز)
- DailySchedule (تاریخ، شیفت، نهایی شده، تاریخ نهایی‌سازی)
- PostAssignment (برنامه روزانه، پست، سرباز، امتیاز محاسبه شده)

**نکته مهم:** جدول `GuardScore` وجود ندارد. امتیازدهی از `PostAssignment` کوئری می‌شود.

### سرویس‌ها (`core/services.py`)
python
def get_guard_score(soldier, reference_date):
"""
محاسبه امتیاز نگهبانی سرباز تا تاریخ مرجع
- تعداد نگهبانی‌های گذشته از PostAssignment
- فاصله از آخرین نگهبانی
- نقش سرباز
"""
pass  # TODO: پیاده‌سازی

def suggest_soldiers_for_post(post_type, shift, date, count):
"""
پیشنهاد سربازان مناسب برای یک پست
- فیلتر بر اساس نقش مجاز
- حذف سربازان در مرخصی یا وضعیت موقت
- مرتب‌سازی بر اساس امتیاز نگهبانی
"""
pass  # TODO: پیاده‌سازی

### ویوها (`core/views.py`)
تمام ویوهای مربوط به:
- مدیریت سربازان (CRUD)
- مدیریت مرخصی‌ها
- تولید و مدیریت برنامه نگهبانی
- گزارش‌ها
- تنظیمات

### فرم‌ها (`core/forms.py`)
- SoldierForm
- LeaveForm
- ShiftConfigForm
- PostTypeForm
- DailyScheduleForm
- PostAssignmentForm

### URL ها (`core/urls.py`)
python
# مدیریت سربازان
GET  /soldiers/                    # لیست سربازان
GET  /soldiers/add/                # افزودن سرباز
POST /soldiers/add/
GET  /soldiers/<id>/               # جزئیات سرباز
GET  /soldiers/<id>/edit/          # ویرایش سرباز
POST /soldiers/<id>/edit/
POST /soldiers/<id>/delete/        # حذف سرباز

# مدیریت مرخصی‌ها
GET  /leaves/add/<soldier_id>/     # افزودن مرخصی
POST /leaves/add/<soldier_id>/
GET  /leaves/                      # لیست مرخصی‌ها
GET  /leaves/history/              # تاریخچه مرخصی‌ها
POST /leaves/<id>/delete/          # حذف مرخصی

# مدیریت برنامه نگهبانی
GET  /schedule/                    # تقویم برنامه‌ها
GET  /schedule/<date>/             # برنامه روز خاص
POST /schedule/<date>/generate/    # تولید برنامه خودکار
POST /schedule/<date>/assign/      # تخصیص دستی
POST /schedule/<date>/finalize/    # نهایی‌سازی برنامه
GET  /schedule/<date>/print/       # نمایش قابل چاپ
GET  /schedule/<date>/export/docx/ # خروجی DOCX

# تنظیمات
GET  /settings/shifts/             # مدیریت شیفت‌ها
POST /settings/shifts/add/
POST /settings/shifts/<id>/edit/
POST /settings/shifts/<id>/delete/

GET  /settings/posts/              # مدیریت انواع پست
POST /settings/posts/add/
POST /settings/posts/<id>/edit/
POST /settings/posts/<id>/delete/

GET  /settings/roles/              # مدیریت نقش‌ها
POST /settings/roles/add/
POST /settings/roles/<id>/edit/
POST /settings/roles/<id>/delete/

# گزارش‌ها
GET  /reports/daily/               # گزارش روزانه
GET  /reports/guard-history/<soldier_id>/  # تاریخچه نگهبانی سرباز
GET  /reports/leaves/              # آمار مرخصی‌ها

### تمپلیت‌ها (`templates/core/`)

templates/
├── base.html                      # قالب پایه با منوی کناری
└── core/
├── soldiers/
│   ├── list.html
│   ├── add.html
│   ├── edit.html
│   └── detail.html
├── leaves/
│   ├── list.html
│   ├── add.html
│   └── history.html
├── schedule/
│   ├── calendar.html
│   ├── daily.html
│   ├── generate.html
│   └── print.html
├── reports/
│   ├── daily.html
│   ├── guard_history.html
│   └── leaves_stats.html
└── settings/
├── shifts.html
├── posts.html
└── roles.html

### Admin (`core/admin.py`)
ثبت تمام مدل‌ها در پنل ادمین Django

---

## ساختار پروژه نهایی


qarargah/
├── manage.py
├
ادامه ساختار نهایی پروژه:

qarargah/

├── manage.py

├── qarargah/

│ ├── init.py

│ ├── settings.py

│ ├── urls.py # include(“core.urls”)

│ └── wsgi.py

│

├── core/

│ ├── init.py

│ ├── admin.py

│ ├── apps.py

│ ├── models.py

│ ├── forms.py

│ ├── views.py

│ ├── services.py

│ ├── urls.py

│ ├── migrations/

│ └── templates/

│ └── core/ # ساختار تمپلیت‌ها طبق بخش قبل

│

├── templates/

│ └── base.html

│

├── media/

│

├── static/

│

├── requirements.txt

└── TODO_QARARGAH.md

الزامات رابط کاربری
RTL کامل (dir="rtl")
فونت فارسی مناسب
منوی کناری شامل:
سربازان
مرخصی‌ها
برنامه نگهبانی
گزارش‌ها
تنظیمات
خروجی DOCX
در core/services.py یا ماژول جداگانه export:

ورودی تمپلیت:

date
shifts
assignments
generated_at