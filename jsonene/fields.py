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
class BaseField:


    @classmethod
    def asField(cls, *args, **kwargs):
        return cls.Schema(*args, **kwargs)

    class Schema:
        JSON_SCHEMA_TYPE = "object"
        def __init__(
            self,
            required=True,
            name=None,
            description=None,
            title=None,
            use_default=None,
        ):
            self.required = required
            self.name = name
            self.description = description
            self.title = title
            self.use_default = self._validate_use_default(use_default)

        def to_json_schema(self):
            schema = {"type": self.JSON_SCHEMA_TYPE}
            if self.title is not None:
               schema["title"] = self.title
            if self.description is not None:
                schema["description"] = self.description
            return schema

        def validate_instance(self, instance, schema=None, draft_cls=None, check_formats=False):
            schema = schema or self.to_json_schema()
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

        def validation_errors(self, instance, schema=None, draft_cls=None, check_formats=False):
            schema = schema or self.to_json_schema()
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

    def deserialize(self, value):
        self._value = value

    @classmethod
    def _confirm_json_loaded(cls, data):
        return data


class PrimitiveBaseField(SingleValueField):
    pass


class Number(int, PrimitiveBaseField):

    class Schema(PrimitiveBaseField.Schema):
        JSON_SCHEMA_TYPE = "number"

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


class Integer(Number):
    class Schema(PrimitiveBaseField.Schema):
        JSON_SCHEMA_TYPE = "integer"


class String(str, PrimitiveBaseField):
    class Schema(PrimitiveBaseField.Schema):
        JSON_SCHEMA_TYPE = "string"

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


class Boolean(PrimitiveBaseField):
    class Schema(PrimitiveBaseField.Schema):
        JSON_SCHEMA_TYPE = "boolean"


class Null(PrimitiveBaseField):
    class Schema(PrimitiveBaseField.Schema):
        JSON_SCHEMA_TYPE = "null"

        def __init__(
            self,
            required=True,
            name=None,
            description=None,
            title=None,
            use_default=False,
        ):
            super().__init__(
                required=required,
                name=name,
                description=description,
                title=title
            )
            assert isinstance(use_default, bool)
            if use_default:
                self.use_default = True


class SchameValueBaseField(SingleValueField):
    class Schema(SingleValueField.Schema):
        def __init__(self, match_value, *args, **kwargs):
            super().__init__(*args, **kwargs)
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
            self.match_value = iterable


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

    class Schema(BaseField.Schema):
        JSON_SCHEMA_TYPE = "array"
        additional_properties = False

    def serialize(self):
        l = []
        for e in self:
            if not isinstance(e, BaseField):
                l.append(e)
            else:
                l.append(e.serialize())
        return l

    def deserialize(self, data):
        _types = self.Schema.types
        if isinstance(_types, list):
            for e, obj in zip(data, _types):
                self.append(obj.from_json(e))
        else:
            obj = _types
            for e in data:
                self.append(obj.from_json(e))

    def serialize_json(self):
        l = []
        for e in self:
            if isinstance(e, BaseField):
                l.append(e.serialize_json())
            else:
                if self.is_json_serializale(e):
                    l.append(e)
                else:
                    l.append(str(e))
        return l

    class Schema(BaseField.Schema):
        JSON_SCHEMA_TYPE = "array"
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
            additional_items=False,
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
                if not isinstance(_type, BaseField.Schema):
                   _type = _type.asField()
                _types.append(_type)

            if len(_types):
                _types = _types if len(_types) > 1 else _types[0]
            else:
                _types = []

            self.types = _types
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
    def __init__(self, *args, **kwargs):
        print( *args, **kwargs)
        super().__init__(*args, **kwargs)


class SchemaType(dict, RootBaseField, metaclass=SchemaTypeMeta):
    class Meta:
        pass
    """
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self._set_fields_map()
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
    """
    def serialize(self):
        data = {}
        for k, v in vars(self).items():
            if k in self.ignore_attributes:
                continue
            if isinstance(v, BaseField):
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

    class Schema(RootBaseField.Schema):
        JSON_SCHEMA_TYPE = "object"
        def __init__(
            self,
            required=True,
            name=None,
            description=None,
            title=None,
            max_properties=None,
            min_properties=None,
            use_default=None,
            field_dependencies=None,
            additional_properties=False,
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
            self.field_dependencies = field_dependencies or []
            self.additional_properties = additional_properties

        def to_json_schema(self, allowed_fields):
            _schema = {"type": self.JSON_SCHEMA_TYPE, "properties": {}, "required": []}
            #  __dict__ only refers currrent class not super chain.
            for attr_name, field_obj in allowed_fields:
                fname = field_obj.name if field_obj.name is not None else attr_name
                _schema["properties"][fname] = field_obj.to_json_schema()
                if field_obj.required:
                    _schema["required"].append(fname)
            if self.max_properties is not None:
                _schema["maxProperties"] = self.max_properties
            if self.min_properties is not None:
                _schema["minProperties"] = self.min_properties
            _field_dependencies = self.field_dependencies
            if _field_dependencies:
                _schema["dependencies"] = {}
            for d in _field_dependencies:
                _schema["dependencies"][d.source] = d.targets
            _schema["additionalProperties"] = self.additional_properties
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

    def validate(self, *args, **kwargs):
        schemaobj = self.asField()
        schema = schemaobj.to_json_schema(self._get_allowed_fields_values())
        return schemaobj.validate_instance(self, *args, schema=schema, **kwargs)

    def validation_errors(self, *args, **kwargs):
        schemaobj = self.asField()
        schema = schemaobj.to_json_schema(self._get_allowed_fields_values())
        return schemaobj.validation_errors(self, *args, schema=schema, **kwargs)

