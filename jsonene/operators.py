from __future__ import absolute_import
from .fields import Field
from .exceptions import ValidationError


class OperatorField(Field):
    pass


class Of(OperatorField):
    def __init__(self, *types, **_3to2kwargs):
        if u'description' in _3to2kwargs: description = _3to2kwargs[u'description']; del _3to2kwargs[u'description']
        else: description = None
        if u'title' in _3to2kwargs: title = _3to2kwargs[u'title']; del _3to2kwargs[u'title']
        else: title = None
        if u'name' in _3to2kwargs: name = _3to2kwargs[u'name']; del _3to2kwargs[u'name']
        else: name = None
        if u'required' in _3to2kwargs: required = _3to2kwargs[u'required']; del _3to2kwargs[u'required']
        else: required = True
        super(Of, self).__init__(
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
    operator = u"anyOf"


class AllOf(Of):
    operator = u"allOf"


class OneOf(Of):
    operator = u"oneOf"


class Not(Of):
    operator = u"not"

    def __init__(self, _type, required=True, name=None, title=None, description=None):
        # No nested
        assert (isinstaissubclass(_type, Field)) is True
        assert isinstance(_type, Of) is False
        super(Not, self).__init__(
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
