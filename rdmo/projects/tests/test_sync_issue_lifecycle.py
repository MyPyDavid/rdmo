from rdmo.projects.models import Integration, Issue, IssueResource
from rdmo.projects.tests.helpers.sync.arrange_project_tasks import arrange_projects_catalogs_and_tasks


def test_task_reapplicability_creates_issue_with_default_state(db, settings):
    projects, catalogs, tasks = arrange_projects_catalogs_and_tasks()
    settings.PROJECT_TASKS_SYNC = True
    issue = Issue.objects.get(project=projects[1], task=tasks[1])
    old_pk = issue.pk
    issue.status = Issue.ISSUE_STATUS_CLOSED
    issue.save()
    integration = Integration.objects.create(project=projects[1], title='Sync integration', provider_key='simple')
    resource = IssueResource.objects.create(issue=issue, integration=integration, url='http://example.com/resource')
    resource_pk = resource.pk

    tasks[1].catalogs.set([catalogs[2]])
    assert not Issue.objects.filter(pk=old_pk).exists()
    assert not IssueResource.objects.filter(pk=resource_pk).exists()

    tasks[1].catalogs.set([catalogs[1]])
    restored = Issue.objects.get(project=projects[1], task=tasks[1])
    assert restored.pk != old_pk
    assert restored.status == Issue.ISSUE_STATUS_OPEN
    assert not restored.resources.exists()
