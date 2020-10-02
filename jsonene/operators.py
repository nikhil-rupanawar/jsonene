from .fields import BaseField 
from .exceptions import ValidationError


class BaseOperatorField(BaseField):
    OPERATOR = ''
    def __init__(self, *types):
        self._types = types

    class Schema(BaseField.Schema):
        def __init__(
            self,
            field_class,
            *types,
            required=True,
            name=None,
            title=None,
            description=None
        ):
            super().__init__(
                field_class,
                required=required,
                name=name,
                title=title,
                description=description
            )
            _types = []
            for _type in types:
                assert issubclass(_type, BaseField) is True
                _types.append(_type.asField())
            self._types = _types

        def from_json(self, data):
            return _type.from_json(data)

        def to_json_schema(self):
            schema = []
            for t in self._types:
                schema.append(t.to_json_schema())
            return {self.field_class.OPERATOR: schema}

    def asField(self, *args, **kwargs):
        return self.Schema(
            self.__class__,
            *self._types,
            *args,
            **kwargs
        )


class AnyOf(BaseOperatorField):
    OPERATOR = "anyOf"


class AllOf(BaseOperatorField):
    OPERATOR = "allOf"


class OneOf(BaseOperatorField):
    OPERATOR = "oneOf"


class Not(BaseOperatorField):
    OPERATOR = "not"
    class Schema(BaseOperatorField.Schema):
        def __init__(self, _type, *args, **kwargs):
            super().__init__(
                *(_type,),
                *args,
                **kwargs
            )
