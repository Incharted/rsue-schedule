from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('schedule', '0004_alter_userprofile_user')]
    operations = [
        migrations.AddField(model_name='userprofile', name='university_group', field=models.CharField(blank=True, max_length=150, verbose_name='Группа университета')),
        migrations.AddField(model_name='userprofile', name='study_form', field=models.CharField(blank=True, choices=[('full-time', 'Очная'), ('part-time', 'Заочная'), ('mixed', 'Очно-заочная')], max_length=20, verbose_name='Форма обучения')),
    ]
