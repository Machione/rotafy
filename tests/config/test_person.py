import pytest
import datetime
from rotafy.config import chore, person


def basic_person_generator(name):
    c1 = chore.Chore("c1", 1, "every day", True, 2, 1, [datetime.date.today()])
    c2 = chore.Chore("c2", 1, "every day", True, 2, 1, [datetime.date.today()])
    c3 = chore.Chore("c3", 1, "every day", True, 2, 1, [datetime.date.today()])
    chores = [c1, c2]
    return person.Person(name, chores, "1234", [datetime.date.today()], [c3])


@pytest.fixture
def test_person():
    return basic_person_generator("test_person")


def test_init(test_person):
    assert test_person.name == "test_person"
    assert len(test_person.skills) == 2
    assert all(isinstance(c, chore.Chore) for c in test_person.skills)
    assert test_person.telephone == "1234"
    assert test_person.unavailable[0] == datetime.date.today()
    assert len(test_person.experience) == 1
    assert all(isinstance(c, chore.Chore) for c in test_person.experience.keys())
    assert all(x == 0 for x in test_person.experience.values())
