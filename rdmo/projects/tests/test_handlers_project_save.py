import pytest

from rdmo.projects.tests.helpers.sync.arrange_project_tasks import arrange_projects_catalogs_and_tasks
from rdmo.projects.tests.helpers.sync.arrange_project_views import arrange_projects_catalogs_and_views
from rdmo.projects.tests.helpers.sync.assert_project_views_or_tasks import (
    assert_other_tasks_are_consistent_with_sync_filter,
    assert_other_views_are_consistent_with_sync_filter,
)
from rdmo.projects.tests.helpers.sync.project_relation_ids import project_relation_ids


@pytest.mark.django_db
def test_project_tasks_sync_when_changing_a_catalog_on_a_project(settings):
    settings.PROJECT_TASKS_SYNC = True

    P, C, T = arrange_projects_catalogs_and_tasks()
    task_ids = [task.pk for task in T.values()]
    initial_state = project_relation_ids('tasks')
    # === Initial state ===
    # P1 (with C1) has T1 among the controlled tasks, etc.
    assert set(P[1].tasks.filter(pk__in=task_ids)) == {T[1]}
    assert set(P[2].tasks.filter(pk__in=task_ids)) == {T[2]}
    assert set(P[3].tasks.filter(pk__in=task_ids)) == {T[3]}
    # Act: change catalog on P1 and P2
    P[1].catalog = C[2]
    P[1].save()
    P[2].catalog = C[1]
    P[2].save()
    # Assert: T1 and T2 were swapped
    assert set(P[1].tasks.filter(pk__in=task_ids)) == {T[2]}
    assert set(P[2].tasks.filter(pk__in=task_ids)) == {T[1]}
    assert set(P[3].tasks.filter(pk__in=task_ids)) == {T[3]}

    for project in (P[1], P[2]):
        assert_other_tasks_are_consistent_with_sync_filter(project, task_ids)

    final_state = project_relation_ids('tasks')
    for pk, task_ids_before in initial_state.items():
        if pk not in (P[1].pk, P[2].pk):
            assert final_state[pk] == task_ids_before


@pytest.mark.django_db
def test_project_views_sync_when_changing_a_catalog_on_a_project(settings):
    settings.PROJECT_VIEWS_SYNC = True

    P, C, V = arrange_projects_catalogs_and_views()
    view_ids = [view.pk for view in V.values()]
    initial_state = project_relation_ids('views')
    # === Initial state ===
    # P1 (with C1) has V1, etc..
    assert set(P[1].views.filter(pk__in=view_ids)) == {V[1]}
    assert set(P[2].views.filter(pk__in=view_ids)) == {V[2]}
    assert set(P[3].views.filter(pk__in=view_ids)) == {V[3]}
    # Act: change catalog on P1 and P2
    P[1].catalog = C[2]
    P[1].save()
    P[2].catalog = C[1]
    P[2].save()
    # Assert: V1 and V2 were swapped
    assert set(P[1].views.filter(pk__in=view_ids)) == {V[2]}
    assert set(P[2].views.filter(pk__in=view_ids)) == {V[1]}
    assert set(P[3].views.filter(pk__in=view_ids)) == {V[3]}

    for project in (P[1], P[2]):
        assert_other_views_are_consistent_with_sync_filter(project, view_ids)

    final_state = project_relation_ids('views')
    for pk, view_ids_before in initial_state.items():
        if pk not in (P[1].pk, P[2].pk):
            assert final_state[pk] == view_ids_before
