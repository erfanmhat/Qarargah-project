from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------- Reference Tables ----------
class ServiceLocation(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self): return self.name


class HealthStatus(TimeStampedModel):
    title = models.CharField(max_length=100, unique=True)
    is_exempt_from_combat = models.BooleanField(default=False)

    def __str__(self): return self.title


class DispatchType(models.TextChoices):
    TRAINING = 'training', 'آموزشی'
    GREEN_CARD = 'green_card', 'برگه سبز'
    ANSAR_PLAN = 'ansar_plan', 'طرح انصار'
    GUARD_DUTY = 'guard_duty', 'پاسدار وظیفه'


class ServiceStatus(TimeStampedModel):
    title = models.CharField(max_length=100, unique=True)
    is_active_service = models.BooleanField(default=True)

    def __str__(self): return self.title


class Expertise(TimeStampedModel):
    title = models.CharField(max_length=100, unique=True)

    def __str__(self): return self.title


class ServiceReductionType(TimeStampedModel):
    title = models.CharField(max_length=150, unique=True)
    default_days = models.PositiveIntegerField(default=0)

    def __str__(self): return f"{self.title} ({self.default_days} روز)"


# ---------- System Setting ----------
class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    @classmethod
    def get_value(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    def __str__(self):
        return f"{self.key}: {self.value}"


# ---------- Soldier ----------
class SoldierManager(models.Manager):
    def get_next_code(self, dispatch_type):
        groups = {
            ('training', 'green_card'): Soldier.objects.filter(dispatch_type__in=['training', 'green_card'],
                                                               dossier_code__gt=0),
            ('ansar_plan',): Soldier.objects.filter(dispatch_type='ansar_plan', dossier_code__gt=0),
            ('guard_duty',): Soldier.objects.filter(dispatch_type='guard_duty', dossier_code__gt=0),
        }
        for types, qs in groups.items():
            if dispatch_type in types:
                last = qs.order_by('-dossier_code').first()
                return (last.dossier_code + 1) if last else 1
        return 1

    def free_code(self, code, dispatch_type):
        groups = {
            ('training', 'green_card'): ['training', 'green_card'],
            ('ansar_plan',): ['ansar_plan'],
            ('guard_duty',): ['guard_duty'],
        }
        for types, values in groups.items():
            if dispatch_type in types:
                Soldier.objects.filter(dossier_code=code, dispatch_type__in=values).update(dossier_code=0)


class Soldier(TimeStampedModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    national_code = models.CharField(max_length=10, unique=True)
    dossier_code = models.PositiveIntegerField(default=0, db_index=True)
    dispatch_type = models.CharField(max_length=20, choices=DispatchType.choices)
    health_status = models.ForeignKey(HealthStatus, null=True, blank=True, on_delete=models.SET_NULL)
    service_status = models.ForeignKey(ServiceStatus, null=True, blank=True, on_delete=models.SET_NULL)
    current_location = models.ForeignKey(ServiceLocation, null=True, blank=True, on_delete=models.SET_NULL)
    expertises = models.ManyToManyField(Expertise, blank=True)

    service_start_date = models.DateField()
    arrival_date = models.DateField(null=True, blank=True)
    birth_date = models.DateField()

    phone_personal = models.CharField(max_length=11, blank=True)
    phone_parent = models.CharField(max_length=11, blank=True)
    phone_home = models.CharField(max_length=11, blank=True)
    phone_work = models.CharField(max_length=11, blank=True)
    home_address = models.TextField(blank=True)
    guard_code = models.CharField(max_length=50, blank=True)

    objects = SoldierManager()

    def full_name(self): return f"{self.first_name} {self.last_name}"

    def total_reduction_days(self):
        return sum(r.days for r in self.reductions.all())

    def service_end_date(self):
        months = int(SystemSetting.get_value('SERVICE_MONTHS', '21'))
        end = self.service_start_date + timezone.timedelta(days=months * 30)
        return end - timezone.timedelta(days=self.total_reduction_days())

    def __str__(self): return f"{self.full_name()} - {self.national_code}"


class SoldierServiceReduction(TimeStampedModel):
    soldier = models.ForeignKey(Soldier, related_name='reductions', on_delete=models.CASCADE)
    reduction_type = models.ForeignKey(ServiceReductionType, on_delete=models.CASCADE)
    days = models.PositiveIntegerField()

    def __str__(self): return f"{self.soldier} - {self.reduction_type}"


# ---------- Leave ----------
class LeaveType(models.TextChoices):
    MEDICAL = 'medical', 'استعلاجی'
    REWARD = 'reward', 'تشویقی'
    ENTITLEMENT = 'entitlement', 'استحقاقی'


class Leave(TimeStampedModel):
    soldier = models.ForeignKey(Soldier, related_name='leaves', on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LeaveType.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.PositiveIntegerField(editable=False)
    is_approved = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.end_date >= self.start_date:
            self.days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.soldier} - {self.get_leave_type_display()} ({self.days} روز)"
