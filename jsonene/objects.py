import json


class BaseInstance:
    def __init__(self, schema):
        self._schema = schema

    def to_json(self, indent=2):
        return json.dumps(self.serialize(), indent=indent)

    @property
    def schema_json(self):
        return self.schema.to_json_schema()

    @property
    def schema(self):
        return self._schema

    @property
    def errors(self):
        return [e.message for e in self.exceptions]

    @property
    def exceptions(self):
        return self.validate(raise_exception=False)

    def serialize(self):
        return NotImplementedError(f"{self.__class__}: has not implemented")

    def validate(self, raise_exception=True):
        if raise_exception:
            return self.schema.validate(self.serialize())
        return [e for e in self.schema.validation_errors(self.serialize())]

    def __repr__(self):
        rpr = super().__repr__()
        if self.schema:
            return f"[{rpr} of <Schema {__name__}.{self.schema.__class__.__name__}>]"
        return rpr


class SingleValueInstance(BaseInstance):
    def __init__(self, instance, schema):
        super().__init__(schema)
        self._instance = instance

    def serialize(self):
        if isinstance(self._instance, BaseInstance):
            return self._instance.serialize()
        return self._instance
