import pytest

from rdmo.projects.answers import AnswerTree

from ..models import Project


def test_conditions_fallback(db):
    project = Project.objects.get(id=1)
    answer_tree = AnswerTree(project.catalog, project.values.filter(snapshot=None))

    assert set(answer_tree.conditions) == set(project.catalog.conditions.values_list('id', flat=True))


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
