# jsonene
This library is intended to provide APIs to define JSON schema, create instances from schema, serialize/de-serialize to/from json or dict to Objects. 

**Inspired by**

[jsonschema](https://python-jsonschema.readthedocs.io/en/stable/)

[json-schema](https://json-schema.org/draft-07/json-schema-validation.html)

The basic idea is to provide light weight class based schema defination and data classes

**Installation**

pip install jsonene

**Demos**:

```python
import enum
from pprint import pprint
import jsonene

class Gender(enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class Person(jsonene.ObjectType):
    class Meta:
        field_dependencies = [jsonene.RequiredDependency("age", ["date_of_birth"])]

    age = jsonene.Integer(required=False)
    name = jsonene.String()
    country = jsonene.Const("India")
    email = jsonene.Format(jsonene.Format.EMAIL)
    contact = jsonene.String(required=False)
    date_of_birth = jsonene.Format(jsonene.Format.DATE, required=False)
    gender = jsonene.Enum(Gender)
    ip = jsonene.Format(jsonene.Format.IPV4)


class Seller(Person):
    brokerrage = jsonene.Integer(required=False)
    is_broker = jsonene.AnyOf(True, False)
    is_owner = jsonene.AnyOf(True, False)


# Nested schema
class House(jsonene.ObjectType):
    owner = jsonene.Field(Person)
    seller = jsonene.Field(Seller)

# Know your json-schema
pprint(Person.asField().json_schema)

owner = Person(
    name="test",
    age=30,
    country="India",
    email="conikhil@gmail.com",
    gender=Gender.MALE.value,
    date_of_birth="1989-09-11",
    ip="10.8.9.0",
)
owner.validate(check_formats=True)
