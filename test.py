from jsonene.fields import Integer, String, Const, Format, List, SchemaType, Null
from jsonene.operators import AnyOf, Not
from pprint import pprint


print(Integer.asField().validate_instance(1))
print(List.asField(String, Integer, String).validate_instance(['1', 2, '3']))


class Person(SchemaType):
    age = Integer.asField()
    name = String.asField(null=False, blank=False)
    conutry = Const.asField('India')


class House(SchemaType):
    owner = AnyOf(Person, Null).asField()


pprint(Person.asField().to_json_schema())
pprint(House.asField().to_json_schema())

p = Person(age=99, name='', conutry='India')
pprint(p.validation_errors())

h = House(owner=p)
pprint(h.validation_errors())
