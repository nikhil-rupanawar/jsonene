from jsonene.fields import Integer, String, Const, Format, List, SchemaType, Null
from jsonene.operators import AnyOf, Not
from pprint import pprint

print(Integer.asField().validate_instance(1))
print(List.asField(String, Integer, String).validate_instance(['1', 2]))
l = List.deserialize(
    List.asField(String, Integer, String),
    ['1', '2', '3', 1, 2]
)



class Person(SchemaType):
    age = Integer.asField()
    name = String.asField(null=False, blank=False)
    conutry = Const.asField('India')

class Engineer(Person):
    degree = String.asField()


class House(SchemaType):
    owner = AnyOf(Person).asField()


class EngineersHouse(House):
    owner = Engineer.asField() 


#pprint(Person.asField().json_schema)
#pprint(House.asField().json_schema)
pprint(EngineersHouse.asField().json_schema)

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
    houses = List.asField(EngineersHouse)


es = EngineerSociety(houses=List([eh, wow]))
es.validate()
data = es.serialize()
print(data)
EngineerSociety.deserialize(data)




