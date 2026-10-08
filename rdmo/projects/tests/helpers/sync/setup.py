from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.test import override_settings

from rdmo.projects.models import Membership, Project
from rdmo.questions.models import Catalog

from .constants import P_TITLE, one_two_three


def suppress_project_sync():
    """Disable every automatic sync path during setup and restore the caller's settings."""
    return override_settings(PROJECT_TASKS_SYNC=False, PROJECT_VIEWS_SYNC=False)


def arrange_projects_and_instances(model, field):
    """Create three controlled instances without modifying shared fixture objects."""
    name = model._meta.model_name
    with suppress_project_sync():
        catalogs = {
            n: Catalog.objects.create(uri_prefix='http://example.com/sync', uri_path=f'{name}-{field}-{n}')
            for n in one_two_three
        }
        sites = {
            n: Site.objects.create(domain=f'sync-{name}-{field}-{n}.example.com', name=f'Sync site {n}')
            for n in one_two_three
        }
        instances = {
            n: model.objects.create(uri_prefix='http://example.com/sync', uri_path=f'{field}-{n}')
            for n in one_two_three
        }
        projects = {
            n: Project.objects.create(
                title=P_TITLE.format(n),
                catalog=catalogs[n] if field == 'catalogs' else catalogs[1],
                site=sites[n] if field == 'sites' else sites[1],
            )
            for n in one_two_three
        }
        if field == 'catalogs':
            restrictions = catalogs
        elif field == 'sites':
            restrictions = sites
        elif field == 'groups':
            restrictions = {
                n: Group.objects.create(name=f'Sync {name} G{n}') for n in one_two_three
            }
            for n in one_two_three:
                user = User.objects.create(username=f'sync-{name}-owner-{n}')
                user.groups.add(restrictions[n])
                Membership.objects.create(project=projects[n], user=user, role='owner')
        else:
            raise ValueError('field must be catalogs, sites or groups')

        for n in one_two_three:
            getattr(instances[n], field).add(restrictions[n])
            getattr(projects[n], f'{name}s').set([instances[n]])

    return projects, instances, restrictions
