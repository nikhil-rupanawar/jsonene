from .fields import Field


class OperatorField(Field):
    pass


class Of(OperatorField):
    def __init__(self, *types, required=True, name=None, title=None, description=None):
        super().__init__(
            required=required, name=name, title=title, description=description
        )
        _types = []
        for _type in types:
            if not isinstance(_type, Field):
                _type = _type()
            _types.append(_type)
        self._types = _types
        self.required = required

    def to_json_schema(self):
        schema = []
        for t in self._types:
            schema.append(t.to_json_schema())
        return {self.operator: schema}


class AnyOf(Of):
    operator = "anyOf"


class AllOf(Of):
    operator = "allOf"


class OneOf(Of):
    operator = "oneOf"


class Not(Of):
    operator = "not"
