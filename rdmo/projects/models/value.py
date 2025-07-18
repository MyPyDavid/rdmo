import mimetypes
from pathlib import Path

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import iso8601
from django_cleanup import cleanup

from rdmo.core.constants import VALUE_TYPE_BOOLEAN, VALUE_TYPE_CHOICES, VALUE_TYPE_DATETIME, VALUE_TYPE_TEXT
from rdmo.core.models import Model
from rdmo.domain.models import Attribute
from rdmo.options.models import Option

from ..managers import ValueManager
from ..utils import get_value_path


def get_file_upload_to(instance, filename):
    return str(get_value_path(instance.project, instance.snapshot) / str(instance.id) / filename)


class Value(Model):

    objects = ValueManager()

    FALSE_TEXT = [None, '', '0', 'f', 'F', 'false', 'False']

    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, related_name='values',
        verbose_name=_('Project'),
        help_text=_('The project this value belongs to.')
    )
    snapshot = models.ForeignKey(
        'Snapshot', blank=True, null=True,
        on_delete=models.CASCADE, related_name='values',
        verbose_name=_('Snapshot'),
        help_text=_('The snapshot this value belongs to.')
    )
    attribute = models.ForeignKey(
        Attribute, blank=True, null=True,
        on_delete=models.SET_NULL, related_name='values',
        verbose_name=_('Attribute'),
        help_text=_('The attribute this value belongs to.')
    )
    set_prefix = models.CharField(
        max_length=16, blank=True, default='',
        verbose_name=_('Set prefix'),
        help_text=_('The position of this value with respect to superior sets (i.e. for nested question sets).')
    )
    set_index = models.IntegerField(
        default=0,
        verbose_name=_('Set index'),
        help_text=_('The position of this value in a set (i.e. for a question set tagged as collection).')
    )
    set_collection = models.BooleanField(
        null=True,
        verbose_name=_('Set collection'),
        help_text=_('Indicates if this value was entered as part of a set (important for conditions).')
    )
    collection_index = models.IntegerField(
        default=0,
        verbose_name=_('Collection index'),
        help_text=_('The position of this value in a list (i.e. for a question tagged as collection).')
    )
    text = models.TextField(
        blank=True,
        verbose_name=_('Text'),
        help_text=_('The string stored for this value.')
    )
    option = models.ForeignKey(
        Option, blank=True, null=True, on_delete=models.SET_NULL, related_name='values',
        verbose_name=_('Option'),
        help_text=_('The option stored for this value.')
    )
    file = models.FileField(
        upload_to=get_file_upload_to, null=True, blank=True,
        verbose_name=_('File'),
        help_text=_('The file stored for this value.')
    )
    value_type = models.CharField(
        max_length=8, choices=VALUE_TYPE_CHOICES, default=VALUE_TYPE_TEXT,
        verbose_name=_('Value type'),
        help_text=_('Type of this value.')
    )
    unit = models.CharField(
        max_length=64, blank=True,
        verbose_name=_('Unit'),
        help_text=_('Unit for this value.')
    )
    external_id = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('External id'),
        help_text=_('External id for this value.')
    )

    class Meta:
        ordering = ('project', 'snapshot', 'attribute', 'set_prefix', 'set_index', 'collection_index')
        verbose_name = _('Value')
        verbose_name_plural = _('Values')

    def __str__(self):
        return '{} / {} / {} / {} / {}'.format(
            self.project, self.snapshot or '-', self.set_prefix, self.set_index, self.collection_index
        )

    @property
    def as_dict(self):
        value_dict = {
            'id': self.id,
            'created': self.created,
            'updated': self.updated,
            'set_prefix': self.set_prefix,
            'set_index': self.set_index,
            'set_collection': self.set_collection,
            'collection_index': self.collection_index,
            'value_type': self.value_type,
            'unit': self.unit,
            'text': self.text,
            'option_uri': self.option_uri,
            'option_text': self.option_text,
            'option_additional_input': self.option_additional_input,
            'external_id': self.external_id,
            'value': self.value,
            'value_and_unit': self.value_and_unit,
            'is_true': self.is_true,
            'is_false': self.is_false,
            'is_empty': self.is_empty,
            'as_number': self.as_number
        }

        if self.file:
            value_dict.update({
                'file_name': self.file_name,
                'file_url': self.file_url,
                'file_type': self.file_type,
                'file_path': self.file_path
            })

        return value_dict

    @property
    def label(self):
        if self.option:
            return self.get_option_display(view=False)
        elif self.file:
            return self.get_file_display()
        elif self.text:
            return self.get_text_display()
        else:
            return ''

    @property
    def value(self):
        if self.option:
            return self.get_option_display(view=True)
        elif self.file:
            return self.get_file_display()
        elif self.text:
            return self.get_text_display()
        else:
            return ''

    @property
    def value_and_unit(self):
        if self.unit:
            return f'{self.value} {self.unit}'
        else:
            return self.value

    @property
    def is_true(self):
        return any([
            self.text not in self.FALSE_TEXT,
            self.option,
            self.file,
            self.external_id != ''
        ])

    @property
    def is_false(self):
        return all([
            self.text in self.FALSE_TEXT,
            not self.option,
            not self.file,
            self.external_id == ''
        ])

    @property
    def is_empty(self):
        return all([
            self.text == '',
            not self.option,
            not self.file,
            self.external_id == ''
        ])

    @property
    def as_number(self):
        try:
            val = self.text
        except AttributeError:
            return 0
        else:
            if isinstance(val, str):
                val = val.replace(',', '.')

            if isinstance(val, float) is False:
                try:
                    return int(val)
                except (ValueError, TypeError):
                    pass
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return 0
            else:
                return val

    @property
    def file_name(self) -> str:
        if self.file:
            return Path(self.file.name).name

    @property
    def file_url(self) -> str:
        if self.file:
            return reverse('v1-projects:value-file', args=[self.id])

    @property
    def file_type(self) -> str:
        if self.file:
            return mimetypes.guess_type(self.file.name)[0]

    @property
    def file_path(self) -> Path:
        if self.file:
            resource_path = get_value_path(self.project, self.snapshot)
            return Path(self.file.name).relative_to(resource_path).as_posix()

    @property
    def attribute_uri(self) -> str:
        if self.attribute is not None:
            return self.attribute.uri

    @property
    def option_uri(self) -> str:
        if self.option is not None:
            return self.option.uri

    @property
    def option_text(self) -> str:
        if self.option is not None:
            return self.option.text

    @property
    def option_additional_input(self):
        if self.option is not None:
            return self.option.additional_input

    def copy_file(self, file_name, file_content):
        # copies a file field from a different value over to this value
        # this is tricky, because we need to trick django_cleanup to not delete the original file
        # important for snapshots and import from projects
        self.file.save(file_name, file_content, save=False)
        cleanup.refresh(self)
        self.save()

    def get_text_display(self):
        if self.value_type == VALUE_TYPE_DATETIME:
            try:
                return iso8601.parse_date(self.text).date()
            except iso8601.ParseError:
                return self.text
        elif self.value_type == VALUE_TYPE_BOOLEAN:
            if self.text == '1':
                return _('Yes')
            else:
                return _('No')
        else:
            return self.text

    def get_option_display(self, view=True):
        if view:
            string = self.option.view_text or self.option.text or ''
        else:
            string = self.option.text or ''
        if self.option.additional_input and self.text:
            string += ': ' + self.text
        return string

    def get_file_display(self):
        return self.file_name
