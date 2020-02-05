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
import datetime
import json
from jsonene.fields import (
    Boolean,
    List,
    GenericList,
    Null,
    Const,
    Enum,
    Number,
    Integer,
    Schema,
    GenericSchema,
    String,
    Format,
)
from jsonene.operators import AllOf, AnyOf, OneOf, Not
from jsonene.constraints import RequiredDependency
from jsonene.exceptions import ValidationError
```

**Define a Schema**
```python
class Person(Schema):
    name = String(min_len=3)
    gender = Enum(["MALE", "FEMALE", "OTHER"])
    emails = List(Format(Format.EMAIL), unique_items=True)
    contact = String(required=False)
    age = Integer(required=False)
    date_of_birth = Format(Format.DATE, name="date-of-birth")  # non python names

    class Meta:
        # Must provide contact if emails is provided
        field_dependencies = [RequiredDependency("emails", ["contact"])]


# Schema Inheritance
class Owner(Person):
    pass


class Broker(Person):
    brokerage = Integer()  # additional properity
    is_broker = Const(True)

    class Meta(Person.Meta):
        field_dependencies = [
            RequiredDependency("emails", ["contact"]),
            RequiredDependency("contact", ["emails"]),
        ]


# Nested schemas
class House(Schema):
    seller = AnyOf(Owner, Broker)  # accepts any of owner or broken
    address = List(Number, String, String)  # accept list in specific type order.
    is_ready = Boolean()
    area = Number()
    country = Const("India")
    garden_area = Number(required=False, use_default=0)
    sqtft_rate = Number(required=False, use_default=0)
    secrete_key = Number(required=False, name="__secrete_key")  # Private
    possesion_date = Format(Format.DATE)
    # Extend instance class and add properties
    class Instance(Schema.Instance):
        @property
        def cost(self):
            # Safety: fields with required=False should be checked before access.
            # Optionaly you can provide default value.
            return self.sqtft_rate * self.area

    # Provide custom meta
    class Meta:
        # Must provide area and sqtft_rate if sqtft_rate provided
        # OR v.v.
        field_dependencies = [
            RequiredDependency("area", ["sqtft_rate"]),
            RequiredDependency("sqtft_rate", ["area"]),
        ]
```


**Create and validate instances**

```python
generic = GenericSchema.instance(anything="you want", almost_anything=[1, 2, "3"])
assert len(generic.errors) == 0 # Generic schema never raises errors
assert generic.anything == "you want"
assert generic.almost_anything == [1, 2, "3"]


# Create a instances of schema
owner = Owner.instance(
    name="Test owner",
    gender="MALE",
    emails=["test@test.com"],
    date_of_birth="1989-01-01",
)

assert owner.errors == ["'contact' is a dependency of 'emails'"]
assert owner["date-of-birth"] == "1989-01-01"

test = Broker.instance(
    name="Test",
    gender="MALE",
    emails=["testtest.com", "testtest.com"], # invalid emails, duplicate emails
    contact="123456",
    brokerage=12345,
    is_broker=True,
    date_of_birth="1989-01-01",
)
assert test.errors == [
    "'testtest.com' is not a 'email'",
    "'testtest.com' is not a 'email'",
    "['testtest.com', 'testtest.com'] has non-unique elements",
]

# Owner instance
owner = Owner.instance(
    name="Nikhil Rupanawar",
    gender="MALE",
    emails=["conikhil@gmail.com"],
    contact="4545454545",
    date_of_birth="1989-09-11",
)

# House with owner
house = House.instance()
house.seller = owner
house.address = [123, "A building", "Singad road"]
house.is_ready = True
house.country = "India"
house.area = 7000
house.possesion_date = datetime.datetime.now()
assert house.cost == 0 # sqtft_rate is 0 as default
assert len(house.errors) == 0

# House with broker
another_house = House.instance(
    seller=Broker.instance(
        name="Test Rupanwar",
        gender="MALE",
        emails=["test@test.com"],
        contact="123456",
        brokerage=12345,
        is_broker=True,
        date_of_birth="2002-09-08",
    ),
    address=[123, "A building", "Baner road"],
    sqtft_rate=5000,
    area=1100,
    is_ready=True,
    country="India",
    secrete_key=12345,
    possesion_date=datetime.datetime.now()
)
another_house.validate()
assert another_house.cost == 5500000
```

**List basics**

```python
# Generic list
>>> l = List.instance([1, 23, 56, "anything"])
>>> l.append("wow")
>>> l[1:6]  # slice
>>> l.append(23)
>>> l.extend([45])
>>> l[2] = 100
>>> l.validate()  # No errors!
```

**List of types**
```python
l = List(String).instance(["only", "strings", "are", "allowed"])
assert len(l.errors) == 0  # No errors!

l = List(String).instance(["only", "strings", 60, 30])
assert [e.message for e in l.exceptions] == [
    "60 is not of type 'string'",
    "30 is not of type 'string'",
]

# list of house
houses = List(House).instance([house, another_house])
houses.validate()
houses.to_json()
```

**Validate any document/dict against the schema**

```python
House().validate(
    {
        "seller": {
            "age": 22,
            "emails": ["test@test.com", "test2@test.com"],
            "name": "nikhil",
            "gender": "MALE",
            "contact": "1234567",
            "date-of-birth": "1978-09-04",
        },
        "address": [120, "Flat A", "Sarang"],
        "area": 1234,
        "sqtft_rate": 2000,
        "garden_area": 123,
        "is_ready": True,
        "country": "India",
        "possesion_date": str(datetime.datetime.now()),
    }
)

```


**Enums and Consts**

```python

Const(2).instance(2).validate()  # won't raise error

try:
    Const(2).instance(3).validate()  # raises error
except ValidationError:
    assert True

assert Enum([1, 2, 3]).instance(3).errors == []  # no error

# Raises error
try:
    Enum([1, 2, "Three"])(5).validate()
except ValidationError:
    assert True
```

**Construct instance from document/schema**
```python
HOUSE_DATA_VALID = json.dumps(
    {
        "seller": {
            "age": 22,
            "emails": ["test@test.com", "test2@test.com"],
            "name": "nikhil",
            "gender": "MALE",
            "contact": "1234567",
            "date-of-birth": "1978-09-04",
        },
        "address": [120, "Flat A", "Sarang"],
        "area": 1234,
        "sqtft_rate": 2000,
        "garden_area": 123,
        "is_ready": True,
        "country": "India",
        "possesion_date": "2020-02-05",  # str(datetime.datetime.now()),
    }
)

h = House.from_json(HOUSE_DATA_VALID)
h.validate(check_formats=True)
```
