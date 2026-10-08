import pytest

from rdmo.projects.models import Membership
from rdmo.projects.tests.helpers.sync.arrange_project_tasks import arrange_projects_groups_and_tasks
from rdmo.projects.tests.helpers.sync.assert_project_views_or_tasks import (
    assert_all_projects_are_synced_with_instance_m2m_field,
)
from rdmo.projects.tests.helpers.sync.project_relation_ids import project_relation_ids
from rdmo.projects.tests.helpers.sync.setup import suppress_project_sync


@pytest.mark.django_db
@pytest.mark.parametrize('operation', ['add', 'remove', 'set', 'clear'])
def test_project_tasks_sync_when_updating_task_groups(settings, operation):
    settings.PROJECT_TASKS_SYNC = True
    settings.MULTISITE = False
    projects, instances, restrictions = arrange_projects_groups_and_tasks()
    instance = instances[1]
    relation = instance.groups
    if operation == 'remove':
        with suppress_project_sync():
            relation.add(restrictions[2])
            projects[2].tasks.add(instance)
    initial_state = project_relation_ids('tasks')

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
        assert set(project.tasks.filter(pk__in=controlled_ids)) == expected
    assert_all_projects_are_synced_with_instance_m2m_field(instance, 'groups')

    # Only the mutated instance may change its project assignments.
    final_state = project_relation_ids('tasks')
    for pk, initial_ids in initial_state.items():
        assert final_state[pk] - {instance.pk} == initial_ids - {instance.pk}


def test_project_sync_with_any_owner_group_overlap(sync_case, settings):
    sync_case.user.groups.add(sync_case.group, sync_case.other_group)
    Membership.objects.create(project=sync_case.project, user=sync_case.user, role='owner')
    setattr(settings, f'PROJECT_{sync_case.field.upper()}_SYNC', True)

    sync_case.instance.groups.add(sync_case.group)

    assert sync_case.instance in getattr(sync_case.project, sync_case.field).all()
    assert_all_projects_are_synced_with_instance_m2m_field(sync_case.instance, 'groups')
