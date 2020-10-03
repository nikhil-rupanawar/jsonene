from factory import BaseDictFactory, BaseListFactory
from .fields import SchemaType, List


class SchemaFactory(BaseDictFactory):
    class Meta:
        abstract = True

    @classmethod
    def _build(cls, model_schema, *args, **kwargs):
        if args:
            assert False, "Not allowed"
        assert issubclass(model_schema, SchemaType)
        return model_schema(**kwargs)

    @classmethod
    def _create(cls, model_schema, *args, **kwargs):
        return cls._build(model_schema, *args, **kwargs)


class ListSchemaFactory(BaseListFactory):
    class Meta:
        abstract = True

    @classmethod
    def _build(cls, model_schema, *args, **kwargs):
        if args:
            assert False, "Not allowed"
        assert issubclass(model_schema, List)
        values = kwargs.values()
        return model_schema([*values])

    @classmethod
    def _create(cls, model_schema, *args, **kwargs):
        return cls._build(model_schema, *args, **kwargs)
