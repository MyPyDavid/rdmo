import logging

from django.conf import settings

from rdmo.projects.models import Project
from rdmo.projects.sync import filter_tasks_or_views_for_project
from rdmo.tasks.models import Task
from rdmo.views.models import View

logger = logging.getLogger(__name__)


def assert_other_tasks_are_consistent_with_sync_filter(project, task_ids):
    """Check tasks outside the controlled scenario against the sync filter."""
    actual = set(project.tasks.exclude(pk__in=task_ids).values_list('pk', flat=True))
    expected = set(
        filter_tasks_or_views_for_project(Task, project).exclude(pk__in=task_ids).values_list('pk', flat=True)
    )
    assert actual == expected, (
        f'Project {project.pk} other tasks: missing {sorted(expected - actual)}, unexpected {sorted(actual - expected)}'
    )


def assert_other_views_are_consistent_with_sync_filter(project, view_ids):
    """Check views outside the controlled scenario against the sync filter."""
    actual = set(project.views.exclude(pk__in=view_ids).values_list('pk', flat=True))
    expected = set(
        filter_tasks_or_views_for_project(View, project).exclude(pk__in=view_ids).values_list('pk', flat=True)
    )
    assert actual == expected, (
        f'Project {project.pk} other views: missing {sorted(expected - actual)}, unexpected {sorted(actual - expected)}'
    )


def assert_other_projects_unchanged(other_projects, initial_tasks_state):
    for other_project in other_projects:
        assert set(other_project.tasks.values_list('id', flat=True)) == set(initial_tasks_state[other_project.id])


def assert_all_projects_are_synced_with_instance_m2m_field(instance: Task | View, field: str) -> None:
    # View/Task .catalogs, .sites or .groups
    instance_field = getattr(instance, field)

    if field == 'sites':
        instance_project_field = 'site'
    elif field == 'catalogs':
        instance_project_field = 'catalog'
    elif field == 'groups':
        instance_project_field = 'groups'
    else:
        raise RuntimeError("field needs to be 'site', 'catalog' or 'groups'")

    if isinstance(instance, Task):
        m2m_field = 'tasks'
    elif isinstance(instance, View):
        m2m_field = 'views'
    else:
        raise RuntimeError('instance needs to be a Task or View')

    for project in Project.objects.all():
        # Project tasks or views
        project_instances = getattr(project, m2m_field).all()
        project_has_instance = instance in project_instances

        # (e.g. Task/View has no catalogs / no sites / no groups)
        if not instance_field.exists():
            if instance_project_field == 'site' and settings.MULTISITE:
                # MULTISITE=True and no sites on the instance:
                project_should_have_instance = False
            else:
                # For catalogs and groups, and for sites when MULTISITE=False:
                #   empty field means "applies to all projects"
                project_should_have_instance = True
        else:
            if instance_project_field == 'catalog':
                project_should_have_instance = bool(project.catalog in instance_field.all())
            elif instance_project_field == 'site':
                project_should_have_instance = bool(project.site in instance_field.all())
            elif instance_project_field == 'groups':
                instance_ids = set(instance_field.values_list('id', flat=True))
                project_groups_ids = {group.id for group in getattr(project, instance_project_field)}
                # Any overlap with the project owners' groups is sufficient.
                project_should_have_instance = bool(project_groups_ids & instance_ids)
            else:
                raise ValueError("Project field not recognized, should be 'site', 'catalog' or 'groups'")

        if project_should_have_instance:
            if not project_has_instance:
                logger.debug(
                    '%s missing in %s with %s match [%s]',
                    instance,
                    instance_project_field,
                    project,
                    m2m_field
                )
            assert project_has_instance, (
                f"{instance} missing in {project} with matching {instance_project_field}"
            )
        else:
            if project_has_instance:
                logger.debug(
                    '%s wrongly assigned to %s with %s mismatch [%s]',
                    instance,
                    instance_project_field,
                    project,
                    m2m_field
                )
            assert not project_has_instance, (
                f"{instance} wrongly assigned to {project} with mismatched {instance_project_field} [{m2m_field}] "
            )
