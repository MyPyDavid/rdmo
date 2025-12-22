import pytest

from rdmo.config.constants import PluginType
from rdmo.config.models import Plugin
from rdmo.config.plugin_types import detect_plugin_type
from rdmo.projects.models import Project


def test_detect_plugin_type_internal_plugins():
    assert detect_plugin_type("rdmo.projects.exports.Export") == PluginType.PROJECT_EXPORT
    assert detect_plugin_type("rdmo.projects.imports.Import") == PluginType.PROJECT_IMPORT
    assert detect_plugin_type("rdmo.projects.providers.IssueProvider") == PluginType.PROJECT_ISSUE_PROVIDER
    assert detect_plugin_type("rdmo.options.providers.Provider") == PluginType.OPTIONSET_PROVIDER

@pytest.mark.django_db
def test_plugin_create_and_render():
    # Arrange: create the Plugin model instance
    project = Project.objects.get(id=1)
    instance = Plugin.objects.create(
        uri_prefix="https://example.org/terms",
        uri_path="test-plugins-export",
        python_path="plugins.project_export.exports.SimpleExportPlugin",
        title_lang1="Test Export Plugin",
        title_lang2="Test Export Plugin(lang2)",
        available=True,
        plugin_settings={"foo": "bar"},
    )

    # get class and initialize like a legacy style plugin
    export_plugin = instance.initialize_class()
    export_plugin.project = project
    export_plugin.snapshot = None
    # Call export (render) and assert behavior
    assert instance.plugin_type == PluginType.PROJECT_EXPORT
    response = export_plugin.render()
    assert response.status_code == 200
    text = response.content.decode()
    assert text,"response of test export plugin is empty"


@pytest.mark.django_db
def test_plugin_save_sets_issue_provider_type():
    instance = Plugin.objects.create(
        uri_prefix="https://example.org/terms",
        uri_path="test-plugins-issue-provider",
        python_path="plugins.project_issue_providers.providers.SimpleIssueProvider",
        title_lang1="Test Issue Provider",
        title_lang2="Test Issue Provider(lang2)",
        available=True,
        plugin_settings={"foo": "bar"},
    )

    plugin = Plugin.objects.get(pk=instance.pk)
    assert plugin.plugin_type == PluginType.PROJECT_ISSUE_PROVIDER


@pytest.mark.django_db
def test_plugin_str_shows_uri():
    instance = Plugin.objects.create(
        uri_prefix="https://example.org/terms",
        uri_path="plugins/plugin-str-test",
        python_path="plugins.project_export.exports.SimpleExportPlugin",
        title_lang1="String repr plugin",
        available=True,
    )

    assert str(instance) == instance.uri


@pytest.mark.django_db
def test_filter_for_project_respects_availability():
    project = Project.objects.get(id=1)

    allowed = Plugin.objects.create(
        uri_prefix="https://example.org/terms",
        uri_path="plugins/available-plugin",
        python_path="plugins.project_export.exports.SimpleExportPlugin",
        title_lang1="Available plugin",
        available=True,
    )
    allowed.catalogs.add(project.catalog)
    allowed.sites.add(project.site)

    blocked = Plugin.objects.create(
        uri_prefix="https://example.org/terms",
        uri_path="plugins/unavailable-plugin",
        python_path="plugins.project_export.exports.SimpleExportPlugin",
        title_lang1="Unavailable plugin",
        available=False,
    )
    blocked.catalogs.add(project.catalog)
    blocked.sites.add(project.site)

    qs = Plugin.objects.filter_for_project(project)

    assert allowed in qs
    assert blocked not in qs
