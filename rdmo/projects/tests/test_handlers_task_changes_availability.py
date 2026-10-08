import pytest

from rdmo.projects.tests.helpers.sync.arrange_project_tasks import arrange_projects_catalogs_and_tasks
from rdmo.projects.tests.helpers.sync.setup import suppress_project_sync


@pytest.mark.django_db
@pytest.mark.parametrize('available', [False, True])
def test_project_tasks_sync_when_updating_available_on_a_task(settings, available):
    projects, _, instances = arrange_projects_catalogs_and_tasks()
    with suppress_project_sync():
        instances[1].available = not available
        instances[1].save()
        if available:
            projects[1].tasks.remove(instances[1])
    settings.PROJECT_TASKS_SYNC = True

    instances[1].available = available
    instances[1].save(update_fields=['available'])

    controlled_ids = [obj.pk for obj in instances.values()]
    assert set(projects[1].tasks.filter(pk__in=controlled_ids)) == ({instances[1]} if available else set())
    assert set(projects[2].tasks.filter(pk__in=controlled_ids)) == {instances[2]}
    assert set(projects[3].tasks.filter(pk__in=controlled_ids)) == {instances[3]}
