import json


class BaseInstance:
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

    def serialize(self):
        return NotImplementedError(f"{self.__class__}: has not implemented")

    @classmethod
    def deserialize(self, data):
        return NotImplementedError(f"{self.__class__}: has not implemented")

    def serialize_json(self):
        return self.serialize()

    def to_json(self, indent=2):
        return json.dumps(self.serialize_json(), indent=indent)

    dumps = to_json

    def validate(self, raise_exception=True):
        if raise_exception:
            return self.schema.validate(self.serialize())
        return [e for e in self.schema.validation_errors(self.serialize())]

    def __repr__(self):
        rpr = super().__repr__()
        if self.schema:
            return f"[{rpr} of <Schema {__name__}.{self.schema.__class__.__name__}>]"
        return rpr

    @classmethod
    def _confirm_json_loaded(cls, data):
        assert isinstance(data, (bytes, str))
        if isinstance(data, (str, bytes)):
            data = json.loads(data)
        return data


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
