from __future__ import absolute_import
from demos import Person, Owner, House, Broker, Gender, List, Schema
from jsonene.factories import SchemaFactory, ListSchemaFactory
from factory import SubFactory, fuzzy, Sequence, Iterator, LazyAttribute
import string
import datetime
import pytz

st_date = pytz.utc.localize(datetime.datetime.now())
end_date = st_date + datetime.timedelta(days=7)


class EmailsFactory(ListSchemaFactory):
    email = LazyAttribute(lambda o: f"{o.factory_parent.name}@example.org")

    class Meta(object):
        model = List


class PersonFactory(SchemaFactory):
    name = fuzzy.FuzzyText()
    gender = fuzzy.FuzzyChoice([e.value for e in Gender])
    emails = SubFactory(EmailsFactory)
    contact = fuzzy.FuzzyText(chars=[unicode(n) for n in xrange(10)])
    age = fuzzy.FuzzyInteger(low=0, high=100)
    date_of_birth = fuzzy.FuzzyDateTime(st_date, end_dt=end_date)

    class Meta(object):
        model = Person


class OwnerFactory(PersonFactory):
    class Meta(object):
        model = Owner


class BrokerFactory(PersonFactory):
    class Meta(object):
        model = Broker


class AddressFactory(ListSchemaFactory):
    house_no = fuzzy.FuzzyInteger(low=1, high=100)
    street_address = fuzzy.FuzzyText(suffix=u" road")
    area = fuzzy.FuzzyText()

    class Meta(object):
        model = List


class HouseFactory(SchemaFactory):
    seller = SubFactory(OwnerFactory)
    address = SubFactory(AddressFactory)
    is_ready = fuzzy.FuzzyChoice([True, False])
    area = fuzzy.FuzzyFloat(low=400, high=3000, precision=2)
    country = u"India"
    garden_area = fuzzy.FuzzyFloat(low=400, high=3000, precision=2)
    sqtft_rate = fuzzy.FuzzyFloat(low=0, high=50000, precision=2)
    possesion_date = fuzzy.FuzzyDateTime(st_date, end_dt=end_date)

    class Meta(object):
        model = House


house = HouseFactory.create()
house.validate(check_formats=True)
assert isinstance(house.seller, Schema.Instance)

house2 = HouseFactory.create()
del house2.seller
assert house2.errors == [u"'seller' is a required property"]
