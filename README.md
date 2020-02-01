# jsonene
A library to define and use JSON schema as python classes.

**Inspired by**

[jsonschema](https://python-jsonschema.readthedocs.io/en/stable/)

[json-schema](https://json-schema.org/draft-07/json-schema-validation.html)

The basic idea is to provide light weight class based schema defination and data classes

**Installation**

$ git clone https://github.com/nikhil-rupanawar/jsonene.git

$ cd jasonene; python setup.py install

**Import**:
```python
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

**'Const' Field**:
```python

Const(2).instance(2).validate()  # won't raise error

try:
    Const(2).instance(3).validate()  # raises error
except ValidationError:
    assert True
```

**'Enum' Field**:
```python
# Raises error
assert Enum([1, 2, 3]).instance(3).validation_error_messages() == []  # no error

try:
    Enum([1, 2, "Three"])(5).validate()
except ValidationError:
    assert True
```

**'List' Field**:
```python

# Generic list
l = List.instance([1, 23, 56, "anything"])
# Supports normal list operations
l.append("wow")
l[1:6] # slice
l.append(23)
l.extend([45])
l[2] = 100
l.validate()
l.to_json()

# Type specific list
errors = List(String).instance(["only", "strings", "are", "allowed"]).validation_errors()
assert len(list(errors)) == 0  # No errors!

errors = List(String).instance(["only", "strings", 60, 30]).validation_errors()
# Get validation errors
assert [e.message for e in errors] == [
    "60 is not of type 'string'",
    "30 is not of type 'string'",
]
```

**Generic Schema instances**:
```python
noschema = GenericSchema.instance(anything="you want", almost_anything=[1, 2, "3"])
assert len(list(noschema.validation_errors())) == 0
assert noschema.anything == "you want"
assert noschema.almost_anything == [1, 2, "3"]
```


**'Schema' Field - Define schema/nested schema**:
```python
# Define a Schema
class Person(Schema):
    name = String()
    gender = Enum(["MALE", "FEMALE", "OTHER"])
    emails = List(Format(Format.EMAIL), unique_items=True)
    contact = String(required=False)
    age = Integer(required=False)

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
    seller = AnyOf(Owner(), Broker())  # accepts any of owner or broken
    address = List(Number, String, String)  # accept list in specific type order.
    is_ready = Boolean()
    area = Number()
    country = Const("India")
    garden_area = Number(required=False)
    sqtft_rate = Number(required=False)

    # Extend instance class and add properties
    class Instance(Schema.Instance):
        @property
        def cost(self):
            # Safety: fields with required=False should be checked before access.
            # TODO way to provide defaults
            return getattr(self, "sqtft_rate", 0) * self.area

    # Provide custom meta
    class Meta:
        # Must provide area and sqtft_rate if sqtft_rate provided
        # OR v.v.
        field_dependencies = [
            RequiredDependency("area", ["sqtft_rate"]),
            RequiredDependency("sqtft_rate", ["area"]),
        ]
```

**Use as instances**:

```python
# Create a instances using Schema
owner = Owner.instance(
    name="Nikhil Rupanawar", gender="MALE", emails=["conikhil@gmail.com"],
)

assert owner.validation_error_messages() == ["'contact' is a dependency of 'emails'"]

test = Broker.instance(
    name="Test Rupanwar",
    gender="MALE",
    emails=["testtest.com", "testtest.com"],
    contact="123456",
    brokerage=12345,
    is_broker=True,
)
assert test.validation_error_messages() == [
    "'testtest.com' is not a 'email'",
    "'testtest.com' is not a 'email'",
    "['testtest.com', 'testtest.com'] has non-unique elements",
]

owner = Owner.instance(
    name="Nikhil Rupanawar",
    gender="MALE",
    emails=["conikhil@gmail.com"],
    contact="232321344",
)
house = House.instance()
house.seller = owner
house.address = [123, "A building", "Singad road"]
house.sqtft_rate = 6000
house.area = 1100
house.is_ready = True
house.country = "India"

assert house.cost == 6600000
assert len(house.validation_error_messages()) == 0

# Another House
another_house = House.instance(
    seller=Broker.instance(
        name="Test Rupanwar",
        gender="MALE",
        emails=["test@test.com"],
        contact="123456",
        brokerage=12345,
        is_broker=True,
    ),
    address=[123, "A building", "Baner road"],
    sqtft_rate=5000,
    area=1100,
    is_ready=True,
    country="India",
)
another_house.validate()
assert another_house.cost == 5500000


# Validate any json by document
House().validate(
    {
        "seller": {
            "age": 22,
            "emails": ["test@test.com", "test2@test.com"],
            "name": "nikhil",
            "gender": "MALE",
            "contact": "1234567",
        },
        "address": [120, "Flat A", "Sarang"],
        "area": 1234,
        "sqtft_rate": 2000,
        "garden_area": 123,
        "is_ready": True,
        "country": "India",
    }
)

# generate json
houses = List(House).instance([house, another_house])
houses.validate()
houses.to_json()
```
