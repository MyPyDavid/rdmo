import pytest

from rdmo.projects.models import Membership
from rdmo.projects.tests.helpers.sync.project_relation_ids import project_relation_ids


@pytest.mark.parametrize('mutation', [
    'catalogs', 'sites', 'groups', 'availability', 'project_catalog', 'membership_save', 'membership_delete',
])
def test_disabled_sync_does_not_change_relations(sync_case, mutation):
    if mutation.startswith('membership'):
        sync_case.user.groups.add(sync_case.group)
        sync_case.instance.groups.add(sync_case.group)
        membership = Membership.objects.create(project=sync_case.project, user=sync_case.user, role='owner')
    getattr(sync_case.project, sync_case.field).add(sync_case.instance)
    initial_state = project_relation_ids(sync_case.field)

    if mutation in ('catalogs', 'sites', 'groups'):
        other = {
            'catalogs': sync_case.other_catalog, 'sites': sync_case.other_site, 'groups': sync_case.other_group,
        }
        getattr(sync_case.instance, mutation).set([other[mutation]])
    elif mutation == 'availability':
        sync_case.instance.available = False
        sync_case.instance.save()
    elif mutation == 'project_catalog':
        sync_case.project.catalog = sync_case.other_catalog
        sync_case.project.save()
    elif mutation == 'membership_save':
        membership.role = 'guest'
        membership.save()
    else:
        membership.delete()

    assert project_relation_ids(sync_case.field) == initial_state
