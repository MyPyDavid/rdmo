from rdmo.projects.models import Project

PROJECT_SHOW_TEMPLATE = 'Project "{}" [id={}]:'


def assert_sync_projects_show_has_output(out_lines: list[str]):
    """Verify each Project's catalog, sorted relations, and empty sections."""
    for project in Project.objects.all():
        header = PROJECT_SHOW_TEMPLATE.format(project.title, project.pk)
        start = out_lines.index(header) + 1
        end = start
        while end < len(out_lines) and out_lines[end].strip():
            end += 1
        block = out_lines[start:end]
        assert f'- Catalog: {project.catalog.uri}' in block

        actual = {'tasks': [], 'views': []}
        current_field = None
        for line in block:
            if line == '- Tasks:':
                current_field = 'tasks'
            elif line == '- Views:':
                current_field = 'views'
            elif line.startswith('  - '):
                assert current_field is not None, f'Missing relation heading for Project {project.pk}'
                actual[current_field].append(line.removeprefix('  - '))

        for field in ('tasks', 'views'):
            expected = sorted(getattr(project, field).values_list('uri', flat=True))
            assert actual[field] == expected, f'Project {project.pk} {field} output differs from its relations'
            assert (f'- {field.title()}:' in block) == bool(expected)
