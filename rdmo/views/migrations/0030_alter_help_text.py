# Generated by Django 4.2.6 on 2023-12-04 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('views', '0029_view_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='view',
            name='help_lang1',
            field=models.TextField(blank=True, help_text='The help text for this view (in the primary language).', verbose_name='Help (primary)'),
        ),
        migrations.AlterField(
            model_name='view',
            name='help_lang2',
            field=models.TextField(blank=True, help_text='The help text for this view (in the secondary language).', verbose_name='Help (secondary)'),
        ),
        migrations.AlterField(
            model_name='view',
            name='help_lang3',
            field=models.TextField(blank=True, help_text='The help text for this view (in the tertiary language).', verbose_name='Help (tertiary)'),
        ),
        migrations.AlterField(
            model_name='view',
            name='help_lang4',
            field=models.TextField(blank=True, help_text='The help text for this view (in the quaternary language).', verbose_name='Help (quaternary)'),
        ),
        migrations.AlterField(
            model_name='view',
            name='help_lang5',
            field=models.TextField(blank=True, help_text='The help text for this view (in the quinary language).', verbose_name='Help (quinary)'),
        ),
        migrations.AlterField(
            model_name='view',
            name='title_lang1',
            field=models.CharField(blank=True, help_text='The title for this view (in the primary language).', max_length=256, verbose_name='Title (primary)'),
        ),
        migrations.AlterField(
            model_name='view',
            name='title_lang2',
            field=models.CharField(blank=True, help_text='The title for this view (in the secondary language).', max_length=256, verbose_name='Title (secondary)'),
        ),
        migrations.AlterField(
            model_name='view',
            name='title_lang3',
            field=models.CharField(blank=True, help_text='The title for this view (in the tertiary language).', max_length=256, verbose_name='Title (tertiary)'),
        ),
        migrations.AlterField(
            model_name='view',
            name='title_lang4',
            field=models.CharField(blank=True, help_text='The title for this view (in the quaternary language).', max_length=256, verbose_name='Title (quaternary)'),
        ),
        migrations.AlterField(
            model_name='view',
            name='title_lang5',
            field=models.CharField(blank=True, help_text='The title for this view (in the quinary language).', max_length=256, verbose_name='Title (quinary)'),
        ),
    ]