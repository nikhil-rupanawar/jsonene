from __future__ import absolute_import
import json
from .mixins import InstanceMixin


class BaseInstance(InstanceMixin):
    def __init__(self, schema):
        self._schema = schema

    @property
    def schema_json(self):
        return self.schema.to_json_schema()

    @property
    def schema(self):
        return self._schema

    @schema.setter
    def schema(self, schema):
        self._schema = schema

    @property
    def errors(self):
        return [e.message for e in self.exceptions]

    @property
    def exceptions(self):
        return self.validate(raise_exception=False)

    def validate(self, raise_exception=True, check_formats=False):
        return super(BaseInstance, self).validate(
            self.schema, raise_exception=raise_exception, check_formats=check_formats
        )

    def __repr__(self):
        rpr = super(BaseInstance, self).__repr__()
        if self.schema:
            return "[{rpr} of <Schema {name}.{classname}>]".format(
                rpr=rpr,
                name=__name__,
                classname=self.schema.__class__.__name__
            )
        return rpr


class SingleValueInstance(BaseInstance):
    def __init__(self, instance, schema):
        super(SingleValueInstance, self).__init__(schema)
        self._instance = instance

    def serialize(self):
        if isinstance(self._instance, BaseInstance):
            return self._instance.serialize()
        return self._instance

    def deserialize(self, data):
        return data
