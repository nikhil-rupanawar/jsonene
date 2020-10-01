from jsonene.fields import Integer, String, Const, Format, List, SchemaType

class Test(SchemaType):
    age = Integer.asField()
    name = String.asField()

print(list(Test().validation_errors()))
