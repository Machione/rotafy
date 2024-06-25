import pytest
import datetime
from rotafy.config.chore import Chore
from rotafy.config.person import Person
from rotafy.rota.assignment import Assignment
from rotafy.rota import row


today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)

c1 = Chore("c1", 1, "every day", True, 2, 1, [today])
c2 = Chore("c2", 1, "every day", True, 2, 1, [today])
c3 = Chore("c3", 1, "every day", True, 2, 1, [today])
all_chores = [c1, c2, c3]

p1 = Person("p1", [c1, c2], "1234", [today], [c3])
p2 = Person("p2", [c1, c3], "5678", [today], [c2])
p3 = Person("p3", [c2, c3], "9000", [today], [c1])
p4 = Person("p4", [], "9999", [today], [c1])
all_people = [p1, p2, p3, p4]

# Purposefully in the incorrect order (according to chore.ordinal value).
all_assignments = [
    Assignment(tomorrow, c2, p3, None, False),
    Assignment(tomorrow, c1, p2, p4, False),
]


@pytest.fixture
def test_row():
    return row.Row(all_assignments)


def test_init(test_row):
    for assignment in all_assignments:
        assert assignment in test_row.assignments

    assert test_row.date == all_assignments[0].date


def test_getitem(test_row):
    assert test_row[c1] == all_assignments[1]
    assert test_row[c2] == all_assignments[0]
    assert test_row[c3] == None


def test_setitem(test_row):
    # Change c1 from p2 to p1.
    reassignment = Assignment(tomorrow, c1, p1, p4)
    test_row[c1] = reassignment
    assert test_row[c1] == reassignment
    assert len(test_row.assignments) == 2

    # Brand new assignment
    new_assignment = Assignment(tomorrow, c3, p2)
    test_row[c3] = new_assignment
    assert test_row[c3] == new_assignment
    assert len(test_row.assignments) == 3


def test_delitem(test_row):
    del test_row[c3]
    assert len(test_row.assignments) == 2
    assert test_row[c1] == all_assignments[1]
    assert test_row[c2] == all_assignments[0]
    assert test_row[c3] == None

    del test_row[c1]
    assert len(test_row.assignments) == 1
    assert test_row[c1] == None