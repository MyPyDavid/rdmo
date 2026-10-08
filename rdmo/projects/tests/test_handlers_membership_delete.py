import pytest

from django.contrib.auth.models import User

from rdmo.projects.models import Membership, Project
from rdmo.projects.sync import sync_tasks_or_views_for_project
from rdmo.projects.tests.helpers.sync.project_relation_ids import project_relation_ids


def delete_member(membership, mode):
    if mode == 'instance':
        membership.delete()
    elif mode == 'queryset':
        Membership.objects.filter(pk=membership.pk).delete()
    else:
        membership.user.delete()


@pytest.mark.parametrize('mode', ['instance', 'queryset', 'user'])
def test_membership_delete_unprivileged_member_restores_instance(sync_case, settings, mode):
    sync_case.instance.available = False
    sync_case.instance.save()
    sync_case.user.is_superuser = True
    sync_case.user.save()
    Membership.objects.create(project=sync_case.project, user=sync_case.user, role='owner')
    normal_user = User.objects.create(username='sync-ordinary-member')
    membership = Membership.objects.create(project=sync_case.project, user=normal_user, role='guest')

    setattr(settings, f'PROJECT_{sync_case.field.upper()}_SYNC', True)
    sync_tasks_or_views_for_project(sync_case.model, sync_case.project)
    relation = getattr(sync_case.project, sync_case.field)
    assert sync_case.instance not in relation.all()

    delete_member(membership, mode)
    assert sync_case.instance in relation.all()


@pytest.mark.parametrize('mode', ['instance', 'queryset', 'user'])
def test_membership_delete_final_privileged_member_removes_instance(sync_case, settings, mode):
    sync_case.instance.available = False
    sync_case.instance.save()
    sync_case.user.is_superuser = True
    sync_case.user.save()
    membership = Membership.objects.create(project=sync_case.project, user=sync_case.user, role='owner')

    setattr(settings, f'PROJECT_{sync_case.field.upper()}_SYNC', True)
    sync_tasks_or_views_for_project(sync_case.model, sync_case.project)
    relation = getattr(sync_case.project, sync_case.field)
    assert sync_case.instance in relation.all()

    delete_member(membership, mode)
    assert sync_case.instance not in relation.all()


@pytest.mark.parametrize('mode', ['instance', 'queryset', 'user'])
def test_membership_delete_owner_recalculates_group_restrictions(sync_case, settings, mode):
    sync_case.user.groups.add(sync_case.group)
    sync_case.instance.groups.add(sync_case.group)
    membership = Membership.objects.create(project=sync_case.project, user=sync_case.user, role='owner')

    setattr(settings, f'PROJECT_{sync_case.field.upper()}_SYNC', True)
    sync_tasks_or_views_for_project(sync_case.model, sync_case.project)
    relation = getattr(sync_case.project, sync_case.field)
    assert sync_case.instance in relation.all()

    delete_member(membership, mode)
    assert sync_case.instance not in relation.all()


@pytest.mark.parametrize('mode', ['instance', 'queryset'])
def test_project_delete_does_not_recreate_sync_relations(sync_case, settings, mode):
    Membership.objects.create(project=sync_case.project, user=sync_case.user, role='owner')
    # Leave an applicable instance missing so an unguarded delete handler would add it.
    settings.PROJECT_TASKS_SYNC = True
    settings.PROJECT_VIEWS_SYNC = True
    pk = sync_case.project.pk
    initial_tasks = project_relation_ids('tasks')
    initial_views = project_relation_ids('views')

    if mode == 'instance':
        sync_case.project.delete()
    else:
        Project.objects.filter(pk=pk).delete()

    assert not Project.objects.filter(pk=pk).exists()
    assert project_relation_ids('tasks') == {key: value for key, value in initial_tasks.items() if key != pk}
    assert project_relation_ids('views') == {key: value for key, value in initial_views.items() if key != pk}
