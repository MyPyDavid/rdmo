from enum import Enum


class PluginType(str, Enum):
    PROJECT_EXPORT = "project_export"
    PROJECT_IMPORT = "project_import"
    PROJECT_ISSUE_PROVIDER = "project_issue_provider"
    OPTIONSET_PROVIDER = "optionset_provider"


PLUGIN_TYPE_TO_SETTING_KEY = {
    PluginType.PROJECT_EXPORT: "PROJECT_EXPORTS",
    PluginType.PROJECT_IMPORT: "PROJECT_IMPORTS",
    PluginType.PROJECT_ISSUE_PROVIDER: "PROJECT_ISSUE_PROVIDERS",
}
