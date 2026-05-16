import json
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ==================== مدل پایه ====================

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    class Meta:
        abstract = True


# ==================== جداول تنظیمات / مرجع ====================

class SoldierRole(TimeStampedModel):
    """نقش / تخصص سرباز — قابل افزودن توسط کاربر"""
    title = models.CharField("عنوان نقش", max_length=100, unique=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "نقش سرباز"
        verbose_name_plural = "نقش‌های سربازان"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class ShiftConfig(TimeStampedModel):
    """تنظیمات پاس نگهبانی — پویا و قابل تغییر"""
    name = models.CharField("نام پاس", max_length=50)
    start_time = models.TimeField("ساعت شروع")
    end_time = models.TimeField("ساعت پایان")
    order = models.PositiveIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "پاس نگهبانی"
        verbose_name_plural = "پاس‌های نگهبانی"
        ordering = ["order", "start_time"]

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')})"


class HealthType(models.TextChoices):
    HEALTHY = "healthy", "سالم"
    PSYCH_EXEMPT = "psych_exempt", "معاف از رزم اعصاب و روان"
    OTHER_EXEMPT = "other_exempt", "معاف از رزم سایر"


class PostType(TimeStampedModel):
    """
    نوع پست نگهبانی — پویا و قابل تنظیم.
    هر پست مشخص می‌کند چند سرباز در چند پاس نیاز دارد
    و کدام وضعیت سلامت مجاز است.
    """
    name = models.CharField("نام پست", max_length=100, unique=True)

    # وضعیت‌های سلامت مجاز (JSON list از مقادیر HealthType)
    # مثال: ["healthy", "other_exempt"]  یا  ["psych_exempt"]
    allowed_health_types = models.TextField(
        "وضعیت سلامت مجاز",
        default=list,
        help_text='مثال: ["healthy", "other_exempt"]'
    )

    soldiers_per_shift = models.PositiveIntegerField(
        "تعداد سرباز در هر پاس",
        default=1,
        help_text="برای پست‌های بدون پاس‌بندی این عدد کل تعداد مورد نیاز است"
    )
    shift_count = models.PositiveIntegerField(
        "تعداد پاس",
        default=3,
        help_text="برای پست‌های بدون پاس‌بندی مثل راننده عدد ۱ وارد کنید"
    )
    is_shift_based = models.BooleanField(
        "پاس‌بندی دارد؟",
        default=True,
        help_text="اگر خیر باشد (مثل راننده) پاس انتخاب نمی‌شود"
    )

    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "نوع پست"
        verbose_name_plural = "انواع پست"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name

    def total_soldiers_needed(self):
        """کل سربازان مورد نیاز در یک روز"""
        if self.is_shift_based:
            return self.soldiers_per_shift * self.shift_count
        return self.soldiers_per_shift

    def get_allowed_health_types(self):
        return json.loads(self.allowed_health_types or "[]")

    def is_health_type_allowed(self, health_type: str) -> bool:
        return health_type in self.get_allowed_health_types()


# ==================== سرباز ====================

class Soldier(TimeStampedModel):
    # ===== اطلاعات هویتی =====
    full_name = models.CharField("نام و نام خانوادگی", max_length=100, db_index=True)
    national_code = models.CharField(
        "کد ملی",
        max_length=10,
        unique=True,
        db_index=True,
    )

    # ===== وضعیت سلامت =====
    health_type = models.CharField(
        "وضعیت سلامت",
        max_length=20,
        choices=HealthType.choices,
        default=HealthType.HEALTHY,
        db_index=True,
    )

    # ===== نقش / تخصص =====
    role = models.ForeignKey(
        SoldierRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="نقش / تخصص",
        related_name="soldiers",
    )

    # ===== رانندگی =====
    has_driving_license = models.BooleanField("دارای گواهینامه رانندگی", default=False)
    driving_license_type = models.CharField(
        "نوع گواهینامه",
        max_length=10,
        blank=True,
        null=True,
        choices=[("1", "پایه ۱"), ("2", "پایه ۲"), ("3", "پایه ۳")],
    )

    # ===== وضعیت خدمت =====
    is_active = models.BooleanField(
        "در خدمت است؟",
        default=True,
        db_index=True,
        help_text="سربازانی که ترخیص شده‌اند یا موقتاً خارج از مجموعه‌اند غیرفعال کنید"
    )

    notes = models.TextField("توضیحات", blank=True, null=True)

    class Meta:
        verbose_name = "سرباز"
        verbose_name_plural = "سربازان"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.get_health_type_display()})"

    def is_on_leave(self, date=None):
        """آیا سرباز در تاریخ مشخص در مرخصی است؟"""
        if date is None:
            date = timezone.now().date()
        return self.leaves.filter(
            start_date__lte=date,
            end_date__gte=date,
        ).exists()

    def last_post_assignment(self):
        """آخرین پست دریافتی سرباز"""
        return (
            self.assignments
            .select_related("schedule")
            .order_by("-schedule__date", "-created_at")
            .first()
        )

    def guard_score(self, reference_date=None):
        """
        امتیاز سرباز برای پیشنهاد نگهبانی.
        هر چه امتیاز بالاتر، اولویت بیشتر برای پیشنهاد.

        محاسبه:
          - اگر هیچ پست قبلی ندارد → امتیاز ۹۹۹ (بالاترین اولویت)
          - فاصله روز از آخرین پست = امتیاز پایه
          - اگر مرخصی بوده و برگشته → bonus ۴۸ ساعت (۲ روز) اضافه می‌شود
          - اگر کمتر از ۱ روز گذشته → امتیاز پایه منفی (زیر ۲۴ ساعت)
        """
        if reference_date is None:
            reference_date = timezone.now().date()

        last = self.last_post_assignment()
        if last is None:
            return 999

        last_date = last.schedule.date
        days_since = (reference_date - last_date).days

        bonus = 0
        # اگر سرباز بعد از آخرین پست مرخصی رفته و برگشته → bonus
        returned_from_leave = self.leaves.filter(
            end_date__gt=last_date,
            end_date__lt=reference_date,
        ).exists()
        if returned_from_leave:
            bonus = 2

        return days_since + bonus

    def clean(self):
        super().clean()
        if not self.has_driving_license and self.driving_license_type:
            raise ValidationError(
                {"driving_license_type": "وقتی گواهینامه ندارد، نوع گواهینامه نباید انتخاب شود."}
            )


# ==================== مرخصی ====================

class LeaveType(models.TextChoices):
    ENTITLEMENT = "entitlement", "استحقاقی"
    REWARD = "reward", "تشویقی"
    MEDICAL = "medical", "استعلاجی"


class Leave(TimeStampedModel):
    soldier = models.ForeignKey(
        Soldier,
        on_delete=models.CASCADE,
        related_name="leaves",
        verbose_name="سرباز",
    )
    leave_type = models.CharField(
        "نوع مرخصی",
        max_length=20,
        choices=LeaveType.choices,
        db_index=True,
    )
    start_date = models.DateField("تاریخ شروع (رفت)", db_index=True)
    days = models.PositiveIntegerField("تعداد روز")
    end_date = models.DateField(
        "تاریخ پایان (بازگشت)",
        editable=False,
        db_index=True,
    )
    notes = models.TextField("توضیحات", blank=True, null=True)

    class Meta:
        verbose_name = "مرخصی"
        verbose_name_plural = "مرخصی‌ها"
        ordering = ["-start_date"]

    def __str__(self):
        return (
            f"{self.soldier.full_name} — {self.get_leave_type_display()} "
            f"({self.start_date} به مدت {self.days} روز)"
        )

    @property
    def return_date(self):
        """تاریخ بازگشت (روز بعد از پایان مرخصی)"""
        from datetime import timedelta
        return self.end_date + timedelta(days=1)

    def save(self, *args, **kwargs):
        # end_date همیشه از start_date + days - 1 محاسبه می‌شود
        from datetime import timedelta
        self.end_date = self.start_date + timedelta(days=self.days - 1)
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.days and self.days < 1:
            raise ValidationError({"days": "تعداد روز مرخصی باید حداقل ۱ روز باشد."})
        if self.days and self.days > 30:
            raise ValidationError({"days": "مدت مرخصی نمی‌تواند بیشتر از ۳۰ روز باشد."})


# ==================== برنامه روزانه ====================

class DailySchedule(TimeStampedModel):
    """
    برنامه نگهبانی یک روز.
    هر روز یک رکورد DailySchedule دارد.
    """
    date = models.DateField("تاریخ", unique=True, db_index=True)
    is_finalized = models.BooleanField(
        "نهایی شده؟",
        default=False,
        help_text="بعد از تأیید نهایی، برنامه قفل می‌شود"
    )
    notes = models.TextField("یادداشت", blank=True, null=True)

    class Meta:
        verbose_name = "برنامه روزانه"
        verbose_name_plural = "برنامه‌های روزانه"
        ordering = ["-date"]

    def __str__(self):
        status = "✓ نهایی" if self.is_finalized else "در حال تنظیم"
        return f"برنامه {self.date} — {status}"

    def get_assignments_grid(self):
        """
        خروجی گرید برنامه برای نمایش در template.
        ساختار: { post_type_id: { shift_id_or_None: [assignment, ...] } }
        """
        grid = {}
        for assignment in self.assignments.select_related(
            "post_type", "shift", "soldier"
        ).order_by("post_type__order", "shift__order"):
            pt_id = assignment.post_type_id
            sh_id = assignment.shift_id
            grid.setdefault(pt_id, {}).setdefault(sh_id, []).append(assignment)
        return grid


class PostAssignment(TimeStampedModel):
    """
    تخصیص یک سرباز به یک پست در یک پاس مشخص.
    اگر پست پاس‌بندی ندارد (is_shift_based=False)، shift=None است.
    """
    schedule = models.ForeignKey(
        DailySchedule,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="برنامه روزانه",
    )
    post_type = models.ForeignKey(
        PostType,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="نوع پست",
    )
    shift = models.ForeignKey(
        ShiftConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments",
        verbose_name="پاس",
    )
    soldier = models.ForeignKey(
        Soldier,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="سرباز",
    )

    # آیا قرارگاه این را دستی تغییر داده (override پیشنهاد سیستم)
    is_override = models.BooleanField(
        "انتخاب دستی",
        default=False,
        help_text="اگر قرارگاه پیشنهاد سیستم را نادیده گرفته و دستی انتخاب کرده"
    )

    class Meta:
        verbose_name = "تخصیص پست"
        verbose_name_plural = "تخصیص‌های پست"
        ordering = ["post_type__order", "shift__order"]
        # یک سرباز در یک برنامه + پست + پاس نمی‌تواند تکراری باشد
        unique_together = [["schedule", "post_type", "shift", "soldier"]]

    def __str__(self):
        shift_str = str(self.shift) if self.shift else "بدون پاس"
        return (
            f"{self.schedule.date} | {self.post_type.name} | "
            f"{shift_str} | {self.soldier.full_name}"
        )

    def clean(self):
        super().clean()

        # سرباز نباید در همان روز بیش از ۲ پاس داشته باشد
        if self.schedule and self.soldier:
            existing_shifts = PostAssignment.objects.filter(
                schedule=self.schedule,
                soldier=self.soldier,
                post_type__is_shift_based=True,
            ).exclude(pk=self.pk)
            if existing_shifts.count() >= 2:
                raise ValidationError(
                    f"سرباز {self.soldier.full_name} در این روز قبلاً ۲ پاس دارد."
                )

        # سرباز نباید در تاریخ برنامه در مرخصی باشد
        if self.schedule and self.soldier:
            if self.soldier.is_on_leave(self.schedule.date):
                raise ValidationError(
                    f"سرباز {self.soldier.full_name} در تاریخ {self.schedule.date} در مرخصی است."
                )

        # وضعیت سلامت سرباز باید با پست مطابقت داشته باشد
        if self.post_type and self.soldier:
            if not self.post_type.is_health_type_allowed(self.soldier.health_type):
                raise ValidationError(
                    f"وضعیت سلامت سرباز ({self.soldier.get_health_type_display()}) "
                    f"برای پست «{self.post_type.name}» مجاز نیست."
                )
