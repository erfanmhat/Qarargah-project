from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Sum, Q
from django.utils import timezone


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


class TrainingCenter(TimeStampedModel):
    title = models.CharField("نام مرکز آموزش", max_length=100, unique=True)

    class Meta:
        verbose_name = "مرکز آموزش"
        verbose_name_plural = "مرکز های آموزش"

    def __str__(self):
        return self.title


class DispatchType(models.TextChoices):
    TRAINING = 'training', 'آموزشی'
    GREEN_CARD = 'green_card', 'برگه سبز'
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


class ExtraServiceType(TimeStampedModel):
    title = models.CharField("نوع اضافه خدمت", max_length=150, unique=True)
    default_days = models.PositiveIntegerField("تعداد روز پیش‌فرض", default=0)

    class Meta:
        verbose_name = "نوع اضافه خدمت"
        verbose_name_plural = "انواع اضافه خدمت"

    def __str__(self):
        return f"{self.title} ({self.default_days} روز)"


class MilitaryRankRef(TimeStampedModel):
    """درجه نظامی برای نمایش و سرچ در UI (کد عددی + نام)"""
    code = models.PositiveIntegerField("کد درجه", unique=True, db_index=True)
    title = models.CharField("نام درجه", max_length=50, unique=True)

    class Meta:
        verbose_name = "درجه نظامی"
        verbose_name_plural = "درجه‌های نظامی"
        ordering = ["code"]

    def __str__(self):
        return f"{self.title} ({self.code})"


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


class MaritalStatus(models.TextChoices):
    SINGLE = 'single', 'مجرد'
    MARRIED = 'married', 'متاهل'


class BloodGroup(models.TextChoices):
    A_POS = 'A+', 'A+'
    A_NEG = 'A-', 'A-'
    B_POS = 'B+', 'B+'
    B_NEG = 'B-', 'B-'
    AB_POS = 'AB+', 'AB+'
    AB_NEG = 'AB-', 'AB-'
    O_POS = 'O+', 'O+'
    O_NEG = 'O-', 'O-'


class DrivingLicenseType(models.TextChoices):
    BASE_1 = '1', 'پایه ۱'
    BASE_2 = '2', 'پایه ۲'
    BASE_3 = '3', 'پایه ۳'


class Commander(TimeStampedModel):
    name = models.CharField("نام فرمانده", max_length=100, unique=True)

    # در صورت نیاز می‌توانید فیلدهای دیگری مثل درجه، شماره تماس و ... اضافه کنید

    class Meta:
        verbose_name = "فرمانده"
        verbose_name_plural = "فرماندهان"

    def __str__(self):
        return self.name


class Responsibility(TimeStampedModel):
    title = models.CharField("عنوان مسئولیت", max_length=100, unique=True)

    class Meta:
        verbose_name = "مسئولیت"
        verbose_name_plural = "مسئولیت‌ها"

    def __str__(self):
        return self.title


class Soldier(TimeStampedModel):
    # ===== اطلاعات هویتی =====
    full_name = models.CharField("نام و نام خانوادگی", max_length=100, blank=True, null=True, db_index=True)
    father_name = models.CharField("نام پدر", max_length=100, blank=True, null=True)

    national_code = models.CharField(
        "کد ملی",
        null=True, blank=True,
        max_length=10,
        unique=False,
        db_index=True,
        validators=[MinLengthValidator(10)]
    )

    issue_place = models.CharField("محل صدور", max_length=100, blank=True, null=True)
    birth_place = models.CharField("محل تولد", max_length=100, blank=True, null=True)

    birth_date = models.DateField("تاریخ تولد", null=True, blank=True)

    # ===== درجه نظامی =====
    military_rank = models.PositiveIntegerField("درجه نظامی (عدد)", blank=True, null=True)
    military_rank_ref = models.ForeignKey(
        MilitaryRankRef,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name="درجه نظامی (انتخابی)"
    )

    # ===== وضعیت خانوادگی =====
    marital_status = models.CharField("وضعیت تاهل", max_length=10, blank=True, null=True, choices=MaritalStatus.choices)
    children_count = models.PositiveIntegerField("تعداد فرزندان", blank=True, null=True)

    # ===== ویژگی‌های ظاهری/پزشکی =====
    height_cm = models.PositiveIntegerField("قد (سانتی‌متر)", blank=True, null=True)
    weight_kg = models.PositiveIntegerField("وزن (کیلوگرم)", blank=True, null=True)
    eye_color = models.CharField("رنگ چشم", max_length=30, blank=True, null=True)
    blood_group = models.CharField("گروه خونی", max_length=3, blank=True, null=True, choices=BloodGroup.choices)

    underlying_disease = models.TextField("بیماری زمینه‌ای", blank=True, null=True)
    drug_allergy = models.TextField("حساسیت دارویی", blank=True, null=True)
    used_medications = models.TextField("داروهای مصرفی", blank=True, null=True)

    # ===== اطلاعات تماس =====
    father_home_phone = models.CharField("شماره تلفن منزل پدری", max_length=11, blank=True, null=True)
    personal_home_phone = models.CharField("شماره تلفن منزل شخصی", max_length=11, blank=True, null=True)
    personal_mobile_phone = models.CharField("شماره تلفن همراه شخصی", max_length=11, blank=True, null=True)
    military_mobile_phone = models.CharField("شماره تلفن نظامی", max_length=11, blank=True, null=True)

    phone_personal = models.CharField("شماره همراه سرباز", max_length=11, blank=True, null=True)
    phone_parent = models.CharField("شماره والدین/همسر", max_length=11, blank=True, null=True)

    # ===== آدرس‌ها =====
    home_address = models.TextField("آدرس منزل", blank=True, null=True)  # فیلد قبلی حفظ شد
    postal_code = models.CharField("کد پستی", max_length=10, blank=True, null=True)

    # ===== تحصیلات =====
    education_level = models.CharField("میزان تحصیلات", max_length=50, blank=True, null=True)
    education_field = models.CharField("رشته تحصیلات", max_length=100, blank=True, null=True)

    # ===== رانندگی =====
    has_driving_license = models.BooleanField("دارای گواهی‌نامه رانندگی", blank=True, null=True)
    driving_license_type = models.CharField("نوع گواهی نامه", max_length=10, blank=True, null=True,
                                            choices=DrivingLicenseType.choices)

    # ===== اطلاعات سیستمی/خدمتی فعلی =====
    dossier_code = models.IntegerField("کد پرونده", default=0, db_index=True, blank=True)
    dispatch_type = models.CharField("نوع اعزامی", null=True, blank=True, max_length=20, choices=DispatchType.choices)
    training_center = models.ForeignKey(
        TrainingCenter, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name="مرکز آموزشی رزم مقدماتی"
    )

    health_status = models.ForeignKey(
        HealthStatus, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name="وضعیت سلامت"
    )
    service_status = models.ForeignKey(
        ServiceStatus, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name="وضعیت خدمت"
    )
    current_location = models.ForeignKey(
        ServiceLocation, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name="محل خدمت فعلی"
    )

    # ===== فیلدهای سازمانی / یگانی =====
    commander = models.ForeignKey(
        Commander,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="فرمانده",
        related_name="soldiers"
    )

    responsibility = models.ForeignKey(
        Responsibility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="مسئولیت",
        related_name="soldiers"
    )

    expertises = models.ManyToManyField(Expertise, blank=True, verbose_name="تخصص‌ها")

    # ===== اضافه خدمت =====
    extra_service_days = models.IntegerField("روزهای اضافه خدمت", default=0)
    extra_service_type = models.ForeignKey(
        ExtraServiceType,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name="نوع اضافه خدمت"
    )

    service_start_date = models.DateField("تاریخ شروع خدمت", db_index=True, null=True, blank=True)
    arrival_date = models.DateField("تاریخ ورود به ناحیه", null=True, blank=True)

    guard_code = models.CharField("کد پاسداری", max_length=50, blank=True, null=True)

    # ===== دوره‌ها =====
    completed_courses = models.TextField("دوره‌های گذرانده شده (آموزشی/میدانی)", blank=True, null=True)

    objects = SoldierManager()

    class Meta:
        verbose_name = "سرباز"
        verbose_name_plural = "سربازان"
        ordering = ['dossier_code']

    def total_reduction_days(self):
        return sum(r.days for r in self.reductions.all())

    def total_extra_days(self):
        """اگر جدول ExtraServiceLog استفاده شود، مجموع اضافه خدمت را هم حساب می‌کند."""
        log_total = self.extra_logs.aggregate(total=Sum('days'))['total'] or 0
        base = self.extra_service_days or 0
        return base + log_total

    def service_metrics(self):
        """Calculate effective service metrics based on configurable base months,
        total reductions, and extra service days."""
        if not self.service_start_date:
            return None

        try:
            base_months = int(SystemSetting.get_value('BASE_SERVICE_MONTHS', '21') or 21)
        except Exception:
            base_months = 21

        base_days = base_months * 30
        reduction_days = self.total_reduction_days()
        extra_days = max(self.total_extra_days(), 0)

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

    def get_type_str(self):
        if self.dispatch_type in (DispatchType.TRAINING, DispatchType.GREEN_CARD):
            return "سرباز"
        elif self.dispatch_type == DispatchType.GUARD_DUTY:
            return "پاسدار"
        else:
            return "-"

    def service_duration(self, base='s', unit='m'):
        """
        base: 's' برای تاریخ شروع (service_start_date) | 'a' برای تاریخ ورود (arrival_date)
        unit: 'm' برای تعداد کل ماه‌ها | 'd' برای باقیمانده روزها
        """
        from dateutil.relativedelta import relativedelta

        end_date = self.service_end_date()
        start_date = self.arrival_date if base == 'a' else self.service_start_date

        if not end_date or not start_date:
            return 0

        diff = relativedelta(end_date, start_date)

        if unit == 'm':
            return (diff.years * 12) + diff.months
        elif unit == 'd':
            return diff.days

        return 0

    def entitlement_allowance_days(self):
        """Maximum entitlement leave allowed based on dispatch group."""
        metrics = self.service_metrics()
        if not metrics:
            return 0

        full_months = metrics['full_months']
        remaining_days = metrics['remaining_days']

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
        if self.military_rank_ref and self.military_rank is None:
            self.military_rank = self.military_rank_ref.code

        if self.dispatch_type:
            if self.service_status and self.service_status.is_active_service is False:
                self.dossier_code = -1
            else:
                if self.dossier_code is None or self.dossier_code <= 0 or self.dossier_code == -1:
                    self.dossier_code = Soldier.objects.lowest_available_code(self.dispatch_type)

        super().save(*args, **kwargs)

    def clean(self):
        super().clean()

        if self.birth_date and self.service_start_date:
            if self.birth_date >= self.service_start_date:
                raise ValidationError({'birth_date': 'تاریخ تولد باید قبل از تاریخ شروع خدمت باشد.'})

        if self.arrival_date and self.service_start_date:
            if self.arrival_date < self.service_start_date:
                raise ValidationError({'arrival_date': 'تاریخ ورود به ناحیه باید بعد از تاریخ شروع خدمت باشد.'})

        if self.has_driving_license is False and self.driving_license_type:
            raise ValidationError({'driving_license_type': 'وقتی گواهینامه ندارد، نوع گواهینامه نباید انتخاب شود.'})

    def __str__(self):
        return f"{self.full_name} - {self.national_code}"


class SoldierServiceReduction(TimeStampedModel):
    soldier = models.ForeignKey(Soldier, related_name='reductions', on_delete=models.CASCADE, verbose_name="سرباز")
    reduction_type = models.ForeignKey(ServiceReductionType, on_delete=models.CASCADE, verbose_name="نوع کسر خدمت")
    days = models.PositiveIntegerField("تعداد روز")

    class Meta:
        verbose_name = "کسر خدمت سرباز"
        verbose_name_plural = "کسر خدمت‌های سربازان"

    def __str__(self):
        return f"{self.soldier} - {self.reduction_type} ({self.days} روز)"


class SoldierExtraServiceLog(TimeStampedModel):
    soldier = models.ForeignKey(Soldier, related_name='extra_logs', on_delete=models.CASCADE, verbose_name="سرباز")
    extra_type = models.ForeignKey(ExtraServiceType, on_delete=models.CASCADE, verbose_name="نوع اضافه خدمت")
    days = models.PositiveIntegerField("تعداد روز")
    notes = models.TextField("توضیحات", blank=True, null=True)

    class Meta:
        verbose_name = "اضافه خدمت سرباز"
        verbose_name_plural = "اضافه خدمت‌های سربازان"

    def __str__(self):
        return f"{self.soldier} - {self.extra_type} ({self.days} روز)"


# ==================== مرخصی ====================
class LeaveType(models.TextChoices):
    MEDICAL = 'medical', 'استعلاجی'
    REWARD = 'reward', 'تشویقی'
    ENTITLEMENT = 'entitlement', 'استحقاقی'


class Leave(TimeStampedModel):
    soldier = models.ForeignKey(Soldier, null=True, blank=True, related_name='leaves', on_delete=models.CASCADE,
                                verbose_name="سرباز")
    leave_type = models.CharField("نوع مرخصی", max_length=20, choices=LeaveType.choices)
    start_date = models.DateField("تاریخ رفت", db_index=True)

    days = models.PositiveIntegerField("مدت (روز)")

    notes = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "مرخصی"
        verbose_name_plural = "مرخصی‌ها"
        ordering = ['-created_at']

    def clean(self):
        super().clean()

        if self.days and self.days > 30:
            raise ValidationError({'days': 'مدت مرخصی نمی‌تواند بیشتر از ۳۰ روز باشد.'})

        if self.soldier and self.leave_type and self.days:
            if self.pk:
                other_leaves = Leave.objects.filter(soldier=self.soldier, leave_type=self.leave_type).exclude(
                    pk=self.pk)
            else:
                other_leaves = Leave.objects.filter(soldier=self.soldier, leave_type=self.leave_type)

            used_days = other_leaves.aggregate(total=Sum('days'))['total'] or 0

            total_with_current = used_days + self.days

            if self.leave_type == LeaveType.MEDICAL and total_with_current > 30:
                raise ValidationError({'leave_type': 'مجموع مرخصی استعلاجی نمی‌تواند بیش از ۳۰ روز باشد.'})

            if self.leave_type == LeaveType.REWARD and total_with_current > 30:
                raise ValidationError({'leave_type': 'مجموع مرخصی تشویقی نمی‌تواند بیش از ۳۰ روز باشد.'})

            if self.leave_type == LeaveType.ENTITLEMENT:
                allowed = self.soldier.entitlement_allowance_days()
                if total_with_current > allowed:
                    raise ValidationError({'leave_type': f'سقف مرخصی استحقاقی ({allowed} روز) رعایت نشده است.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.soldier} - {self.get_leave_type_display()} ({self.days} روز)"


class DocumentTemplate(models.Model):
    """
    قالب/فرم داینامیک برای تولید docx
    فایل docx داخل پوشه ثابت پروژه قرار دارد و اینجا فقط filename ذخیره می‌شود.
    """
    title = models.CharField("عنوان فرم", max_length=200)
    filename = models.CharField("نام فایل قالب", max_length=255, help_text="مثال: membership_certificate.docx")
    description = models.TextField("توضیحات", blank=True, null=True)

    is_active = models.BooleanField("فعال باشد؟", default=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    # نام فایل خروجی (قابل قالب گذاری با Jinja2)
    # مثال: certificate_{{ soldier.national_code }}_{{ now|date('Y-m-d') }}.docx
    output_filename_pattern = models.CharField(
        "الگوی نام فایل خروجی",
        max_length=255,
        default="{{ template.title }}_{{ soldier.national_code }}.docx",
        help_text="الگوی نام فایل خروجی (jinja2)"
    )

    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "قالب فرم"
        verbose_name_plural = "قالب‌های فرم"
        ordering = ("order", "id")

    def __str__(self):
        return self.title


class DocumentTemplateInput(models.Model):
    """
    فیلدهایی که هنگام تولید فرم باید از کاربر گرفته شوند
    """
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CHOICE = "choice"

    INPUT_TYPES = (
        (TEXT, "متن"),
        (NUMBER, "عدد"),
        (DATE, "تاریخ"),
        (CHOICE, "لیست انتخابی"),
    )

    template = models.ForeignKey(
        DocumentTemplate,
        verbose_name="قالب فرم",
        related_name="inputs",
        on_delete=models.CASCADE
    )

    key = models.SlugField("کلید", max_length=100, help_text="مثال: letter_number")
    label = models.CharField("عنوان فیلد", max_length=200, help_text="مثال: شماره نامه")
    input_type = models.CharField("نوع ورودی", max_length=20, choices=INPUT_TYPES, default=TEXT)

    required = models.BooleanField("اجباری باشد؟", default=True)
    placeholder = models.CharField("راهنما (placeholder)", max_length=255, blank=True, null=True)
    default_value = models.CharField("مقدار پیش‌فرض", max_length=255, blank=True, null=True)

    choices_text = models.TextField(
        "گزینه‌ها (برای لیست انتخابی)",
        blank=True,
        null=True,
        help_text="هر گزینه در یک خط. مثال:\nگزینه 1\nگزینه 2\nگزینه 3"
    )

    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "فیلد ورودی فرم"
        verbose_name_plural = "فیلدهای ورودی فرم"
        ordering = ("order", "id")
        unique_together = ("template", "key")

    def __str__(self):
        return f"{self.template.title} - {self.label}"
