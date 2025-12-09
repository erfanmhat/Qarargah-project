# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_leave_options_alter_soldier_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='soldier',
            name='is_vip',
        ),
    ]

