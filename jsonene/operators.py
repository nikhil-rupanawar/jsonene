import inspect
from .fields import BaseSchemaField, ObjectType


class BaseOperatorSchemaField(BaseSchemaField):
    OPERATOR = ""

    def __init__(self, *types, required=True, name=None, title=None, description=None):
        super().__init__(
            required=required, name=name, title=title, description=description
        )
        _types = []
        for _type in types:
            is_class = inspect.isclass(_type)
            if is_class and issubclass(_type, ObjectType):
                _type = _type.asField()
            elif isinstance(_type, BaseSchemaField):
                _type = _type
            elif is_class and issubclass(_type, BaseSchemaField):
                _type = _type()
            else:
                assert not is_class
                _type = _type
            _types.append(_type)
        self._types = _types

    def to_json_schema(self):
        schema = []
        for t in self._types:
            if isinstance(t, BaseSchemaField):
                schema.append(t.to_json_schema())
            else:
                schema.append(t)
        return {self.OPERATOR: schema}


class AnyOf(BaseOperatorSchemaField):
    OPERATOR = "anyOf"


class AllOf(BaseOperatorSchemaField):
    OPERATOR = "allOf"


class OneOf(BaseOperatorSchemaField):
    OPERATOR = "oneOf"


class Not(BaseOperatorSchemaField):
    OPERATOR = "not"

    def __init__(self, _type, *args, **kwargs):
        super().__init__(*(_type,), *args, **kwargs)
