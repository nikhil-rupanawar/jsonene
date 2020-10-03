from jsonene.fields import Integer, String, Const, Format, List, SchemaType, Null
from jsonene.operators import AnyOf, Not
from pprint import pprint

print(Integer.Field().validate_instance(1))
print(List.Field(String, Integer, String).validate_instance(['1', 2]))
l = List.deserialize(
    List.Field(String, Integer, String),
    ['1', '2', '3', 1, 2]
)



class Person(SchemaType):
    age = Integer.Field()
    name = String.Field(null=False, blank=False)
    conutry = Const.Field('India')

class Engineer(Person):
    degree = String.Field()


class House(SchemaType):
    owner = AnyOf(Person).Field()


class EngineersHouse(House):
    owner = Engineer.Field() 


#pprint(Person.Field().json_schema)
#pprint(House.Field().json_schema)
pprint(EngineersHouse.Field().json_schema)

p = Person(age=99, name='Nikhil', conutry='India')
pprint(p.validation_errors())

h = House(owner=p)
pprint(h.validation_errors())


e = Engineer(age=99, name='Nikhil', conutry='India', degree='BE')
eh = EngineersHouse(owner=e)
pprint(eh)
pprint(eh.validation_errors())

data = {'owner': {'age': 99, 'conutry': 'India', 'degree': 'BE', 'name': 'Nikhil'}}
wow = EngineersHouse.deserialize(data)
print(wow['owner'])

class EngineerSociety(SchemaType):
    houses = List.Field(EngineersHouse)


es = EngineerSociety(houses=List([eh, wow]))
es.validate()
data = es.serialize()
print(data)
EngineerSociety.deserialize(data)




