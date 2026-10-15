# لیست وظایف (TODO) - سیستم مدیریت نگهبانی قرارگاه

## 🟢 اولویت بالا (هفته اول و دوم) - هسته اصلی

### 1. مدل‌ها (Models) - `core/models.py`
- [x] مدل پایه `TimeStampedModel`
- [x] مدل `Soldier` (سرباز)
- [x] مدل `Leave` (مرخصی)
- [x] مدل `ShiftConfig` (تنظیمات شیفت)
- [x] مدل `PostType` (نوع پست)
- [x] مدل `DailySchedule` (برنامه روزانه)
- [x] مدل `PostAssignment` (تخصیص پست)
*(وضعیت: فایل `core/models.py` ایجاد شده است)*

### 2. سرویس‌ها و منطق تجاری (Services) - `core/services.py`
- [x] تابع `get_guard_score(soldier, reference_date)`
- [x] تابع `suggest_soldiers_for_post(post_type, shift, date, count)`
*(وضعیت: فایل `core/services.py` ایجاد شده است)*

### 3. فرم‌ها (Forms) - `core/forms.py`
- [x] فرم‌های مربوط به سربازان، مرخصی‌ها، شیفت‌ها و پست‌ها (`SoldierForm`, `LeaveForm`, و ...)
*(وضعیت: فایل `core/forms.py` ایجاد شده است)*

### 4. ویوها و قالب‌های مدیریت سربازان و مرخصی‌ها
- [x] `core/views/soldiers.py` (لیست، ایجاد، پروفایل)
- [x] `core/views/leaves.py` (مدیریت مرخصی‌ها)
- [x] تمپلیت‌های سربازان (`templates/soldiers/list.html`, `form.html`, `profile.html`)
- [x] تمپلیت‌های مرخصی (`templates/leave/list.html`, `form.html`, `delete.html`)

### 5. ویوها و قالب‌های زمان‌بندی و شیفت‌ها
- [x] `core/views/schedule.py` (زمان‌بندی و تخصیص پست‌ها)
- [x] تمپلیت‌های زمان‌بندی (`templates/schedule/calendar.html`, `view.html`, `assign_form.html`)

### 6. ویوها و قالب‌های تنظیمات (Settings)
- [x] `core/views/settings.py` (مدیریت شیفت‌ها، پست‌ها و نقش‌ها)
- [x] تمپلیت‌های مرتبط در پوشه `templates/settings/`

---

## 🟡 اولویت متوسط (هفته سوم) - گزارش‌ها و خروجی‌ها

### 7. گزارش‌ها (Reports)
- [ ] `core/views/reports.py`
  - [ ] گزارش روزانه (`daily_report`)
  - [ ] تاریخچه نگهبانی (`guard_history_report`)
- [ ] تمپلیت‌های مرتبط در پوشه `templates/reports/`

### 8. خروجی Word (DOCX) - `core/services/export.py`
- [ ] ساخت فایل و ماژول `core/services/export.py` (یا افزودن به services.py فعلی)
- [ ] توابع گرفتن خروجی (برنامه روزانه، تاریخچه، مرخصی)
- [ ] پیاده‌سازی قالب Word فارسی (RTL) با فونت مناسب
- [ ] اضافه کردن دکمه‌های دانلود در صفحات مربوطه

---

## 🟠 اولویت پایین (هفته چهارم) - تکمیلی و UI

### 9. داشبورد (Dashboard)
- [ ] `core/views/dashboard.py` (ویو `dashboard_view` برای نمایش آمار کلی)
- [ ] ایجاد تمپلیت `templates/dashboard/` یا `templates/core/dashboard.html`

### 10. پنل ادمین (Admin) - `core/admin.py`
- [x] ثبت تمامی مدل‌ها در جنگو ادمین جهت مدیریت سریع (`core/admin.py` ایجاد شده است)

### 11. رابط کاربری (UI) و مسیرها (URLs)
- [x] راه‌اندازی فایل اصلی روتینگ `core/urls.py`
- [x] ایجاد فایل پایه قالب `templates/base.html`
- [ ] راست‌چین کردن کامل (Full RTL) و تنظیم فونت فارسی (نیاز به استاتیک فایل‌ها که فعلاً 0 است)
- [ ] ایجاد منوی کناری (Sidebar) برای دسترسی سریع
