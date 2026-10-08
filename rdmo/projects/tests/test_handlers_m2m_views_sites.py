import pytest

from rdmo.projects.tests.helpers.sync.arrange_project_views import arrange_projects_sites_and_views
from rdmo.projects.tests.helpers.sync.assert_project_views_or_tasks import (
    assert_all_projects_are_synced_with_instance_m2m_field,
)
from rdmo.projects.tests.helpers.sync.project_relation_ids import project_relation_ids
from rdmo.projects.tests.helpers.sync.setup import suppress_project_sync


@pytest.mark.django_db
@pytest.mark.parametrize('operation', ['add', 'remove', 'set', 'clear'])
def test_project_views_sync_when_updating_view_sites(settings, operation):
    settings.PROJECT_VIEWS_SYNC = True
    settings.MULTISITE = False
    projects, instances, restrictions = arrange_projects_sites_and_views()
    instance = instances[1]
    relation = instance.sites
    if operation == 'remove':
        with suppress_project_sync():
            relation.add(restrictions[2])
            projects[2].views.add(instance)
    initial_state = project_relation_ids('views')

    if operation == 'add':
        relation.add(restrictions[2])
        matching_projects = (1, 2)
    elif operation == 'remove':
        relation.remove(restrictions[1])
        matching_projects = (2,)
    elif operation == 'set':
        relation.set([restrictions[2]])
        matching_projects = (2,)
    else:
        relation.clear()
        matching_projects = (1, 2, 3)

    controlled_ids = [obj.pk for obj in instances.values()]
    for n, project in projects.items():
        expected = {instances[n]} if n != 1 else set()
        if n in matching_projects:
            expected.add(instance)
        assert set(project.views.filter(pk__in=controlled_ids)) == expected
    assert_all_projects_are_synced_with_instance_m2m_field(instance, 'sites')

    # Only the mutated instance may change its project assignments.
    final_state = project_relation_ids('views')
    for pk, initial_ids in initial_state.items():
        assert final_state[pk] - {instance.pk} == initial_ids - {instance.pk}
