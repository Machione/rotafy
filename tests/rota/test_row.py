import pytest
import datetime
from rotafy.config.chore import Chore
from rotafy.config.person import Person
from rotafy.rota.assignment import Assignment
from rotafy.rota import row


today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)

all_chores = [
    Chore("c1", 1, "every day", True, 2, 1, [today]),
    Chore("c2", 1, "every day", True, 2, 1, [today]),
    Chore("c3", 1, "every day", True, 2, 1, [today]),
]

all_people = [
    Person("p1", all_chores[0:2], "1234", [today], [all_chores[2]]),
    Person("p2", [all_chores[0], all_chores[2]], "5678", [today], [all_chores[1]]),
    Person("p3", all_chores[1:], "9000", [today], [all_chores[0]]),
]

all_assignments = [
    Assignment(tomorrow, all_chores[0], all_people[0], all_people[2], False),
    Assignment(tomorrow, all_chores[1], all_people[1], None, False),
]


@pytest.fixture
def test_row():
    all_assignments.sort(key=lambda a: a.chore.name)
    all_assignments.reverse()
    return row.Row(all_assignments)


def test_init(test_row):
    for assignment in all_assignments:
        assert assignment in test_row.assignments

    assert test_row.date == all_assignments[0].date
