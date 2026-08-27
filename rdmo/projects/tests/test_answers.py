import pytest

from rdmo.projects.answers import AnswerTree
from rdmo.projects.models import Value


def test_value_index_preserves_element_lookup_semantics(mocker):
    catalog = mocker.Mock()
    catalog.conditions.in_bulk.return_value = {}
    values = [
        Value(attribute_id=1, set_prefix='', set_index=0, collection_index=0, text='first'),
        Value(attribute_id=None, set_prefix='', set_index=0, collection_index=0, text='without attribute'),
        Value(attribute_id=1, set_prefix='', set_index=0, collection_index=1, text='second'),
        Value(attribute_id=1, set_prefix='0', set_index=0, collection_index=0, text='nested'),
    ]
    answer_tree = AnswerTree(catalog, values)

    for attribute_id in (1, None):
        element = mocker.Mock(attribute_id=attribute_id)
        expected = [
            {'collection_index': value.collection_index, 'is_empty': value.is_empty}
            for value in values
            if value.attribute_id == attribute_id and value.set_prefix == '' and value.set_index == 0
        ]

        assert answer_tree.compute_element_values(element, ('', 0)) == expected


def test_value_index_computes_same_sets_as_value_queryset(db):
    values = Value.objects.filter(project_id=1, snapshot=None)
    expected = dict(values.compute_sets())

    catalog = values.first().project.catalog
    answer_tree = AnswerTree(catalog, values)

    assert dict(answer_tree.sets) == expected


@pytest.mark.parametrize('parent_set, set_level', [
    (None, 0),
    (('0', 0), 1),
    (('1|2', 1), 2),
    (('3|4|5', 2), 3),
    (('6|7|8|9', 3), 4),
])
def test_compute_set_level(parent_set, set_level):
    assert AnswerTree.compute_set_level(parent_set) == set_level


@pytest.mark.parametrize('parent_set, set_prefix', [
    (None, ''),
    (('', 0), '0'),
    (('0', 1), '0|1'),
    (('1|2', 3), '1|2|3'),
    (('4|5|6', 7), '4|5|6|7')
])
def test_compute_child_set_prefix(parent_set, set_prefix):
    assert AnswerTree.compute_child_set_prefix(parent_set) == set_prefix


@pytest.mark.parametrize('descendant_set_prefix, level, ancestor_set', [
    (None, 1, None),
    ('', 1, None),
    ('1|2|3|4|5', 1, ('1', 2)),
    ('1|2|3|4|5', 2, ('1|2', 3)),
    ('1|2|3|4|5', 3, ('1|2|3', 4)),
    ('1|2|3|4|5', 4, ('1|2|3|4', 5)),
    ('1|2|3|4|5', 5, None)
])
def test_compute_ancestor_set(descendant_set_prefix, level, ancestor_set):
    assert AnswerTree.compute_ancestor_set(descendant_set_prefix, level) == ancestor_set
