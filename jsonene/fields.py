import jsonschema
import abc
import json
import inspect
import enum
from collections.abc import Iterable
from cached_property import cached_property
from functools import partial
from jsonschema.validators import validator_for
from jsonschema import draft7_format_checker
from itertools import cycle

# base class for all fields
class BaseField:
    @classmethod
    def asField(cls, *args, **kwargs):
        return cls.Schema(cls, *args, **kwargs)

    def validate(self):
        return self.asField().validate_instance(self)

    def validation_errors(self):
        return list(self.asField().validation_errors(self))

    class Schema:
        JSON_SCHEMA_TYPE = "object"
        def __init__(
            self,
            field_class,
            required=True,
            name=None,
            description=None,
            title=None,
            use_default=None,
            null=False
        ):
            self.field_class = field_class
            self.required = required
            self.name = name
            self.description = description
            self.title = title
            self.use_default = self._validate_use_default(use_default)
            self.null = null

        def to_json_schema(self):
            if self.null:
                schema = {"type": [self.JSON_SCHEMA_TYPE, 'null']}
            else:
                schema = {"type": self.JSON_SCHEMA_TYPE}
            if self.title is not None:
               schema["title"] = self.title
            if self.description is not None:
                schema["description"] = self.description
            return schema

        @cached_property
        def json_schema(self):
            return self.to_json_schema()

        def validate_instance(self, instance, draft_cls=None, check_formats=False):
            schema = self.json_schema
            if isinstance(instance, BaseField):
                instance = instance.serialize()
            if check_formats:
                # TODO warning depedencied
                # https://python-jsonschema.readthedocs.io/en/stable/validate/
                return jsonschema.validate(
                    instance=instance,
                    schema=schema,
                    cls=draft_cls,
                    format_checker=jsonschema.draft7_format_checker
                 )
            return jsonschema.validate(
                instance=instance,
                schema=schema,
                cls=draft_cls
            )

        def validation_errors(self, instance, draft_cls=None, check_formats=False):
            schema = self.json_schema
            if isinstance(instance, BaseField):
                instance = instance.serialize()
            if not draft_cls:
                draft_cls = jsonschema.validators.validator_for(schema)
            if check_formats:
                return draft_cls(schema).iter_errors(instance)
            return draft_cls(
                schema, format_checker=jsonschema.draft7_format_checker
            ).iter_errors(instance)

        @classmethod
        def _validate_use_default(cls, value):
            if isinstance(value, BaseField):
                value.validate()
            return value

    @classmethod
    def _get_all_supers(cls):
        return [cls for cls in cls.__mro__ if cls.__name__ != "object"]

    @classmethod
    def _get_allowed_fields_values(cls):
        visited = set()
        for sup in cls._get_all_supers():
            for attr_name, field_obj in sup.__dict__.items():
                if isinstance(field_obj, BaseField.Schema) and attr_name not in visited:
                    yield attr_name, field_obj
                    visited.add(attr_name)

    @classmethod
    def _confirm_json_loaded(cls, data):
        raise NotImplementedError()

    @classmethod
    def is_json_serializale(cls, value):
        try:
            json.dumps(value)
        except TypeError:
            return False
        return True

    def to_json(self, indent=2):
        return json.dumps(self.serialize_json(), indent=indent)


class SingleValueField(BaseField):
    def __init__(self, value):
        self._value = value

    def serialize(self):
        return self._value

    @classmethod
    def deserialize(cls, value):
        return cls(value)

    @classmethod
    def _confirm_json_loaded(cls, data):
        return data


class PrimitiveBaseField(SingleValueField):
    pass


class Number(PrimitiveBaseField):
    class Schema(PrimitiveBaseField.Schema):
        JSON_SCHEMA_TYPE = "number"
        def __init__(
            self,
            *args,
            min=None,
            max=None,
            exclusive_max=None,
            exclusive_min=None,
            multiple_of=None,
            **kwargs,
        ):
            super().__init__(
                *args,
                **kwargs,
            )
            self.min = min
            self.max = max
            self.exclusive_min = exclusive_min
            self.exclusive_max = exclusive_max
            self.multiple_of = multiple_of

        def to_json_schema(cls):
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


class Integer(int, Number):
    class Schema(PrimitiveBaseField.Schema):
        JSON_SCHEMA_TYPE = "integer"


class String(str, PrimitiveBaseField):
    class Schema(PrimitiveBaseField.Schema):
        JSON_SCHEMA_TYPE = "string"

        def __init__(
            self,
            *args,
            min_len=None,
            max_len=None,
            pattern=None,
            blank=False,
            **kwargs,
        ):
            super().__init__(
                *args,
                **kwargs,
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
            if self.blank is False:
                if not self.min_len:
                    schema["minLength"] = 1
            return schema


class Boolean(PrimitiveBaseField):
    class Schema(PrimitiveBaseField.Schema):
        JSON_SCHEMA_TYPE = "boolean"


class Null(PrimitiveBaseField):
    class Schema(PrimitiveBaseField.Schema):
        JSON_SCHEMA_TYPE = "null"


class SchameValueBaseField(SingleValueField):
    class Schema(SingleValueField.Schema):
        def __init__(self, field_class, match_value, *args, **kwargs):
            super().__init__(field_class, *args, **kwargs)
            self.match_value = match_value

        def to_json_schema(self):
            value = (
                self.match_value.serialize()
                if isinstance(self.match_value, BaseField)
                else self.match_value
            )
            return {self.JSON_SCHEMA_TYPE: value}


class Const(SchameValueBaseField):
    class Schema(SchameValueBaseField.Schema):
        JSON_SCHEMA_TYPE = "const"


class Enum(SchameValueBaseField):
    class Schema(SchameValueBaseField.Schema):
        JSON_SCHEMA_TYPE = "enum"
        def __init__(
            self,
            *args,
            iterable,
            **kwargs,
        ):
            assert isinstance(iterable, Iterable)
            super().__init__(
                *args,
                **kwargs,
            )
            if isinstance(iterable, enum.EnumMeta):
                iterable = [e.value for e in iterable]
            self.match_value = list(iterable)


class Format(String):
    class Schema(SchameValueBaseField.Schema):
        JSON_SCHEMA_TYPE = "format"
    IDN_EMAIL = "idn-email"
    EMAIL = "email"
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


class RootBaseField(BaseField):
    pass


class List(list, RootBaseField):
    def serialize(self):
        l = []
        for e in self:
            if not isinstance(e, BaseField):
                l.append(e)
            else:
                l.append(e.serialize())
        return l

    @classmethod
    def deserialize(cls, schema_obj, data, strict=False):
        obj = cls()
        for item, dtype in zip(data, cycle(schema_obj.datatypes)):
            v = item
            if dtype:
                if issubclass(dtype, RootBaseField):
                    v = dtype.deserialize(v)
                else:
                    v = dtype(v)
            obj.append(v)
        return obj

    class Schema(BaseField.Schema):
        JSON_SCHEMA_TYPE = "array"
        def __init__(
            self,
            field_class,
            *types,
            max_items=None,
            min_items=None,
            unique_items=False,
            contains=None,
            max_contains=None,
            min_contains=None,
            additional_items=False,
            **kwargs,
        ):
            super().__init__(
                field_class,
                **kwargs,
            )
            _types = []
            _datatypes = []
            for _type in types:
                assert issubclass(_type, BaseField)
                _datatypes.append(_type)
                _type = _type.asField()
                _types.append(_type)

            if len(_types):
                _types = _types if len(_types) > 1 else _types[0]
            else:
                _types = []

            self.types = _types
            self.datatypes = _datatypes
            self.max_items = max_items
            self.min_items = min_items
            self.unique_items = unique_items
            self.max_contains = max_contains
            self.min_contains = min_contains
            self.contains = contains
            self.additional_items = additional_items

        def to_json_schema(self):
            schema = super().to_json_schema()
            if isinstance(self.types, list):
                if self.types:
                    schema["items"] = []
                    for _type in self.types:
                        schema["items"].append(_type.to_json_schema())
            else:
                schema["items"] = self.types.to_json_schema()

            if self.max_items is not None:
                schema["maxItems"] = self.max_items
            if self.min_items is not None:
                schema["minItems"] = self.min_items

            schema["uniqueItems"] = self.unique_items

            if self.additional_items:
                schema["additionalItems"] = self.additional_items

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
    def from_json(cls, data):
        data = cls._confirm_json_loaded(data)
        instance = cls(*data)
        return instance


class SchemaTypeMeta(type):
    def __new__(cls, name, bases, dct):
        kclass = super().__new__(cls, name, bases, dct)
        kclass._meta = kclass.Meta()
        kclass._meta.allowed_fields_map = dict(cls._get_allowed_fields_values(kclass))
        return kclass

    @classmethod
    def _get_all_supers(cls, kclass):
        return [cls for cls in kclass.__mro__ if issubclass(cls, BaseField)]

    @classmethod
    def _get_allowed_fields_values(cls, kclass):
        visited = set()
        for sup in cls._get_all_supers(kclass):
            for attr_name, field_obj in sup.__dict__.items():
                if isinstance(field_obj, BaseField.Schema) and attr_name not in visited:
                    yield attr_name, field_obj
                    visited.add(attr_name)


class SchemaType(dict, RootBaseField, metaclass=SchemaTypeMeta):
 
    class Meta:
        field_dependencies = []
        additional_properties = False

    def serialize(self):
        data = {}
        for k, v in self.items():
            if isinstance(v, BaseField):
                data[k] = v.serialize()
            else:
                data[k] = v
        return data

    @classmethod
    def deserialize(cls, data):
        schema_object = cls()
        for fname, obj in schema_object._meta.allowed_fields_map.items():
            is_missing = False
            try:
                v = data[obj.name or fname]
            except KeyError:
                if obj.use_default is not None:
                    v = obj.use_default
                else:
                    is_missing = True
            if not is_missing:
                if isinstance(obj, List.Schema):
                    schema_object[obj.name or fname] = obj.field_class.deserialize(obj, v)
                else:
                    schema_object[obj.name or fname] = obj.field_class.deserialize(v)
        return schema_object

    class Schema(RootBaseField.Schema):
        JSON_SCHEMA_TYPE = "object"
        def __init__(
            self,
            field_class,
            required=True,
            name=None,
            description=None,
            title=None,
            max_properties=None,
            min_properties=None,
            use_default=None,
            additional_properties=False,
            field_dependencies=None,
        ):
            super().__init__(
                field_class,
                required=required,
                name=name,
                title=title,
                description=description,
                use_default=use_default,
            )
            self.required = required
            self.max_properties = max_properties
            self.min_properties = min_properties
            self.field_dependencies = field_dependencies or []
            self.additional_properties = additional_properties

        def to_json_schema(self):
            _meta = self.field_class._meta
            _schema = {"type": self.JSON_SCHEMA_TYPE, "properties": {}, "required": []}
            #  __dict__ only refers currrent class not super chain.
            for attr_name, field_obj in _meta.allowed_fields_map.items():
                fname = field_obj.name if field_obj.name is not None else attr_name
                _schema["properties"][fname] = field_obj.to_json_schema()
                if field_obj.required:
                    _schema["required"].append(fname)
            if self.max_properties is not None:
                _schema["maxProperties"] = self.max_properties
            if self.min_properties is not None:
                _schema["minProperties"] = self.min_properties
            _field_dependencies = self.field_dependencies or getattr(
                _meta, 'field_dependencies', []
            )
            if _field_dependencies:
                _schema["dependencies"] = {}
            for d in _field_dependencies:
                _schema["dependencies"][d.source] = d.targets
            _schema["additionalProperties"] = self.additional_properties or getattr(
                _meta, 'additional_properties', False
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
        instance = cls()
        instance.deserialize(**data)
        return instance


