import pytest
import datetime
from dateutil import rrule
from rotafy.config import chore


def basic_chore_generator(name):
    return chore.Chore(
        name, 
        1, 
        "every day",
        True,
        2,
        1,
        [datetime.date.today()]
    )

@pytest.fixture
def test_chore():
    return basic_chore_generator("test_chore")

@pytest.fixture
def other_chore():
    return basic_chore_generator("other_chore")


def test_init(test_chore):
    assert test_chore.name == "test_chore"
    assert test_chore.ordinal == 1
    assert test_chore._raw_recurrence == "every day"
    assert isinstance(test_chore.recurring_rule, rrule.rrule)
    assert test_chore.notify == True
    assert test_chore.num_training_sessions == 2
    assert test_chore.num_shadowing_sessions == 1
    assert len(test_chore.exceptions) == 1
    assert test_chore.exceptions[0] == datetime.date.today()

def test_name():
    with pytest.raises(ValueError):
        basic_chore_generator("")
        basic_chore_generator(None)
        basic_chore_generator("    ")
    
    malformed = basic_chore_generator("  malformed  ")
    assert malformed.name == "malformed"

def test_repr(test_chore):
    assert eval("chore." + repr(test_chore)) == test_chore

def test_str(test_chore):
    assert str(test_chore) == test_chore.name

def test_eq(test_chore, other_chore):
    assert test_chore == test_chore
    assert test_chore != other_chore

def test_hash(test_chore, other_chore):
    assert hash(test_chore) == hash(test_chore)
    assert hash(test_chore) != hash(other_chore)

def test_on(test_chore):
    assert test_chore.on(datetime.date.today()) == False
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    assert test_chore.on(tomorrow) == True

def test_next(test_chore):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)
    day_after_tomorrow = tomorrow + datetime.timedelta(days=1)
    assert test_chore.next(today) == tomorrow
    assert test_chore.next(tomorrow) == day_after_tomorrow
    assert test_chore.next(yesterday) == tomorrow


@pytest.mark.parametrize("recurrence", [
    ("on weekdays"),
    ("every fourth of the month from jan 1 2010 to dec 25th 2020"),
    ("each thurs until next month"),
    ("once a year on the fourth thursday in november"),
    ("tuesdays and thursdays at 3:15"),
    ("wednesdays at 9 o'clock"),
    ("fridays at 11am"),
    ("daily except in June"),
    ("daily except on June 23rd and July 4th"),
    ("every monday except each 2nd monday in March"),
    ("fridays twice"),
    ("fridays 3x"),
    ("every other friday for 5 times"),
    ("every 3 fridays from november until february"),
    ("fridays starting in may for 10 occurrences"),
    ("tuesdays for the next six weeks"),
    ("every Mon-Wed for the next 2 months"),
    ("every Mon thru Wed for the next year"),
    ("every other Fri for the next three years"),
    ("monthly on the first and last instance of wed and fri"),
    ("every Tue and Fri in week 14"),
    ("every year on Dec 25")
])
def test_generate_rrule(recurrence):
    actual = chore.generate_rrule(recurrence)
    assert isinstance(actual, (rrule.rrule, rrule.rruleset))


def test_find_chore(test_chore, other_chore):
    chore_list = [test_chore, other_chore]
    
    assert chore.find_chore("test_chore", chore_list) == test_chore
    assert chore.find_chore("other_chore", chore_list) == other_chore
    assert chore.find_chore("TEST_CHORE", chore_list) == test_chore
    assert chore.find_chore("TeSt_ChOrE", chore_list) == test_chore
    
    with pytest.raises(chore.ChoreNotFound):
        chore.find_chore("something_else", chore_list)