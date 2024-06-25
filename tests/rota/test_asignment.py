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


def generate_test_assignment(date, chore, person, trainee, notification_sent):
    a = assignment.Assignment(date, chore, person, trainee, notification_sent)
    return a


@pytest.fixture
def test_assignment(test_chore, test_person, trainee_person):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    return generate_test_assignment(
        tomorrow, test_chore, test_person, trainee_person, False
    )


@pytest.fixture
def no_trainee_assignment(test_chore, test_person):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    return generate_test_assignment(tomorrow, test_chore, test_person, None, False)


def test_init(test_assignment, test_chore, test_person, trainee_person):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    assert test_assignment.date == tomorrow
    assert test_assignment.chore == test_chore
    assert test_assignment.person == test_person
    assert test_assignment.trainee == trainee_person
    assert test_assignment.notification_sent == False


def test_repr(test_assignment):
    assert eval("assignment." + repr(test_assignment)) == test_assignment


def test_str(test_assignment, no_trainee_assignment):
    assert str(no_trainee_assignment) == no_trainee_assignment.person.name
    assert str(test_assignment).startswith(test_assignment.person.name)
    assert test_assignment.trainee.name in str(test_assignment)
    assert "shadowing" in str(test_assignment)
    test_assignment.trainee.add_to_experience(all_chores[0])
    test_assignment.trainee.add_to_experience(all_chores[0])
    assert str(test_assignment).startswith(test_assignment.trainee.name)
    assert test_assignment.person.name in str(test_assignment)
    assert "supervised" in str(test_assignment)


def test_eq(
    test_assignment, no_trainee_assignment, test_chore, test_person, trainee_person
):
    assert test_assignment == test_assignment

    day_after_tomorrow = datetime.date.today() + datetime.timedelta(days=2)
    diff_date = generate_test_assignment(
        day_after_tomorrow, test_chore, test_person, trainee_person, False
    )
    assert test_assignment != diff_date

    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    diff_chore = generate_test_assignment(
        tomorrow, all_chores[1], test_person, trainee_person, False
    )
    assert test_assignment != diff_chore

    diff_person = Person(
        "other_person",
        all_chores[:-1],
        "9000",
        [datetime.date.today()],
        [all_chores[-1]],
    )
    diff_person_assignment = generate_test_assignment(
        tomorrow, test_chore, diff_person, trainee_person, False
    )
    assert test_assignment != diff_person_assignment

    diff_trainee = Person(
        "other_trainee",
        all_chores[1:],
        "9000",
        [datetime.date.today()],
        [all_chores[0]],
    )
    diff_trainee_assignment = generate_test_assignment(
        tomorrow, test_chore, test_person, diff_trainee, False
    )
    assert test_assignment != diff_trainee_assignment
    assert test_assignment != no_trainee_assignment

    notified = generate_test_assignment(
        tomorrow, test_chore, test_person, trainee_person, True
    )
    assert test_assignment == notified
