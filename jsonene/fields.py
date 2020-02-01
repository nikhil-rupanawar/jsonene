import jsonschema
import abc
import json
import inspect
import enum

from jsonschema.validators import validator_for
from jsonschema import draft7_format_checker
from .objects import BaseInstance, SingleValueInstance


class Field:
    _JSON_SCHEMA_TYPE = ""

    class Meta:
        field_dependencies = []
        additional_properties = False

    def __init__(self, required=True):
        self.required = required

    def to_json_schema(self):
        return {"type": self._JSON_SCHEMA_TYPE}

    def validate(self, instance, draft_cls=None):
        return jsonschema.validate(
            instance=instance,
            schema=self.to_json_schema(),
            cls=draft_cls,
            format_checker=draft7_format_checker,
        )

    def validation_errors(self, instance, draft_cls=None):
        schema = self.to_json_schema()
        if not draft_cls:
            draft_cls = validator_for(schema)
        return draft_cls(schema, format_checker=draft7_format_checker).iter_errors(
            instance
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


class PrimitiveField(Field):
    _VALID_TYPES = ()

    class Instance(SingleValueInstance):
        pass

    def _precheck(self, value):
        assert isinstance(value, self._VALID_TYPES)

    def __call__(self, value):
        self._precheck()
        return self.__class__.Instance(value, schema=self)

    class _AsInstanceDescriptor:
        def __get__(self, instance, owner=None):
            if not instance:
                return owner()
            return instance

    instance = _AsInstanceDescriptor


class Number(PrimitiveField):
    _JSON_SCHEMA_TYPE = "number"
    _VALID_TYPES = (int, float)

    def __init__(
        self,
        required=True,
        min=None,
        max=None,
        exclusive_max=None,
        exclusive_min=None,
        multiple_of=None,
    ):
        super().__init__(required=required)
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


class String(PrimitiveField):
    _JSON_SCHEMA_TYPE = "string"
    _VALID_TYPES = (str,)

    def __init__(
        self, required=True, min_length=None, max_length=None, pattern=None, blank=False
    ):
        super().__init__(required=required)

        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.blank = blank

    def to_json_schema(self):
        schema = super().to_json_schema()
        if self.min_length is not None:
            assert self.min_length >= 0
            schema["minLength"] = self.min_length
        elif self.blank is True:
            schema["minLength"] = 0

        if self.max_length is not None:
            assert self.max_length >= 0
            schema["maxLength"] = self.max_length

        if self.pattern is not None:
            assert pattern
            schema["pattarn"] = pattern

        return schema


class Boolean(PrimitiveField):
    _JSON_SCHEMA_TYPE = "boolean"
    _VALID_TYPES = (bool,)


class Null(PrimitiveField):
    _JSON_SCHEMA_TYPE = "null"

    def __call__(self):
        return Null.Instance(None)


class Const(Field):
    class Instance(SingleValueInstance):
        pass

    def __init__(self, value, required=False):
        super().__init__(required=required)
        self._value = value

    def __call__(self, value):
        return self.__class__.Instance(value, schema=self)

    def to_json_schema(self):
        value = (
            self._value.serialize()
            if isinstance(self._value, BaseInstance)
            else self._value
        )
        return {"const": value}

    def instance(self, instance):
        return self.Instance(instance, schema=self)


class Enum(Field):
    class Instance(SingleValueInstance):
        pass

    def __call__(self, value):
        return self.__class__.Instance(value, schema=self)

    def __init__(self, value, required=False):
        assert isinstance(value, (List.Instance, list, tuple))
        if isinstance(value, List.Instance):
            value = value.serialize()
        super().__init__(required=required)
        self.value = value

    def to_json_schema(self):
        value = (
            self.value.serialize()
            if isinstance(self.value, BaseInstance)
            else self.value
        )
        return {"enum": value}

    def instance(self, instance):
        return self.Instance(instance, schema=self)


class Format(Field):
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
        pass

    def __init__(self, format, required=True):
        super().__init__(required=required)
        self.format = format

    def __call__(self, value):
        return self.__class__.Instance(value, schema=self)

    def to_json_schema(self):
        return {"format": self.format}

    def instance(self, value):
        return self.Instance(value, schema=self)


class RootField(Field):
    pass


class List(RootField):

    _JSON_SCHEMA_TYPE = "array"

    class Meta:
        additional_properties = False

    # TODO: override copy,  operations to return new List.Instance
    class Instance(BaseInstance):
        def __init__(self, iterable, schema=None):
            super().__init__(schema=schema)
            self._list = list(iterable)

        def validate(self):
            self.schema and self.schema.validate(self.serialize())

        def serialize(self):
            l = []
            for e in self._list:
                if not isinstance(e, BaseInstance):
                    l.append(e)
                else:
                    l.append(e.serialize())
            return l

        def __getitem__(self, slice_):
            # list does shallow copy only
            if isinstance(slice_, slice):
                new_list = self._list.__getitem__(slice_)
                return self.schema.__class__.Instance(new_list, schema=self.schema)
            else:
                return self._list.__getitem__(slice_)

        def __setitem__(self, i, item):
            return self._list.__setitem__(i, item)

        def __getattr__(self, name):
            attr = getattr(self._list, name, None)
            if attr:
                return attr
            return super.__getattr__(name)

        def __add__(self, other):
            assert isinstance(other, (list, List.Instance))
            if isinstance(other, list):
                new_list = self._list + other
            else:
                new_list = self._list + other._list
            return self.schema.__class__.Instance(new_list, schema=self.schema)

    def __init__(
        self,
        *types,
        required=False,
        max_items=None,
        min_items=None,
        unique_items=False,
    ):
        super().__init__(required=required)

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

    def __call__(self, iterable):
        return self.__class__.Instance(iterable, schema=self)

    def to_json_schema(self):
        _schema = super().to_json_schema()
        if isinstance(self._types, list):
            if self._types:
                _schema["items"] = []
                for _type in self._types:
                    _schema["items"].append(_type.to_json_schema())
        else:
            _schema["items"] = self._types.to_json_schema()

        if self.max_items is not None:
            _schema["maxItems"] = self.max_items
        if self.min_items is not None:
            _schema["minItems"] = self.min_items
        _schema["uniqueItems"] = self.unique_items

        if self._get_meta_attribute("additional_items"):
            _schema["additionalItems"] = self._get_meta_attribute("additional_items")
        return _schema

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
        # _schema_ fancy?
        #    - yes but we don't want to minimize conflict with schema as attr name
        def __init__(self, _schema_=None, **kwargs):
            super().__init__(schema=_schema_)
            for k, v in kwargs.items():
                setattr(self, k, v)

        def serialize(self):
            data = {}
            for k, v in vars(self).items():
                if k.startswith("_"):
                    continue
                if isinstance(v, BaseInstance):
                    data[k] = v.serialize()
                else:
                    data[k] = v
            return data

    def __call__(self, **kwargs):
        return self.__class__.Instance(_schema_=self, **kwargs)

    def __init__(self, required=False, max_properties=None, min_properties=None):
        self.required = required
        self.max_properties = max_properties
        self.min_properties = min_properties

    def to_json_schema(self):
        _schema = {"type": self._JSON_SCHEMA_TYPE, "properties": {}, "required": []}
        kclass = self.__class__

        #  __dict__ only refers currrent class not super chain.
        all_supers = [cls for cls in self.__class__.__mro__ if cls.__name__ != "object"]
        for sup in all_supers:
            for name, field in sup.__dict__.items():
                if isinstance(field, Field):
                    _schema["properties"][name] = field.to_json_schema()
                    if field.required:
                        _schema["required"].append(name)

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

    class _AsInstanceDescriptor:
        def __get__(self, instance, owner=None):
            if not instance:
                return owner()
            return instance

    instance = _AsInstanceDescriptor()


class GenericSchema(Schema):
    class Meta(Schema.Meta):
        additional_properties = True
