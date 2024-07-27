import pytest
import clicksend_client
import jinja2
import datetime
from rotafy.rota import printable, assignment
from rotafy.config.chore import Chore
from rotafy.config.person import Person
from rotafy.api import notifier


all_chores = [
    Chore("test_chore", 1, "every day", True, 2, 1, []),
    Chore("other_chore", 1, "every day", True, 2, 1, [datetime.date.today()]),
    Chore("training", 1, "every day", True, 2, 1, [datetime.date.today()]),
]

test_chore = all_chores[0]
tomorrow = tomorrow = datetime.date.today() + datetime.timedelta(days=1)
person = Person(
    "person", all_chores[:-1], "1234", [datetime.date.today()], [all_chores[-1]]
)
trainee = Person(
    "trainee", all_chores[1:], "5678", [datetime.date.today()], [all_chores[0]]
)


@pytest.fixture
def test_assignment():
    return assignment.Assignment(tomorrow, test_chore, person, trainee, False)


@pytest.fixture
def no_trainee_assignment():
    return assignment.Assignment(tomorrow, test_chore, person, None, False)


@pytest.fixture
def test_notifier():
    n = notifier.Notifier(
        "test1@test.com",
        "D83DED51-9E35-4D42-9BB9-0E34B7CA85AE",
        "Hi {{recipient}}! On {{date}}, {{chore}} will be handled by {{assignment}}.",
    )
    return n


def test_init(test_notifier):
    assert isinstance(test_notifier.clicksend_api, clicksend_client.SMSApi)
    assert isinstance(test_notifier.template, jinja2.Template)
    assert len(test_notifier.queue) == 0


def test_format_upcoming_date(test_notifier):
    today = datetime.date.today()
    formatted_today = test_notifier.format_upcoming_date(today)
    assert formatted_today.startswith(today.strftime("%A"))
    assert f"({printable.ordinal(today.day)})" in formatted_today

    almost_week_away = today + datetime.timedelta(days=6)
    formatted_almost_week_away = test_notifier.format_upcoming_date(almost_week_away)
    assert formatted_almost_week_away.startswith(almost_week_away.strftime("%A"))
    assert f"({printable.ordinal(almost_week_away.day)})" in formatted_almost_week_away

    week_away = today + datetime.timedelta(days=7)
    formatted_week_away = test_notifier.format_upcoming_date(week_away)
    assert formatted_week_away == printable.human_readable_date(week_away, True, False)


def test_add_to_queue(test_notifier, test_assignment):
    assert len(test_notifier.queue) == 0

    test_notifier.add_to_queue(person, test_assignment)
    assert len(test_notifier.queue) == 1
    assert isinstance(test_notifier.queue[0], clicksend_client.SmsMessage)
    assert test_notifier.queue[0].source == "Rotafy"
    assert len(test_notifier.queue[0].body) > 0
    assert test_notifier.queue[0].to == person.telephone

    test_notifier.add_to_queue(person, test_assignment)
    assert len(test_notifier.queue) == 2


def test_message_from_assignment(test_notifier, test_assignment, no_trainee_assignment):
    assert len(test_notifier.queue) == 0

    test_notifier.message_from_assignment(test_assignment)
    assert len(test_notifier.queue) == 2
    recipients = [m.to for m in test_notifier.queue]
    assert test_assignment.person.telephone in recipients
    assert test_assignment.trainee.telephone in recipients

    test_notifier.message_from_assignment(no_trainee_assignment)
    assert len(test_notifier.queue) == 3
    recipients = [m.to for m in test_notifier.queue]
    assert no_trainee_assignment.person.telephone in recipients
