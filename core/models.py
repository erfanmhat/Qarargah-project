from django.db import models
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from django.db.models import Sum


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
    GROUP_MAP = {
        DispatchType.TRAINING: (DispatchType.TRAINING, DispatchType.GREEN_CARD),
        DispatchType.GREEN_CARD: (DispatchType.TRAINING, DispatchType.GREEN_CARD),
        DispatchType.ANSAR_PLAN: (DispatchType.ANSAR_PLAN,),
        DispatchType.GUARD_DUTY: (DispatchType.GUARD_DUTY,),
    }

    def get_group_types(self, dispatch_type):
        return self.GROUP_MAP.get(dispatch_type, (dispatch_type,))

    def lowest_available_code(self, dispatch_type):
        group_types = self.get_group_types(dispatch_type)
        active_codes = (
            self.model.objects.filter(
                dispatch_type__in=group_types,
                dossier_code__gt=0
            )
            .filter(Q(service_status__isnull=True) | Q(service_status__is_active_service=True))
            .values_list('dossier_code', flat=True)
        )
        used = set(active_codes)
        code = 1
        while code in used:
            code += 1
        return code


class Soldier(TimeStampedModel):
    first_name = models.CharField("نام", max_length=100)
    last_name = models.CharField("نام خانوادگی", max_length=100)
    national_code = models.CharField("کد ملی", max_length=10, unique=True, validators=[MinLengthValidator(10)])
    dossier_code = models.IntegerField("کد پرونده", default=0, db_index=True, blank=True)
    dispatch_type = models.CharField("نوع اعزامی", max_length=20, choices=DispatchType.choices)
    health_status = models.ForeignKey(HealthStatus, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="وضعیت سلامت")
    service_status = models.ForeignKey(ServiceStatus, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="وضعیت خدمت")
    current_location = models.ForeignKey(ServiceLocation, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="محل خدمت فعلی")
    expertises = models.ManyToManyField(Expertise, blank=True, verbose_name="تخصص‌ها")
    extra_service_days = models.IntegerField("روزهای اضافه خدمت", default=0)

    service_start_date = models.DateField("تاریخ شروع خدمت", db_index=True)
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

    def service_metrics(self):
        """
        Calculate effective service metrics based on configurable base months,
        total reductions, and extra service days.
        """
        if not self.service_start_date:
            return None
        try:
            base_months = int(SystemSetting.get_value('BASE_SERVICE_MONTHS', '21') or 21)
        except Exception:
            base_months = 21

        base_days = base_months * 30
        reduction_days = self.total_reduction_days()
        extra_days = max(self.extra_service_days or 0, 0)

        effective_days = max(base_days - reduction_days + extra_days, 0)
        full_months = effective_days // 30
        remaining_days = effective_days % 30

        return {
            'base_months': base_months,
            'base_days': base_days,
            'reduction_days': reduction_days,
            'extra_days': extra_days,
            'effective_days': effective_days,
            'full_months': full_months,
            'remaining_days': remaining_days,
        }

    def service_end_date(self):
        metrics = self.service_metrics()
        if not metrics:
            return None
        try:
            end_date = self.service_start_date + relativedelta(months=metrics['full_months'])
            end_date = end_date + timezone.timedelta(days=metrics['remaining_days'])
            return end_date
        except Exception:
            return None

    def entitlement_allowance_days(self):
        """Maximum entitlement leave allowed based on dispatch group."""
        metrics = self.service_metrics()
        if not metrics:
            return 0

        full_months = metrics['full_months']
        remaining_days = metrics['remaining_days']

        # No entitlement for Ansar scheme
        if self.dispatch_type == DispatchType.ANSAR_PLAN:
            return 0

        base_factor = 2.5
        if self.dispatch_type in (DispatchType.TRAINING, DispatchType.GREEN_CARD):
            months_for_calc = max(full_months - 1, 0)
        elif self.dispatch_type == DispatchType.GUARD_DUTY:
            months_for_calc = full_months
        else:
            months_for_calc = full_months

        allowance = (base_factor * months_for_calc) + (base_factor * remaining_days / 30)
        return int(allowance)

    def leave_usage_days(self, leave_type):
        return self.leaves.filter(leave_type=leave_type).aggregate(total=Sum('days'))['total'] or 0

    def leave_balances(self):
        """Return allowed/used/remaining for entitlement, medical, and reward leaves."""
        entitlement_allowed = self.entitlement_allowance_days()
        entitlement_used = self.leave_usage_days(LeaveType.ENTITLEMENT)
        entitlement_remaining = max(entitlement_allowed - entitlement_used, 0)

        medical_used = self.leave_usage_days(LeaveType.MEDICAL)
        medical_allowed = 30
        medical_remaining = max(medical_allowed - medical_used, 0)

        reward_used = self.leave_usage_days(LeaveType.REWARD)
        reward_allowed = 30
        reward_remaining = max(reward_allowed - reward_used, 0)

        return {
            'entitlement': {
                'allowed': entitlement_allowed,
                'used': entitlement_used,
                'remaining': entitlement_remaining,
            },
            'medical': {
                'allowed': medical_allowed,
                'used': medical_used,
                'remaining': medical_remaining,
            },
            'reward': {
                'allowed': reward_allowed,
                'used': reward_used,
                'remaining': reward_remaining,
            },
        }

    def save(self, *args, **kwargs):
        # Handle dossier code assignment and release on completion
        if self.dispatch_type:
            if self.service_status and self.service_status.is_active_service is False:
                # Mark completed service
                self.dossier_code = -1
            else:
                if self.dossier_code is None or self.dossier_code <= 0 or self.dossier_code == -1:
                    self.dossier_code = Soldier.objects.lowest_available_code(self.dispatch_type)

        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        # Validate birth date is before service start date
        if self.birth_date and self.service_start_date:
            if self.birth_date >= self.service_start_date:
                raise ValidationError({
                    'birth_date': 'تاریخ تولد باید قبل از تاریخ شروع خدمت باشد.'
                })
        
        # Validate arrival date is after service start date
        if self.arrival_date and self.service_start_date:
            if self.arrival_date < self.service_start_date:
                raise ValidationError({
                    'arrival_date': 'تاریخ ورود به ناحیه باید بعد از تاریخ شروع خدمت باشد.'
                })

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
    EMERGENCY = 'emergency', 'اضطراری'


class Leave(TimeStampedModel):
    soldier = models.ForeignKey(Soldier, related_name='leaves', on_delete=models.CASCADE, verbose_name="سرباز")
    leave_type = models.CharField("نوع مرخصی", max_length=20, choices=LeaveType.choices)
    start_date = models.DateField("تاریخ رفت", db_index=True)
    end_date = models.DateField("تاریخ برگشت", db_index=True)
    days = models.PositiveIntegerField("مدت (روز)", editable=False)
    notes = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "مرخصی"
        verbose_name_plural = "مرخصی‌ها"
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        # Validate end_date is after start_date
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    'end_date': 'تاریخ برگشت باید بعد از تاریخ رفت باشد.'
                })
            
            # Validate leave doesn't exceed reasonable duration (e.g., 30 days)
            days_diff = (self.end_date - self.start_date).days + 1
            if days_diff > 30:
                raise ValidationError({
                    'end_date': 'مدت مرخصی نمی‌تواند بیشتر از ۳۰ روز باشد.'
                })
            self.days = days_diff

        # Leave type enable/disable settings
        leave_enable_map = {
            LeaveType.ENTITLEMENT: SystemSetting.get_value('ENABLE_LEAVE_ENTITLEMENT', 'true'),
            LeaveType.MEDICAL: SystemSetting.get_value('ENABLE_LEAVE_MEDICAL', 'true'),
            LeaveType.REWARD: SystemSetting.get_value('ENABLE_LEAVE_REWARD', 'true'),
        }
        enabled_value = leave_enable_map.get(self.leave_type, 'true')
        if str(enabled_value).lower() == 'false':
            raise ValidationError({'leave_type': 'این نوع مرخصی در تنظیمات غیرفعال است.'})

        # Enforce leave type specific rules
        if self.soldier and self.leave_type:
            # Prevent entitlement leave for Ansar Scheme
            if self.leave_type == LeaveType.ENTITLEMENT and self.soldier.dispatch_type == DispatchType.ANSAR_PLAN:
                raise ValidationError({'leave_type': 'ثبت مرخصی استحقاقی برای سربازان طرح انصار مجاز نیست.'})

            # Caps for medical and reward leaves
            if self.pk:
                other_leaves = Leave.objects.filter(soldier=self.soldier, leave_type=self.leave_type).exclude(pk=self.pk)
            else:
                other_leaves = Leave.objects.filter(soldier=self.soldier, leave_type=self.leave_type)

            used_days = other_leaves.aggregate(total=Sum('days'))['total'] or 0
            total_with_current = used_days + (self.days or 0)

            if self.leave_type == LeaveType.MEDICAL and total_with_current > 30:
                raise ValidationError({'leave_type': 'مجموع مرخصی استعلاجی نمی‌تواند بیش از ۳۰ روز باشد.'})

            if self.leave_type == LeaveType.REWARD and total_with_current > 30:
                raise ValidationError({'leave_type': 'مجموع مرخصی تشویقی نمی‌تواند بیش از ۳۰ روز باشد.'})

            # Entitlement allowance check
            if self.leave_type == LeaveType.ENTITLEMENT:
                allowed = self.soldier.entitlement_allowance_days()
                if total_with_current > allowed:
                    raise ValidationError({'leave_type': f'سقف مرخصی استحقاقی ({allowed} روز) رعایت نشده است.'})

    def save(self, *args, **kwargs):
        self.full_clean()  # Call clean validation
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.soldier} - {self.get_leave_type_display()} ({self.days} روز)"