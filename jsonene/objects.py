import json
from .mixins import InstanceMixin


class BaseInstance(InstanceMixin):

    @property
    def schema_json(self):
        return self.to_json_schema()

    @property
    def errors(self):
        return [e.message for e in self.exceptions]

    @property
    def exceptions(self):
        return self.validate(raise_exception=False)

    def validate(self, raise_exception=True, check_formats=False):
        return super().validate(
            self.schema, raise_exception=raise_exception, check_formats=check_formats
        )


class SingleValueInstance(BaseInstance):
    def __init__(self, instance, schema):
        super().__init__(schema)
        self._instance = instance

    def serialize(self):
        if isinstance(self._instance, BaseInstance):
            return self._instance.serialize()
        return self._instance

    def deserialize(self, data):
        return data
