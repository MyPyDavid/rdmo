from typing import Dict, List, Optional

from django import template
from django.utils.translation import gettext_lazy as _

from rdmo.core.constants import VALUE_TYPE_DATETIME, VALUE_TYPE_INTEGER, VALUE_TYPE_TEXT
from rdmo.projects.models import Project, Value

register = template.Library()


ATTRIBUTE_VALUE_MAPPER = {
    "project/id": {
        "text_attribute": "id",
        "value_type": VALUE_TYPE_INTEGER
    },
    "project/title": {
        "text_attribute": "title",
        "value_type": VALUE_TYPE_TEXT
    },
    "project/description": {
        "text_attribute": "description",
        "value_type": VALUE_TYPE_TEXT,
    },
    "project/created": {
        "text_attribute": "created",
        "value_type": VALUE_TYPE_DATETIME
    },
    "project/updated": {
        "text_attribute": "updated",
        "value_type": VALUE_TYPE_DATETIME
    },
    "project/snapshot/id": {
        "text_attribute": "snapshot__id",
        "value_type": VALUE_TYPE_INTEGER,
    },
    "project/snapshot/title": {
        "text_attribute": "snapshot__title",
        "value_type": VALUE_TYPE_TEXT,
    },
    "project/snapshot/description": {
        "text_attribute": "snapshot__description",
        "value_type": VALUE_TYPE_TEXT,
    },
    "project/snapshot/created": {
        "text_attribute": "snapshot__created",
        "value_type": VALUE_TYPE_DATETIME,
    },
    "project/snapshot/updated": {
        "text_attribute": "snapshot__updated",
        "value_type": VALUE_TYPE_DATETIME,
    },
}


def get_value_from_mapped_attribute(attribute: str, project: Project) -> Value:

    if attribute not in ATTRIBUTE_VALUE_MAPPER:
        raise ValueError(f"Attribute {attribute} is not supported")
    attribute_value_map = ATTRIBUTE_VALUE_MAPPER[attribute]

    text = getattr(project, attribute_value_map["text_attribute"])
    value_type = attribute_value_map["value_type"]
    return Value(text=text, value_type=value_type)

def get_values_from_project_or_mapper(context: dict, attribute: str,
                                      set_prefix: str, set_index: str,
                                      index, project, **kwargs) -> List[Optional[Dict[str, str]]]:
    if project is None:
        project = context['project']

    if attribute in ATTRIBUTE_VALUE_MAPPER:
        value = get_value_from_mapped_attribute(attribute, project)
        return [value.as_dict]
    else:
        return project._get_values(attribute, set_prefix, set_index, index)

def get_values_func(*args, **kwargs):
    values = get_values_from_project_or_mapper(*args, **kwargs)
    return values

def get_value_func(*args, **kwargs):
    values = get_values_from_project_or_mapper(*args, **kwargs)
    try:
        return values[0]
    except IndexError:
        return None

@register.simple_tag(takes_context=True)
def get_values(context, attribute, set_prefix='*', set_index='*', index='*', project=None):
    values = get_values_func(context, attribute, set_prefix, set_index, index, project)
    return values


@register.simple_tag(takes_context=True)
def get_numbers(context, attribute, set_prefix='*', set_index='*', index='*', project=None):
    values = get_values_func(context, attribute, set_prefix, set_index, index, project)
    return (value.get('as_number', 0) for value in values)


@register.simple_tag(takes_context=True)
def get_value(context, attribute, set_prefix='', set_index=0, index=0, project=None):
    value = get_value_func(context, attribute, set_prefix, set_index, index, project)
    return value

@register.simple_tag(takes_context=True)
def get_number(context, attribute, set_prefix='', set_index=0, index=0, project=None):
    value = get_value_func(context, attribute, set_prefix, set_index, index, project)
    if value is None:
        return 0
    return value.get('as_number', 0)


@register.simple_tag(takes_context=True)
def get_set_values(context, set, attribute, set_prefix='', index='*', project=None):
    set_index = set.get('set_index')
    return get_values_func(context, attribute, set_prefix, index, set_index, project)


@register.simple_tag(takes_context=True)
def get_set_value(context, set, attribute, set_prefix='', index=0, project=None):
    set_index = set.get('set_index')
    value = get_value_func(context, attribute, set_prefix, set_index, index, project)
    return value


@register.simple_tag(takes_context=True)
def get_set_prefixes(context, attribute, project=None):
    try:
        _dct = {value['set_prefix'] for value in get_values(context, attribute, project=project)}
        return sorted(_dct)
    except IndexError:
        return None


@register.simple_tag(takes_context=True)
def get_set_indexes(context, attribute, set_prefix='', project=None):
    try:
        _idx = {value['set_index'] for value in get_values(context, attribute, set_prefix=set_prefix, project=project)}
        return sorted(_idx)
    except IndexError:
        return None


@register.simple_tag(takes_context=True)
def get_sets(context, attribute, set_prefix='', project=None):
    # get the values for the set attribute
    values = get_values(context, attribute.rstrip('/'), set_prefix=set_prefix, index=0, project=project)
    if values:
        return values
    elif not attribute.endswith('/id'):
        # for backwards compatibility, try again with the /id attribute
        return get_sets(context, attribute.rstrip('/') + '/id', set_prefix=set_prefix, project=project)


@register.simple_tag(takes_context=True)
def get_set(context, attribute, set_prefix='', project=None):
    # for backwards compatibility, identical to get_sets
    return get_sets(context, attribute, set_prefix=set_prefix, project=project)


@register.inclusion_tag('views/tags/value.html', takes_context=True)
def render_value(context, attribute, set_prefix='', set_index=0, index=0, project=None):
    context['value'] = get_value(context, attribute, set_prefix=set_prefix, set_index=set_index,
                                 index=index, project=project)
    return context


@register.inclusion_tag('views/tags/value_list.html', takes_context=True)
def render_value_list(context, attribute, set_prefix='', set_index=0, project=None):
    context['values'] = get_values(context, attribute, set_prefix=set_prefix, set_index=set_index, project=project)
    return context


@register.inclusion_tag('views/tags/value_inline_list.html', takes_context=True)
def render_value_inline_list(context, attribute, set_prefix='', set_index=0, project=None):
    context['values'] = get_values(context, attribute, set_prefix=set_prefix, set_index=set_index, project=project)
    return context


@register.inclusion_tag('views/tags/value.html', takes_context=True)
def render_set_value(context, set, attribute, set_prefix='', index=0, project=None):
    context['value'] = get_set_value(context, set, attribute, set_prefix=set_prefix, index=index, project=project)
    return context


@register.inclusion_tag('views/tags/value_list.html', takes_context=True)
def render_set_value_list(context, set, attribute, set_prefix='', project=None):
    context['values'] = get_set_values(context, set, attribute, set_prefix=set_prefix, project=project)
    return context


@register.inclusion_tag('views/tags/value_inline_list.html', takes_context=True)
def render_set_value_inline_list(context, set, attribute, set_prefix='', project=None):
    context['values'] = get_set_values(context, set, attribute, set_prefix=set_prefix, project=project)
    return context


@register.simple_tag(takes_context=True)
def check_element(context, element, set_prefix=None, set_index=None, project=None):
    if project is None:
        project = context['project']

    return project._check_element(element, set_prefix=None, set_index=None)


@register.simple_tag(takes_context=True)
def check_condition(context, condition, set_prefix=None, set_index=None, project=None):
    if project is None:
        project = context['project']

    return project._check_condition(condition, set_prefix=None, set_index=None)


@register.simple_tag(takes_context=True)
def get_labels(context, element, set_prefix='', set_index=0, project=None):
    if project is None:
        project = context['project']

    set_labels = []
    for ancestor in element['ancestors']:
        if ancestor['is_collection']:
            set_label = f'#{set_index + 1}'

            if ancestor['attribute']:
                # get attribute value
                value = get_value(context, ancestor['attribute'], set_prefix=set_prefix, set_index=set_index,
                                  index=0, project=project)
                if value:
                    set_label = '"{}"'.format(value['value'])

            set_labels.append('{} {}'.format(ancestor['verbose_name'].title() or _('Set'), set_label))

            if set_prefix != '':
                rpartition = set_prefix.rpartition('|')
                set_prefix, set_index = rpartition[0], int(rpartition[2])

    # flip the list
    set_labels.reverse()

    return set_labels


@register.filter
def is_true(values):
    return [value for value in values if value['is_true']]


@register.filter
def is_false(values):
    return [value for value in values if value['is_false']]


@register.filter
def is_empty(values):
    return [value for value in values if value['is_empty']]


@register.filter
def is_not_empty(values):
    return [value for value in values if not value['is_empty']]
