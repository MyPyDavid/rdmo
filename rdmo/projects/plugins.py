from rdmo.core.plugins import Plugin


class ValueValidationPlugin(Plugin):

    def validate_value(self, data, serializer):
        raise NotImplementedError
