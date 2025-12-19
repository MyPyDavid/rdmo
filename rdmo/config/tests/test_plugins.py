import pytest

from rdmo.config.models import Plugin
from rdmo.config.plugin_type_constants import PluginType
from rdmo.config.plugin_types import detect_plugin_type
from rdmo.projects.models import Project


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
    assert instance.plugin_type == "project_export"
    response = export_plugin.render()
    assert response.status_code == 200
    text = response.content.decode()
    assert text,"response of test export plugin is empty"


@pytest.mark.parametrize(
    "python_path, expected",
    [
        ("plugins.project_export.exports.SimpleExportPlugin", PluginType.PROJECT_EXPORT.value),
        ("rdmo.projects.imports.RDMOXMLImport", PluginType.PROJECT_IMPORT.value),
        ("plugins.project_issue_providers.providers.SimpleIssueProvider", PluginType.PROJECT_ISSUE_PROVIDER.value),
        ("plugins.optionset_providers.providers.SimpleProvider", PluginType.OPTIONSET_PROVIDER.value),
    ]
)
def test_detect_plugin_type_known_plugins(python_path, expected):
    assert detect_plugin_type(python_path) == expected


@pytest.mark.django_db
def test_plugin_save_sets_issue_provider_type():
    instance = Plugin.objects.create(
        uri_prefix="https://example.org/terms",
        uri_path="test-plugins-issue-provider",
        python_path="plugins.project_issue_providers.providers.SimpleIssueProvider",
        title_lang1="Test Issue Provider",
        available=True,
        plugin_settings={"foo": "bar"},
    )

    assert instance.plugin_type == PluginType.PROJECT_ISSUE_PROVIDER.value
