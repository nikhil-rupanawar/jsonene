from __future__ import absolute_import
from factory import BaseDictFactory, BaseListFactory
from .fields import Schema, List


class SchemaFactory(BaseDictFactory):
    class Meta(object):
        abstract = True

    @classmethod
    def _build(cls, model_schema, *args, **kwargs):
        if args:
            assert False, u"Not allowed"
        assert issubclass(model_schema, Schema)
        return model_schema.instance(**kwargs)

    @classmethod
    def _create(cls, model_schema, *args, **kwargs):
        return cls._build(model_schema, *args, **kwargs)


class ListSchemaFactory(BaseListFactory):
    class Meta(object):
        abstract = True

    @classmethod
    def _build(cls, model_schema, *args, **kwargs):
        if args:
            assert False, u"Not allowed"

        assert issubclass(model_schema, List)
        values = kwargs.values()
        return model_schema.instance(values)

    @classmethod
    def _create(cls, model_schema, *args, **kwargs):
        return cls._build(model_schema, *args, **kwargs)
