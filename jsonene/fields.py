import jsonschema
import abc
import json
import inspect
import enum
from collections.abc import Iterable

from functools import partial
from jsonschema.validators import validator_for
from jsonschema import draft7_format_checker
from .mixins import ValidatorMixin, JsonSchemableMixin, InstanceMixin
from .objects import BaseInstance, SingleValueInstance

# base class for all fields
class Field(JsonSchemableMixin, ValidatorMixin):
    _JSON_SCHEMA_TYPE = ""

    class Meta:
        field_dependencies = []

    def __init__(
        self, required=True, name=None, description=None, title=None, use_default=None
    ):
        self.required = required
        self.description = description
        self.title = title
        self.name = name
        # if use_default and required:
        #     raise Exception("'use_default' is not allowed for 'required' property")
        self.use_default = self._validate_use_default(use_default)

    def _validate_use_default(self, value):
        if isinstance(value, BaseInstance):
            value.validate()
        return value

    def validate(self, instance, draft_cls=None, check_formats=False):
        return super().validate(
            instance, self, draft_cls=draft_cls, check_formats=check_formats
        )

    def validation_errors(self, instance, draft_cls=None, check_formats=False):
        return super().validation_errors(
            instance, self, draft_cls=draft_cls, check_formats=check_formats
        )

    def __call__(self, *args, **kwargs):
        raise NotImplementedError("Not implemented.")

    def _get_meta(self):
        return getattr(self.__class__, "Meta", None)

    def _get_meta_attribute(self, attr):
        _meta = self._get_meta()
        return _meta and getattr(_meta, attr, None)

    def _get_all_supers(self):
        return [cls for cls in self.__class__.__mro__ if cls.__name__ != "object"]

    def _get_allowed_fields_values(self):
        visited = []
        for sup in self._get_all_supers():
            for attr_name, field_obj in sup.__dict__.items():
                if isinstance(field_obj, Field) and attr_name not in visited:
                    yield attr_name, field_obj
                    visited.append(attr_name)

    @classmethod
    def _confirm_json_loaded(cls, data):
        return data


class PrimitiveField(Field):
    _VALID_TYPES = ()

    class Instance(SingleValueInstance):
        pass

    def _precheck(self, value):
        assert isinstance(value, self._VALID_TYPES)

    def __call__(self, value):
        return self.__class__.Instance(value, schema=self)

    @classmethod
    def _from_json_class(cls, data):
        data = cls._confirm_json_loaded(data)
        schema = cls()
        schema.validate(data)
        instance = cls.instance(data)
        data = instance.deserialize(data)
        return data

    def _from_json_instance(self, data):
        data = self._confirm_json_loaded(data)
        self.validate(data)
        instance = self.instance(data)
        data = instance.deserialize(data)
        return data

    class _FromJsonDescriptor:
        def __get__(self, instance, owner=None):
            if not instance:
                return owner._from_json_class
            return instance._from_json_instance

    from_json = _FromJsonDescriptor()

    class _AsInstanceDescriptor:
        def __get__(self, instance, owner=None):
            if not instance:
                return owner()
            return instance

    instance = _AsInstanceDescriptor()


class Number(PrimitiveField):
    _JSON_SCHEMA_TYPE = "number"
    _VALID_TYPES = (int, float)

    class Instance(SingleValueInstance):
        pass

    def __init__(
        self,
        required=True,
        name=None,
        title=None,
        description=None,
        min=None,
        max=None,
        exclusive_max=None,
        exclusive_min=None,
        multiple_of=None,
        use_default=None,
    ):
        super().__init__(
            required=required,
            name=name,
            title=title,
            description=description,
            use_default=use_default,
        )
        self.min = min
        self.max = max
        self.exclusive_min = exclusive_min
        self.exclusive_max = exclusive_max
        self.multiple_of = multiple_of

    def to_json_schema(self):
        schema = super().to_json_schema()
        if self.min is not None:
            assert self.min >= 0
            schema["minimum"] = self.min
        elif self.exclusive_min is not None:
            assert self.exclusive_min >= 0
            schema["exclusiveMinimum"] = self.exclusive_min

        if self.max is not None:
            assert self.max >= 0
            schema["maximun"] = self.max
        elif self.exclusive_max is not None:
            assert self.exclusive_max >= 0
            schema["exclusiveMaximun"] = self.exclusive_max

        if self.multiple_of is not None:
            schema["multipleOf"] = self.multiple_of

        return schema


class Integer(Number):
    _JSON_SCHEMA_TYPE = "integer"
    _VALID_TYPES = (int,)

    class Instance(SingleValueInstance):
        pass


class String(PrimitiveField):
    _JSON_SCHEMA_TYPE = "string"
    _VALID_TYPES = (str,)

    class Instance(SingleValueInstance):
        def serialize_json():
            return str(self._instance)

    def __init__(
        self,
        required=True,
        name=None,
        title=None,
        description=None,
        min_len=None,
        max_len=None,
        pattern=None,
        blank=False,
        use_default=None,
    ):
        super().__init__(
            required=required,
            name=name,
            title=title,
            description=description,
            use_default=use_default,
        )

        self.min_len = min_len
        self.max_len = max_len
        self.pattern = pattern
        self.blank = blank

    def to_json_schema(self):
        schema = super().to_json_schema()
        if self.min_len is not None:
            assert self.min_len >= 0
            schema["minLength"] = self.min_len
        elif self.blank is True:
            schema["minLength"] = 0

        if self.max_len is not None:
            assert self.max_len >= 0
            schema["maxLength"] = self.max_len

        if self.pattern is not None:
            assert pattern
            schema["pattern"] = pattern

        return schema


class Boolean(PrimitiveField):
    _JSON_SCHEMA_TYPE = "boolean"
    _VALID_TYPES = (bool,)

    class Instance(SingleValueInstance):
        pass


class Null(PrimitiveField):
    _JSON_SCHEMA_TYPE = "null"
    _VALID_TYPES = (bool,)

    class Instance(SingleValueInstance):
        pass

    def __init__(
        self, required=True, name=None, description=None, title=None, use_default=False
    ):
        super().__init__(
            required=required, name=name, description=description, title=title,
        )
        assert isinstance(use_default, bool)
        if use_default:
            self.use_default = True


class MustInstanceField(Field):
    def __call__(self, value):
        return self.__class__.Instance(value, schema=self)

    def to_json_schema(self):
        value = (
            self._value.serialize()
            if isinstance(self._value, InstanceMixin)
            else self._value
        )
        return {self._JSON_SCHEMA_TYPE: value}

    def instance(self, instance):
        return self.Instance(instance, schema=self)

    def from_json(self, data):
        return self.instance(data)


class Const(MustInstanceField):
    _JSON_SCHEMA_TYPE = "const"

    class Instance(SingleValueInstance):
        pass

    def __init__(
        self,
        value,
        required=True,
        name=None,
        title=None,
        description=None,
        use_default=None,
    ):
        super().__init__(
            required=required,
            name=name,
            title=title,
            description=description,
            use_default=use_default,
        )
        self._value = value


class Enum(MustInstanceField):
    _JSON_SCHEMA_TYPE = "enum"

    class Instance(SingleValueInstance):
        pass

    def __init__(
        self,
        iterable,
        required=True,
        name=None,
        title=None,
        description=None,
        use_default=None,
    ):
        assert isinstance(iterable, Iterable)
        super().__init__(
            required=required,
            name=name,
            title=title,
            description=description,
            use_default=use_default,
        )

        if isinstance(iterable, enum.EnumMeta):
            iterable = [e.value for e in iterable]
        self._value = iterable


class Format(MustInstanceField):
    _JSON_SCHEMA_TYPE = "format"

    EMAIL = "email"
    IDN_EMAIL = "idn-email"
    DATE = "date"
    DATE_TIME = "date-time"
    HOSTNAME = "hostname"
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    URI = "uri"
    URI_REFERENCE = "uri-reference"
    IRI = "iri"
    IRI_REFERENCE = "iri-reference"
    UUID = "uuid"
    JSON_POINTER = "json-poniter"
    URI_TEMPLATE = "uri-template"
    REGEX = "regex"

    class Instance(SingleValueInstance):
        def serialize_json(self):
            return str(self._instance)

    def __init__(
        self,
        format,
        required=True,
        name=None,
        title=None,
        description=None,
        use_default=None,
    ):
        super().__init__(
            required=required,
            name=name,
            description=description,
            title=title,
            use_default=use_default,
        )
        self._value = format


class RootField(Field):
    pass


class List(RootField):

    _JSON_SCHEMA_TYPE = "array"

    class Meta:
        additional_properties = False

    # TODO: override copy,  operations to return new List.Instance
    class Instance(BaseInstance):
        def __init__(self, iterable, schema):
            assert isinstance(iterable, Iterable)
            super().__init__(schema)
            self._list = list(iterable)

        def serialize(self):
            l = []
            for e in self._list:
                if not isinstance(e, InstanceMixin):
                    l.append(e)
                else:
                    l.append(e.serialize())
            return l

        def deserialize(self, data):
            _types = self.schema._types
            if isinstance(_types, list):
                for e, obj in zip(data, _types):
                    self._list.append(obj.from_json(e))
            else:
                obj = _types
                for e in data:
                    self._list.append(obj.from_json(e))

        def serialize_json(self):
            l = []
            for e in self._list:
                if isinstance(e, InstanceMixin):
                    l.append(e.serialize_json())
                else:
                    if self.is_json_serializale(e):
                        l.append(e)
                    else:
                        l.append(str(e))
            return l

        def __getitem__(self, slice_):
            # list does shallow copy only
            if isinstance(slice_, slice):
                return self.schema.__class__.Instance(
                    self._list.__getitem__(slice_), schema=self.schema
                )
            else:
                return self._list.__getitem__(slice_)

        def __setitem__(self, i, item):
            return self._list.__setitem__(i, item)

        def __getattr__(self, name):
            attr = getattr(self._list, name, None)
            if attr:
                return attr
            return super().__getattribute__(name)

        def __add__(self, other):
            assert isinstance(other, (list, List.Instance))
            if isinstance(other, list):
                return self.schema.__class__.Instance(
                    (self._list + other), schema=self.schema
                )
            else:
                return self.schema.__class__.Instance(
                    (self._list + other._list), schema=self.schema
                )

    def __init__(
        self,
        *types,
        required=False,
        name=None,
        title=None,
        description=None,
        max_items=None,
        min_items=None,
        unique_items=False,
        contains=None,
        max_contains=None,
        min_contains=None,
        use_default=None,
    ):
        super().__init__(
            required=required,
            name=name,
            title=title,
            description=description,
            use_default=use_default,
        )

        _types = []

        for _type in types:
            if not isinstance(_type, Field):
                _type = _type()
            _types.append(_type)

        if len(_types):
            self._types = _types if len(_types) > 1 else _types[0]
        else:
            self._types = []

        self.max_items = max_items
        self.min_items = min_items
        self.unique_items = unique_items
        self.max_contains = max_contains
        self.min_contains = min_contains
        self.contains = contains

    def __call__(self, iterable):
        return self.__class__.Instance(iterable, schema=self)

    def to_json_schema(self):
        schema = super().to_json_schema()
        if isinstance(self._types, list):
            if self._types:
                schema["items"] = []
                for _type in self._types:
                    schema["items"].append(_type.to_json_schema())
        else:
            schema["items"] = self._types.to_json_schema()

        if self.max_items is not None:
            schema["maxItems"] = self.max_items
        if self.min_items is not None:
            schema["minItems"] = self.min_items

        schema["uniqueItems"] = self.unique_items

        if self._get_meta_attribute("additional_items"):
            schema["additionalItems"] = self._get_meta_attribute("additional_items")

        if self.contains is not None:
            schema["contains"] = self.contains.to_json_schema()
        if self.min_contains is not None:
            schema["minContains"] = self.min_contains.to_json_schema()
        if self.max_contains is not None:
            schema["maxContains"] = self.max_contains.to_json_schema()

        return schema

    @classmethod
    def _confirm_json_loaded(cls, data):
        assert isinstance(data, (bytes, list, str))
        if isinstance(data, (str, bytes)):
            data = json.loads(data)
        return data

    @classmethod
    def _from_json_class(cls, data):
        data = cls._confirm_json_loaded(data)
        schema = cls()
        schema.validate(data)
        instance = cls.instance([])
        instance.deserialize(data)
        return instance

    def _from_json_instance(self, data):
        data = self._confirm_json_loaded(data)
        self.validate(data)
        instance = self.instance([])
        instance.deserialize(data)
        return instance

    class _FromJsonDescriptor:
        def __get__(self, instance, owner=None):
            if not instance:
                return owner._from_json_class
            return instance._from_json_instance

    from_json = _FromJsonDescriptor()

    class _AsInstanceDescriptor:
        def __get__(self, instance, owner=None):
            if not instance:
                return GenericList()
            return instance

    instance = _AsInstanceDescriptor()


class GenericList(List):
    class Meta(List.Meta):
        additional_items = True


class Schema(RootField):

    _JSON_SCHEMA_TYPE = "object"

    class Meta:
        field_dependencies = []
        additional_properties = False

    class Instance(BaseInstance):

        ignore_attributes = ("_schema", "_field_map", "_strict_check")

        def __init__(self, schema, **kwargs):
            super().__init__(schema)
            self._set_fields_map()
            self._validate_and_set_attrs(kwargs)

        def _set_fields_map(self):
            self._field_map = dict(self.schema._get_allowed_fields_values())

        def _validate_and_set_attrs(self, kwargs):
            if not self.schema._get_meta_attribute("additional_properties"):
                self._set_by_field_map(kwargs)
            else:
                for k, v in kwargs.items():
                    setattr(self, k, v)

        def _set_by_field_map(self, kwargs):
            for f, obj in self._field_map.items():
                is_missing = False
                try:
                    v = kwargs.pop(f)
                except KeyError:
                    if obj.use_default is not None:
                        v = obj.use_default
                    else:
                        is_missing = True
                if is_missing is False:
                    if obj.name:
                        obj.attr_name = f
                        setattr(self, (obj.name or f), v)
                    else:
                        setattr(self, f, v)

        def __getitem__(self, name):
            if isinstance(name, str):
                return getattr(self, name)
            return super().__getitem__(name)

        def __getattr__(self, name):
            for f, obj in self._field_map.items():
                if getattr(obj, "attr_name", None) == name:
                    return getattr(self, obj.name)
            return self.__getattribute__(name)

        def __setitem__(self, name, value):
            if isinstance(name, str):
                return self._validate_and_set_attrs({name: value})
            return super().__setitem__(name, value)

        def serialize(self):
            data = {}
            for k, v in vars(self).items():
                if k in self.ignore_attributes:
                    continue
                if isinstance(v, InstanceMixin):
                    data[k] = v.serialize()
                else:
                    data[k] = v
            return data

        def serialize_json(self):
            data = {}
            for k, v in vars(self).items():
                if k in self.ignore_attributes:
                    continue
                if isinstance(v, InstanceMixin):
                    data[k] = v.serialize_json()
                else:
                    if self.is_json_serializale(v):
                        data[k] = v
                    else:
                        data[k] = str(v)
            return data

        def deserialize(self, data):
            self._set_fields_map()
            for fname, obj in self._field_map.items():
                is_missing = False
                try:
                    v = data[obj.name or fname]
                except KeyError:
                    if obj.use_default is not None:
                        v = obj.use_default
                    else:
                        is_missing = True

                if not is_missing:
                    setattr(self, obj.name or fname, obj.from_json(v))

    def __call__(self, **kwargs):
        return self.__class__.Instance(self, **kwargs)

    def __init__(
        self,
        required=True,
        name=None,
        description=None,
        title=None,
        max_properties=None,
        min_properties=None,
        use_default=None,
    ):
        super().__init__(
            required=required,
            name=name,
            title=title,
            description=description,
            use_default=use_default,
        )
        self.required = required
        self.max_properties = max_properties
        self.min_properties = min_properties

    def to_json_schema(self):
        _schema = {"type": self._JSON_SCHEMA_TYPE, "properties": {}, "required": []}
        kclass = self.__class__

        #  __dict__ only refers currrent class not super chain.
        for attr_name, field_obj in self._get_allowed_fields_values():
            fname = field_obj.name if field_obj.name is not None else attr_name
            _schema["properties"][fname] = field_obj.to_json_schema()
            if field_obj.required:
                _schema["required"].append(fname)

        if self.max_properties is not None:
            _schema["maxProperties"] = self.max_properties
        if self.min_properties is not None:
            _schema["minProperties"] = self.min_properties

        _field_dependencies = self._get_meta_attribute("field_dependencies") or []
        if _field_dependencies:
            _schema["dependencies"] = {}
        for d in _field_dependencies:
            _schema["dependencies"][d.source] = d.targets
        _schema["additionalProperties"] = (
            self._get_meta_attribute("additional_properties") or False
        )
        return _schema

    @classmethod
    def _confirm_json_loaded(cls, data):
        assert isinstance(data, (bytes, dict, str))
        if isinstance(data, (str, bytes)):
            data = json.loads(data)
        return data

    @classmethod
    def from_json(cls, data):
        data = cls._confirm_json_loaded(data)
        schema = cls()
        schema.validate(data)
        instance = cls.instance()
        instance.deserialize(data)
        return instance

    class _AsInstanceDescriptor:
        def __get__(self, instance, owner=None):
            if not instance:
                return owner()
            return instance

    instance = _AsInstanceDescriptor()


class GenericSchema(Schema):
    class Instance(Schema.Instance):
        pass

    class Meta(Schema.Meta):
        additional_properties = True
