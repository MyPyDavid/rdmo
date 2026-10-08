from types import SimpleNamespace

import pytest

from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site

from rdmo.projects.models import Project
from rdmo.projects.tests.helpers.sync.setup import suppress_project_sync
from rdmo.questions.models import Catalog
from rdmo.tasks.models import Task
from rdmo.views.models import View


@pytest.fixture(params=[Task, View], ids=['tasks', 'views'])
def sync_case(db, settings, request):
    """A local selector/lifecycle scenario alongside the complete shared fixtures."""
    settings.PROJECT_TASKS_SYNC = False
    settings.PROJECT_VIEWS_SYNC = False
    settings.MULTISITE = False
    model = request.param
    with suppress_project_sync():
        catalog = Catalog.objects.create(uri_prefix='http://example.com/sync', uri_path='catalog')
        other_catalog = Catalog.objects.create(uri_prefix='http://example.com/sync', uri_path='other-catalog')
        site = Site.objects.create(domain='sync.example.com', name='Sync')
        other_site = Site.objects.create(domain='other-sync.example.com', name='Other sync')
        group = Group.objects.create(name='Sync matching group')
        other_group = Group.objects.create(name='Sync other group')
        user = User.objects.create(username='sync-owner')
        project = Project.objects.create(title='Sync contract project', catalog=catalog, site=site)
        instance = model.objects.create(uri_prefix='http://example.com/sync', uri_path='instance')
        instance.catalogs.add(catalog)
        instance.sites.add(site)

    return SimpleNamespace(
        model=model, field=f'{model._meta.model_name}s', project=project, instance=instance,
        catalog=catalog, other_catalog=other_catalog, site=site, other_site=other_site,
        group=group, other_group=other_group, user=user,
    )
