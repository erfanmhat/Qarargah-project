from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    class Meta:
        abstract = True


# ==================== جداول مرجع ====================

class ServiceLocation(TimeStampedModel):
    name = models.CharField("نام محل خدمت", max_length=200, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                               verbose_name="محل خدمت والد")

    class Meta:
        verbose_name = "محل خدمت"
        verbose_name_plural = "محل‌های خدمت"

    def __str__(self):
        return self.name


class HealthStatus(TimeStampedModel):
    title = models.CharField("نوع سلامت", max_length=100, unique=True)
    is_exempt_from_combat = models.BooleanField("معاف از رزم", default=False)

    class Meta:
        verbose_name = "وضعیت سلامت"
        verbose_name_plural = "وضعیت‌های سلامت"

    def __str__(self):
        return self.title


class DispatchType(models.TextChoices):
    TRAINING = 'training', 'آموزشی'
    GREEN_CARD = 'green_card', 'برگه سبز'
    ANSAR_PLAN = 'ansar_plan', 'طرح انصار'
    GUARD_DUTY = 'guard_duty', 'پاسدار وظیفه'


class ServiceStatus(TimeStampedModel):
    title = models.CharField("وضعیت خدمت", max_length=100, unique=True)
    is_active_service = models.BooleanField("در حال خدمت", default=True)

    class Meta:
        verbose_name = "وضعیت خدمت"
        verbose_name_plural = "وضعیت‌های خدمت"

    def __str__(self):
        return self.title


class Expertise(TimeStampedModel):
    title = models.CharField("نام تخصص", max_length=100, unique=True)

    class Meta:
        verbose_name = "تخصص"
        verbose_name_plural = "تخصص‌ها"

    def __str__(self):
        return self.title


class ServiceReductionType(TimeStampedModel):
    title = models.CharField("نوع کسر خدمت", max_length=150, unique=True)
    default_days = models.PositiveIntegerField("تعداد روز پیش‌فرض", default=0)

    class Meta:
        verbose_name = "نوع کسر خدمت"
        verbose_name_plural = "انواع کسر خدمت"

    def __str__(self):
        return f"{self.title} ({self.default_days} روز)"


# ==================== تنظیمات سیستم ====================
class SystemSetting(models.Model):
    key = models.CharField("کلید تنظیم", max_length=100, unique=True)
    value = models.CharField("مقدار", max_length=200)
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "تنظیمات سیستم"
        verbose_name_plural = "تنظیمات سیستم"

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_value(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default


# ==================== سرباز ====================
class SoldierManager(models.Manager):
    def get_next_code(self, dispatch_type):
        groups = {
            ('training', 'green_card'): Soldier.objects.filter(dispatch_type__in=['training', 'green_card'], dossier_code__gt=0),
            ('ansar_plan',): Soldier.objects.filter(dispatch_type='ansar_plan', dossier_code__gt=0),
            ('guard_duty',): Soldier.objects.filter(dispatch_type='guard_duty', dossier_code__gt=0),
        }
        for types, qs in groups.items():
            if dispatch_type in types:
                last = qs.order_by('-dossier_code').first()
                return (last.dossier_code + 1) if last else 1
        return 1


class Soldier(TimeStampedModel):
    first_name = models.CharField("نام", max_length=100)
    last_name = models.CharField("نام خانوادگی", max_length=100)
    national_code = models.CharField("کد ملی", max_length=10, unique=True, validators=[MinLengthValidator(10)])
    dossier_code = models.PositiveIntegerField("کد پرونده", default=0, db_index=True, blank=True)
    dispatch_type = models.CharField("نوع اعزامی", max_length=20, choices=DispatchType.choices)
    health_status = models.ForeignKey(HealthStatus, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="وضعیت سلامت")
    service_status = models.ForeignKey(ServiceStatus, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="وضعیت خدمت")
    current_location = models.ForeignKey(ServiceLocation, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="محل خدمت فعلی")
    expertises = models.ManyToManyField(Expertise, blank=True, verbose_name="تخصص‌ها")

    service_start_date = models.DateField("تاریخ شروع خدمت")
    arrival_date = models.DateField("تاریخ ورود به ناحیه", null=True, blank=True)
    birth_date = models.DateField("تاریخ تولد")

    phone_personal = models.CharField("شماره همراه سرباز", max_length=11, blank=True)
    phone_parent = models.CharField("شماره والدین/همسر", max_length=11, blank=True)
    phone_home = models.CharField("تلفن منزل", max_length=11, blank=True)
    phone_work = models.CharField("تلفن محل کار", max_length=11, blank=True)
    home_address = models.TextField("آدرس منزل", blank=True)
    guard_code = models.CharField("کد پاسداری", max_length=50, blank=True)

    objects = SoldierManager()

    class Meta:
        verbose_name = "سرباز"
        verbose_name_plural = "سربازان"
        ordering = ['-service_start_date']

    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    full_name.short_description = "نام و نام خانوادگی"

    def total_reduction_days(self):
        return sum(r.days for r in self.reductions.all())

    def service_end_date(self):
        if not self.service_start_date:
            return None
        try:
            months = int(SystemSetting.get_value('SERVICE_MONTHS', '21') or 21)
            base_days = months * 30
            reduction = self.total_reduction_days()
            return self.service_start_date + timezone.timedelta(days=base_days - reduction)
        except:
            return None

    def __str__(self):
        return f"{self.full_name()} - {self.national_code}"


class SoldierServiceReduction(TimeStampedModel):
    soldier = models.ForeignKey(Soldier, related_name='reductions', on_delete=models.CASCADE, verbose_name="سرباز")
    reduction_type = models.ForeignKey(ServiceReductionType, on_delete=models.CASCADE, verbose_name="نوع کسر خدمت")
    days = models.PositiveIntegerField("تعداد روز")

    class Meta:
        verbose_name = "کسر خدمت سرباز"
        verbose_name_plural = "کسر خدمت‌های سربازان"

    def __str__(self):
        return f"{self.soldier} - {self.reduction_type} ({self.days} روز)"


# ==================== مرخصی ====================
class LeaveType(models.TextChoices):
    MEDICAL = 'medical', 'استعلاجی'
    REWARD = 'reward', 'تشویقی'
    ENTITLEMENT = 'entitlement', 'استحقاقی'


class Leave(TimeStampedModel):
    soldier = models.ForeignKey(Soldier, related_name='leaves', on_delete=models.CASCADE, verbose_name="سرباز")
    leave_type = models.CharField("نوع مرخصی", max_length=20, choices=LeaveType.choices)
    start_date = models.DateField("تاریخ رفت")
    end_date = models.DateField("تاریخ برگشت")
    days = models.PositiveIntegerField("مدت (روز)", editable=False)
    is_approved = models.BooleanField("تأیید شده توسط فرمانده", default=False)
    notes = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "مرخصی"
        verbose_name_plural = "مرخصی‌ها"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.end_date and self.start_date:
            self.days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.soldier} - {self.get_leave_type_display()} ({self.days} روز)"