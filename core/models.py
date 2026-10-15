from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class TimeStampedModel(models.Model):
    """مدل پایه برای ذخیره زمان ایجاد و به‌روزرسانی"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ به‌روزرسانی")

    class Meta:
        abstract = True


class Soldier(TimeStampedModel):
    """سرباز"""
    first_name = models.CharField(max_length=100, verbose_name="نام")
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی")
    national_code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="کد ملی"
    )

    class Meta:
        verbose_name = "سرباز"
        verbose_name_plural = "سربازان"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Leave(TimeStampedModel):
    """مرخصی سرباز"""
    LEAVE_TYPES = [
        ("entitlement", "استحقاقی"),
        ("reward", "تشویقی"),
        ("medical", "استعلاجی"),
    ]

    soldier = models.ForeignKey(
        Soldier,
        on_delete=models.CASCADE,
        related_name='leaves',
        verbose_name="سرباز"
    )
    start_date = models.DateField(verbose_name="تاریخ شروع")
    days = models.IntegerField(verbose_name="تعداد روز")
    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPES,
        default='entitlement',
        verbose_name="نوع مرخصی"
    )
    description = models.TextField(blank=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "مرخصی"
        verbose_name_plural = "مرخصی‌ها"
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.soldier.full_name} - {self.start_date} تا {self.end_date}"
    

class ShiftConfig(TimeStampedModel):
    """تنظیمات شیفت‌های نگهبانی"""
    name = models.CharField(max_length=100, unique=True, verbose_name="نام شیفت")
    start_time = models.TimeField(verbose_name="ساعت شروع")
    end_time = models.TimeField(verbose_name="ساعت پایان")
    order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        verbose_name = "شیفت"
        verbose_name_plural = "شیفت‌ها"
        ordering = ['order', 'start_time']

    def __str__(self):
        return self.name


class PostType(TimeStampedModel):
    """نوع پست نگهبانی"""
    name = models.CharField(max_length=100, unique=True, verbose_name="نام پست")
    required_count = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="تعداد نفرات مورد نیاز"
    )

    class Meta:
        verbose_name = "نوع پست"
        verbose_name_plural = "انواع پست"

    def __str__(self):
        return self.name


class DailySchedule(TimeStampedModel):
    """برنامه روزانه نگهبانی"""
    date = models.DateField(unique=True, verbose_name="تاریخ")
    is_finalized = models.BooleanField(default=False, verbose_name="نهایی شده")
    finalized_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ نهایی‌سازی"
    )

    class Meta:
        verbose_name = "برنامه روزانه"
        verbose_name_plural = "برنامه‌های روزانه"
        ordering = ['-date']

    def __str__(self):
        return str(self.date)


class PostAssignment(TimeStampedModel):
    """تخصیص سرباز به یک پست در یک شیفت از یک روز"""
    schedule = models.ForeignKey(
        DailySchedule,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name="برنامه روز"
    )
    shift = models.ForeignKey(
        ShiftConfig,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name="شیفت"
    )
    post_type = models.ForeignKey(
        PostType,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name="پست"
    )
    soldier = models.ForeignKey(
        Soldier,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name="سرباز"
    )
    score_snapshot = models.FloatField(
        default=0,
        verbose_name="امتیاز در زمان تخصیص"
    )

    class Meta:
        verbose_name = "تخصیص پست"
        verbose_name_plural = "تخصیص‌های پست"
        unique_together = ['schedule', 'shift', 'post_type', 'soldier']

    def __str__(self):
        return f"{self.schedule.date} | {self.shift.name} | {self.post_type.name} | {self.soldier.full_name}"

