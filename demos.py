import datetime
import json
import enum
from jsonene.fields import (
    Boolean,
    List,
    Null,
    Const,
    Enum,
    Number,
    Integer,
    Schema,
    String,
    Format,
)
from jsonene.operators import AllOf, AnyOf, OneOf, Not
from jsonene.constraints import RequiredDependency
from jsonene.exceptions import ValidationError


class Gender(enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


# Define a Schema
class Person(Schema):
    name = String.asField(min_len=3, title="Your full name")
    gender = Enum.asField(Gender)  # Any iterable
    emails = List.asField(
        Format.asField(Format.EMAIL), unique_items=True, description="List of unique email ids"
    )
    contact = String.asField(required=False)
    age = Integer.asField(required=False, use_default=0)
    date_of_birth = Format.asField(Format.DATE, name="date-of-birth")  # non python names

    class Instance(Schema.Instance):
        @property
        def prompt(self):
            return f"{self.name}, {self.age} years {self.gender}"

    class Meta:
        # Must provide contact if emails is provided
        field_dependencies = [RequiredDependency("emails", ["contact"])]


# Schema Inheritances


class Male(Person):
    gender = Const.asField(Gender.MALE, use_default=Gender.MALE)


class Female(Person):
    gender = Const.asField(Gender.FEMALE, use_default=Gender.FEMALE)


class Owner(Person):
    pass


class Broker(Person):
    brokerage = Integer.asField()  # additional properity
    is_broker = Const.asField(True)

    class Meta(Person.Meta):
        field_dependencies = [
            RequiredDependency("emails", ["contact"]),
            RequiredDependency("contact", ["emails"]),
        ]


# Nested schemas
class House(Schema):
    seller = AnyOf(Owner, Broker)  # accepts any of owner or broken
    address = List.asField(Integer, String, String)  # accept list in specific type order.
    is_ready = Boolean()
    area = Number.asField()
    country = Const.asField("India")
    garden_area = Number.asField(required=False, use_default=0)
    sqtft_rate = Number.asField(required=False, use_default=0)
    secrete_key = Number.asField(required=False, name="__secrete_key")
    possesion_date = Format.asField(Format.DATE)

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


Const.asField(2).instance(2).validate()  # won't raise error

try:
    Const.asField(2).instance(3).validate()  # raises error
except ValidationError:
    assert True

assert Enum.asField([1, 2, 3]).instance(3).errors == []  # no error

# Raises error
try:
    Enum.asField([1, 2, "Three"])(5).validate()
except ValidationError:
    assert True

# Lists

# Generic list
l = List.instance([1, 23, 56, "anything"])
l.append("wow")
l[1:6]  # slice
l.append(23)
l.extend([45])
l[2] = 100
l.validate()  # No errors!

# List accepting only string type
l = List.asField(String).instance(["only", "strings", "are", "allowed"])
assert len(l.errors) == 0  # No errors!

l = List.asField(String).instance(["only", "strings", 60, 30])
assert [e.message for e in l.exceptions] == [
    "60 is not of type 'string'",
    "30 is not of type 'string'",
]

# Instances
generic = GenericSchema.instance(anything="you want", almost_anything=[1, 2, "3"])
assert len(generic.errors) == 0
assert generic.anything == "you want"
assert generic.almost_anything == [1, 2, "3"]

wonder_woman = Female.instance(
    name="Wonder Woman",
    emails=["wonder@wonder.com"],
    contact="same as email",
    date_of_birth="2017-05-15",
)

wonder_woman.validate(check_formats=True)
assert wonder_woman.gender == Gender.FEMALE

# Create a instances using Schema
owner = Owner.instance(
    name="Rasika",
    gender="Female",
    emails=["test@test.com"],
    date_of_birth="1989-01-01",
)


assert owner.prompt == "Rasika, 0 years Female"
assert owner.errors == ["'contact' is a dependency of 'emails'"]
assert owner["date-of-birth"] == "1989-01-01"
assert owner["date-of-birth"] == owner.date_of_birth

test = Broker.instance(
    name="Suresh",
    gender="Male",
    emails=["testtest.com", "testtest.com"],
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

owner = Owner.instance(
    name="Nikhil Rupanawar",
    gender="Male",
    emails=["conikhil@gmail.com"],
    contact="4545454545",
    date_of_birth="1989-09-11",
)
house = House.instance()
house.seller = owner
house.address = [123, "A building", "Singad road"]
house.is_ready = True
house.country = "India"
house.area = 7000
house.possesion_date = "1989-09-11"
assert house.cost == 0  # sqtft_rate is 0 as default
assert len(house.errors) == 0


# Another House
another_house = House.instance(
    seller=Broker.instance(
        name="Test Rupanwar",
        gender="Male",
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
    possesion_date=str(datetime.datetime.now()),
)
another_house.validate()
assert another_house.cost == 5500000
assert another_house.secrete_key == another_house["__secrete_key"]

# Validate any json by document
House().validate(
    {
        "seller": {
            "age": 22,
            "emails": ["test@test.com", "test2@test.com"],
            "name": "nikhil",
            "gender": "Male",
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

# generate json
houses = List.asField(House).instance([house, another_house])
houses.validate()
houses.to_json()


HOUSE_DATA_VALID = json.dumps(
    {
        "seller": {
            "age": 22,
            "emails": ["test@test.com", "test2@test.com"],
            "name": "nikhil",
            "gender": "Male",
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
json.loads(h.to_json())
