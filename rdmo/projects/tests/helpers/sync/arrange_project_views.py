from rdmo.views.models import View

from .setup import arrange_projects_and_instances


def arrange_projects_catalogs_and_views():
    projects, views, catalogs = arrange_projects_and_instances(View, 'catalogs')
    return projects, catalogs, views


def arrange_projects_sites_and_views():
    return arrange_projects_and_instances(View, 'sites')


def arrange_projects_groups_and_views():
    return arrange_projects_and_instances(View, 'groups')
