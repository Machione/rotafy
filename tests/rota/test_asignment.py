import pytest
import datetime
from rotafy.config.chore import Chore
from rotafy.config.person import Person
from rotafy.rota import assignment


all_chores = [
    Chore("test_chore", 1, "every day", True, 2, 1, [datetime.date.today()]),
    Chore("other_chore", 1, "every day", True, 2, 1, [datetime.date.today()]),
    Chore("training", 1, "every day", True, 2, 1, [datetime.date.today()]),
]


@pytest.fixture
def test_chore():
    return all_chores[0]


@pytest.fixture
def test_person():
    p = Person(
        "test_person",
        all_chores[:-1],
        "1234",
        [datetime.date.today()],
        [all_chores[-1]],
    )
    return p


@pytest.fixture
def trainee_person():
    p = Person(
        "trainee_person",
        all_chores[1:],
        "5678",
        [datetime.date.today()],
        [all_chores[0]],
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


def test_repr(test_assignment):
    assert eval("assignment." + repr(test_assignment)) == test_assignment
