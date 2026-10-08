from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from rdmo.tasks.models import Task
from rdmo.views.models import View

from ..models import Membership, Project
from ..sync import sync_tasks_or_views_for_project


@receiver(post_save, sender=Membership)
def post_save_membership_sync_tasks(sender, instance, created, raw, update_fields, **kwargs):
    if settings.PROJECT_TASKS_SYNC and not raw:
        sync_tasks_or_views_for_project(Task, instance.project)


@receiver(post_save, sender=Membership)
def post_save_membership_sync_views(sender, instance, created, raw, update_fields, **kwargs):
    if settings.PROJECT_VIEWS_SYNC and not raw:
        sync_tasks_or_views_for_project(View, instance.project)


@receiver(post_delete, sender=Membership)
def post_delete_membership_sync_instances(sender, instance, origin=None, **kwargs):
    # Project cascades must not recreate relations while the Project is being deleted.
    if isinstance(origin, Project) or getattr(origin, 'model', None) is Project:
        return

    if settings.PROJECT_TASKS_SYNC:
        sync_tasks_or_views_for_project(Task, instance.project)
    if settings.PROJECT_VIEWS_SYNC:
        sync_tasks_or_views_for_project(View, instance.project)
