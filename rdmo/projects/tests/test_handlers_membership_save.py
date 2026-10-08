from rdmo.projects.models import Membership
from rdmo.projects.tests.helpers.sync.setup import suppress_project_sync


def test_project_membership_creation_restores_unavailable_instance(sync_case, settings):
    with suppress_project_sync():
        sync_case.instance.available = False
        sync_case.instance.save()
        sync_case.user.is_superuser = True
        sync_case.user.save()

    setattr(settings, f'PROJECT_{sync_case.field.upper()}_SYNC', True)
    relation = getattr(sync_case.project, sync_case.field)
    assert sync_case.instance not in relation.all()

    Membership.objects.create(project=sync_case.project, user=sync_case.user, role='guest')
    assert sync_case.instance in relation.all()


def test_project_membership_role_change_recalculates_owner_groups(sync_case, settings):
    with suppress_project_sync():
        sync_case.user.groups.add(sync_case.group)
        sync_case.instance.groups.add(sync_case.group)
        membership = Membership.objects.create(project=sync_case.project, user=sync_case.user, role='guest')

    setattr(settings, f'PROJECT_{sync_case.field.upper()}_SYNC', True)
    relation = getattr(sync_case.project, sync_case.field)
    assert sync_case.instance not in relation.all()

    membership.role = 'owner'
    membership.save(update_fields=['role'])
    assert sync_case.instance in relation.all()
