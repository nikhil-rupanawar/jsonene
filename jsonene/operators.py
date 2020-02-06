from .fields import Field
from .exceptions import ValidationError


class OperatorField(Field):
    pass


class Of(OperatorField):
    def __init__(self, *types, required=True, name=None, title=None, description=None):
        super().__init__(
            required=required, name=name, title=title, description=description
        )
        _types = []
        for _type in types:
            assert isinstance(_types, Of) is False
            try:
                if issubclass(_type, Field):
                    _type = _type()
            except:
                pass
            _types.append(_type)
        self._types = _types

    def to_json_schema(self):
        schema = []
        for t in self._types:
            schema.append(t.to_json_schema())
        return {self.operator: schema}

    def from_json(self, data):
        _type = None
        for t in self._types:
            try:
                t.validate(data)
                _type = t
                break
            except ValidationError:
                pass
        if _type is None:
            return data
        return _type.from_json(data)


class AnyOf(Of):
    operator = "anyOf"


class AllOf(Of):
    operator = "allOf"


class OneOf(Of):
    operator = "oneOf"


class Not(Of):
    operator = "not"

    def __init__(self, _type, required=True, name=None, title=None, description=None):
        # No nested
        assert (isinstaissubclass(_type, Field)) is True
        assert isinstance(_type, Of) is False
        super().__init__(
            required=required, name=name, title=title, description=description
        )
        if issubclass(_type, Field):
            _type = _type()
        self._type = _type

    def to_json_schema(self):
        return {self.operator: self._type.to_json_schema()}

    def from_json(self, data):
        try:
            self._type.validate(data)
            return _type.from_json(data)
        except ValidationError:
            return data
