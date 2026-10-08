import pytest

from django.contrib.auth.models import Group, Permission, User

from rdmo.projects.models import Membership
from rdmo.projects.sync import filter_projects_for_task_or_view, filter_tasks_or_views_for_project
from rdmo.projects.tests.helpers.sync.setup import arrange_projects_and_instances


def assert_applicability(case, expected):
    # Both directions must independently satisfy the test's explicit expectation.
    selected_instances = filter_tasks_or_views_for_project(case.model, case.project).filter(pk=case.instance.pk)
    selected_projects = filter_projects_for_task_or_view(case.instance).filter(pk=case.project.pk)
    assert set(selected_instances) == ({case.instance} if expected else set())
    assert set(selected_projects) == ({case.project} if expected else set())


@pytest.mark.parametrize('restriction,expected', [('empty', True), ('match', True), ('mismatch', False)])
def test_sync_catalog_contract(sync_case, restriction, expected):
    catalogs = {
        'empty': [], 'match': [sync_case.catalog], 'mismatch': [sync_case.other_catalog],
    }
    sync_case.instance.catalogs.set(catalogs[restriction])
    assert_applicability(sync_case, expected)


@pytest.mark.parametrize('tasks_sync,views_sync', [(False, False), (True, False), (False, True), (True, True)])
@pytest.mark.parametrize('restriction', ['catalogs', 'sites', 'groups'])
def test_sync_arrangement_restores_settings(sync_case, settings, tasks_sync, views_sync, restriction):
    settings.PROJECT_TASKS_SYNC = tasks_sync
    settings.PROJECT_VIEWS_SYNC = views_sync

    projects, instances, _ = arrange_projects_and_instances(sync_case.model, restriction)

    assert settings.PROJECT_TASKS_SYNC is tasks_sync
    assert settings.PROJECT_VIEWS_SYNC is views_sync
    for n, project in projects.items():
        assert set(getattr(project, sync_case.field).all()) == {instances[n]}
        other_field = 'views' if sync_case.field == 'tasks' else 'tasks'
        assert not getattr(project, other_field).exists()


@pytest.mark.parametrize('multisite,restriction,expected', [
    (False, 'empty', True), (False, 'match', True), (False, 'mismatch', False),
    (True, 'empty', False), (True, 'match', True), (True, 'mismatch', False),
])
def test_sync_site_contract(sync_case, settings, multisite, restriction, expected):
    settings.MULTISITE = multisite
    sites = {'empty': [], 'match': [sync_case.site], 'mismatch': [sync_case.other_site]}
    sync_case.instance.sites.set(sites[restriction])
    assert_applicability(sync_case, expected)


@pytest.mark.parametrize('restriction,role,expected', [
    ('empty', 'owner', True),
    ('match', 'owner', True),
    ('mismatch', 'owner', False),
    ('multiple', 'owner', True),
    ('match', 'manager', False),
])
def test_sync_owner_group_contract(sync_case, restriction, role, expected):
    Membership.objects.create(project=sync_case.project, user=sync_case.user, role=role)
    sync_case.user.groups.add(sync_case.group)
    if restriction == 'multiple':
        sync_case.user.groups.add(sync_case.other_group)
    if restriction != 'empty':
        group = sync_case.other_group if restriction == 'mismatch' else sync_case.group
        sync_case.instance.groups.add(group)
    assert_applicability(sync_case, expected)


@pytest.mark.parametrize('mismatch', [None, 'catalogs', 'sites', 'groups'])
@pytest.mark.parametrize('multisite', [False, True])
def test_sync_restrictions_combine_with_and(sync_case, settings, mismatch, multisite):
    settings.MULTISITE = multisite
    Membership.objects.create(project=sync_case.project, user=sync_case.user, role='owner')
    sync_case.user.groups.add(sync_case.group)
    sync_case.instance.groups.add(sync_case.group)
    if mismatch:
        other = {'catalogs': sync_case.other_catalog, 'sites': sync_case.other_site, 'groups': sync_case.other_group}
        getattr(sync_case.instance, mismatch).set([other[mismatch]])
    assert_applicability(sync_case, mismatch is None)


@pytest.mark.parametrize('available,privileges,expected', [
    (True, (), True),
    (False, (), False),
    (False, ('normal',), False),
    (False, ('superuser',), True),
    (False, ('superuser', 'superuser'), True),
    (False, ('superuser', 'normal'), False),
    (False, ('direct',), True),
    (False, ('group',), True),
    (False, ('editor',), True),
    (False, ('reviewer',), True),
    (False, ('wrong-editor',), False),
    (False, ('wrong-reviewer',), False),
])
def test_sync_availability_contract(sync_case, available, privileges, expected):
    sync_case.instance.available = available
    sync_case.instance.save()
    permission = Permission.objects.get(
        content_type__app_label=sync_case.model._meta.app_label,
        codename=f'view_{sync_case.model._meta.model_name}',
    )
    for index, privilege in enumerate(privileges):
        user = User.objects.create(username=f'sync-member-{index}', is_superuser=privilege == 'superuser')
        if privilege == 'direct':
            user.user_permissions.add(permission)
        elif privilege == 'group':
            group = Group.objects.create(name=f'Sync permission group {index}')
            group.permissions.add(permission)
            user.groups.add(group)
        elif privilege in ('editor', 'reviewer'):
            getattr(user.role, privilege).add(sync_case.site)
        elif privilege in ('wrong-editor', 'wrong-reviewer'):
            getattr(user.role, privilege.removeprefix('wrong-')).add(sync_case.other_site)
        Membership.objects.create(project=sync_case.project, user=user, role='guest')
    assert_applicability(sync_case, expected)
