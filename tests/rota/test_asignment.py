import pytest
import datetime
from rotafy.config import chore, person
from rotafy.rota import assignment


all_chores = [
    chore.Chore("test_chore", 1, "every day", True, 2, 1, [datetime.date.today()]),
    chore.Chore("other_chore", 1, "every day", True, 2, 1, [datetime.date.today()]),
    chore.Chore("training", 1, "every day", True, 2, 1, [datetime.date.today()]),
]


@pytest.fixture
def test_chore():
    return all_chores[0]


@pytest.fixture
def test_person():
    p = person.Person(
        "test_person",
        all_chores[:-1],
        "1234",
        [datetime.date.today()],
        [all_chores[-1]],
    )
    return p


@pytest.fixture
def trainee_person():
    p = person.Person(
        "test_person", all_chores[1:], "5678", [datetime.date.today()], [all_chores[0]]
    )
    return p


@pytest.fixture
def test_assignment(test_chore, test_person, trainee_person):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    a = assignment.Assignment(tomorrow, test_chore, test_person, trainee_person, False)
    return a


def test_init(test_assignment, test_chore, test_person, trainee_person):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    assert test_assignment.date == tomorrow
    assert test_assignment.chore == test_chore
    assert test_assignment.person == test_person
    assert test_assignment.trainee == trainee_person
    assert test_assignment.notification_sent == False
