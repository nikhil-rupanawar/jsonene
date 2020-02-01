import json


class BaseInstance:
    def __init__(self, schema=None):
        self._schema = schema

    def to_json(self, indent=2):
        return json.dumps(self.serialize(), indent=indent)

    @property
    def schema_json(self):
        return self.schema.to_json_schema()

    @property
    def schema(self):
        return self._schema

    def serialize(self):
        return NotImplementedError(f"{self.__class__}: Not implemented")

    def validate(self, schema=None):
        schema = schema or self.schema
        assert schema is not None
        return self.schema.validate(self.serialize())

    def validation_errors(self, schema=None):
        schema = schema or self.schema
        assert schema is not None
        return self.schema.validation_errors(self.serialize())

    def validation_error_messages(self, schema=None):
        schema = schema or self.schema
        return [e.message for e in self.validation_errors()]

    def __repr__(self):
        rpr = super().__repr__()
        if self.schema:
            return f"[{rpr} of <Schema {__name__}.{self.schema.__class__.__name__}>]"
        return rpr


class SingleValueInstance(BaseInstance):
    def __init__(self, instance, schema=None):
        super().__init__(schema=schema)
        self._instance = instance

    def serialize(self):
        return self._instance
