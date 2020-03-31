from __future__ import absolute_import
import json
import jsonschema


class InstanceMixin(object):
    def serialize(self):
        return NotImplementedError("has not implemented the method")

    def deserialize(self, data):
        return NotImplementedError("has not implemented the method")

    def serialize_json(self):
        return self.serialize()

    @classmethod
    def is_json_serializale(cls, value):
        try:
            json.dumps(value)
        except TypeError:
            return False
        return True

    def to_json(self, indent=2):
        return json.dumps(self.serialize_json(), indent=indent)

    def validate(self, schema, raise_exception=True, check_formats=False):
        if raise_exception:
            return schema.validate(self.serialize(), check_formats=check_formats)
        return [
            e
            for e in schema.validation_errors(
                self.serialize(), check_formats=check_formats
            )
        ]


class ValidatorMixin(object):
    def validate(self, instance, schema, draft_cls=None, check_formats=False):
        from .fields import Field

        if isinstance(schema, Field):
            schema = schema.to_json_schema()

        if check_formats:
            return jsonschema.validate(
                instance=instance,
                schema=schema,
                cls=draft_cls,
                format_checker=jsonschema.draft7_format_checker,
            )

        return jsonschema.validate(instance=instance, schema=schema, cls=draft_cls,)

    def validation_errors(self, instance, schema, draft_cls=None, check_formats=False):
        from .fields import Field

        if isinstance(schema, Field):
            schema = schema.to_json_schema()
        if not draft_cls:
            draft_cls = jsonschema.validators.validator_for(schema)
        if check_formats:
            return draft_cls(schema).iter_errors(instance)
        return draft_cls(
            schema, format_checker=jsonschema.draft7_format_checker
        ).iter_errors(instance)


class JsonSchemableMixin(object):

    _JSON_SCHEMA_TYPE = u"object"

    def to_json_schema(self, title=None, description=None):
        schema = {u"type": self._JSON_SCHEMA_TYPE}
        if title is not None:
            schema[u"title"] = title
        if description is not None:
            schema[u"description"] = description
        return schema
