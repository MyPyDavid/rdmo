from rdmo.tasks.models import Task

from .setup import arrange_projects_and_instances


def arrange_projects_catalogs_and_tasks():
    projects, tasks, catalogs = arrange_projects_and_instances(Task, 'catalogs')
    return projects, catalogs, tasks


def arrange_projects_sites_and_tasks():
    return arrange_projects_and_instances(Task, 'sites')


def arrange_projects_groups_and_tasks():
    return arrange_projects_and_instances(Task, 'groups')
