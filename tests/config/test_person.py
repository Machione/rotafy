import pytest
import datetime
from rotafy.config.chore import Chore
from rotafy.config import person


all_chores = [
    Chore("c1", 1, "every day", True, 2, 1, [datetime.date.today()]),
    Chore("c2", 1, "every day", True, 2, 1, [datetime.date.today()]),
    Chore("c3", 1, "every day", True, 2, 1, [datetime.date.today()]),
]


def basic_person_generator(name):
    p = person.Person(
        name, all_chores[:-1], "1234", [datetime.date.today()], [all_chores[-1]]
    )
    return p


@pytest.fixture
def test_person():
    return basic_person_generator("test_person")


@pytest.fixture
def other_person():
    return basic_person_generator("other_person")


@pytest.fixture
def new_chore():
    return Chore("unseen", 1, "every day", True, 2, 1, [datetime.date.today()])


def test_init(test_person):
    assert test_person.name == "test_person"
    assert len(test_person.skills) == 2
    assert all(isinstance(c, Chore) for c in test_person.skills)
    assert test_person.telephone == "1234"
    assert list(test_person.unavailable)[0] == datetime.date.today()
    assert len(test_person.experience) == 1
    assert all(isinstance(c, Chore) for c in test_person.experience.keys())
    assert all(x == 0 for x in test_person.experience.values())


def test_name():
    with pytest.raises(person.NoPersonName):
        basic_person_generator("")
        basic_person_generator(None)
        basic_person_generator("    ")

    malformed = basic_person_generator("  malformed  ")
    assert malformed.name == "malformed"


def test_repr(test_person):
    assert eval("person." + repr(test_person)) == test_person


def test_str(test_person):
    assert str(test_person) == test_person.name


def test_eq(test_person, other_person):
    assert test_person == test_person
    assert test_person != other_person

    same_name = person.Person(
        test_person.name,
        test_person.skills,
        "5678",
        test_person.unavailable,
        test_person._raw_training,
    )
    assert test_person != same_name

    same_telephone = person.Person(
        "same_telephone",
        test_person.skills,
        test_person.telephone,
        test_person.unavailable,
        test_person._raw_training,
    )
    assert test_person != same_telephone


def test_hash(test_person, other_person):
    assert hash(test_person) == hash(test_person)
    assert hash(test_person) != hash(other_person)

    same_name = person.Person(
        test_person.name,
        test_person.skills,
        "5678",
        test_person.unavailable,
        test_person._raw_training,
    )
    assert hash(test_person) != hash(same_name)

    same_telephone = person.Person(
        "same_telephone",
        test_person.skills,
        test_person.telephone,
        test_person.unavailable,
        test_person._raw_training,
    )
    assert hash(test_person) != hash(same_telephone)


def test_qualified(test_person):
    for chore in all_chores[:-1]:
        assert test_person.qualified(chore) == True

    assert test_person.qualified(all_chores[-1]) == False


def test_is_learning(test_person):
    for chore in all_chores[:-1]:
        assert test_person.is_learning(chore) == False

    assert test_person.is_learning(all_chores[-1]) == True


def test_add_to_experience(test_person, new_chore):
    # The chores require 2 training sessions (shadowing someone else) and 1
    # shadowing session (shadowed by someone else)
    training_chore = all_chores[-1]

    assert test_person.experience[training_chore] == 0
    assert training_chore not in test_person.skills

    test_person.add_to_experience(training_chore)
    assert test_person.experience[training_chore] == 1
    assert training_chore not in test_person.skills

    test_person.add_to_experience(training_chore)
    assert test_person.experience[training_chore] == 2
    assert training_chore not in test_person.skills

    # Complete training
    test_person.add_to_experience(training_chore)
    assert training_chore not in test_person.experience.keys()
    assert training_chore in test_person.skills

    # Overdo training should have no effect
    test_person.add_to_experience(training_chore)
    assert training_chore not in test_person.experience.keys()
    assert training_chore in test_person.skills

    # Adding a brand new chore should be allowed
    assert new_chore not in test_person.experience.keys()
    assert new_chore not in test_person.skills

    test_person.add_to_experience(new_chore)
    assert test_person.experience[new_chore] == 1
    assert new_chore not in test_person.skills


def test_reduce_experience(test_person, new_chore):
    # The chores require 2 training sessions (shadowing someone else) and 1
    # shadowing session (shadowed by someone else)
    training_chore = all_chores[-1]

    assert test_person.experience[training_chore] == 0

    # Experience should never fall below zero
    test_person.reduce_experience(training_chore)
    assert test_person.experience[training_chore] == 0

    test_person.add_to_experience(training_chore)
    assert test_person.experience[training_chore] == 1
    test_person.reduce_experience(training_chore)
    assert test_person.experience[training_chore] == 0

    # Completed training can be revoked
    while training_chore not in test_person.skills:
        test_person.add_to_experience(training_chore)

    test_person.reduce_experience(training_chore)
    assert training_chore not in test_person.skills
    assert test_person.experience[training_chore] == 2

    # Reducing a brand new chore should be allowed
    assert new_chore not in test_person.experience.keys()
    assert new_chore not in test_person.skills

    test_person.reduce_experience(new_chore)
    assert test_person.experience[new_chore] == 0
    assert new_chore not in test_person.skills


def test_is_shadowing(test_person, new_chore):
    # The chores require 2 sessions shadowing someone else.
    training_chore = all_chores[-1]

    assert test_person.is_shadowing(training_chore) == True
    test_person.add_to_experience(training_chore)  # 1
    assert test_person.is_shadowing(training_chore) == True
    test_person.add_to_experience(training_chore)  # 2
    assert test_person.is_shadowing(training_chore) == False
    test_person.add_to_experience(training_chore)  # 3 - complete
    assert test_person.is_shadowing(training_chore) == False

    assert test_person.is_shadowing(new_chore) == False


def test_is_being_observed(test_person, new_chore):
    # The chores require 2 sessions shadowing someone else then 1 session being
    # observed by someone else
    training_chore = all_chores[-1]

    assert test_person.is_being_observed(training_chore) == False
    test_person.add_to_experience(training_chore)  # 1
    assert test_person.is_being_observed(training_chore) == False
    test_person.add_to_experience(training_chore)  # 2
    assert test_person.is_being_observed(training_chore) == True
    test_person.add_to_experience(training_chore)  # 3 - complete
    assert test_person.is_being_observed(training_chore) == False

    assert test_person.is_shadowing(new_chore) == False


def test_available(test_person):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)

    assert test_person.available(today) == False
    assert test_person.available(yesterday) == True
    assert test_person.available(tomorrow) == True


def test_can_do(test_person):
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    assert test_person.can_do(all_chores[0], today) == False
    assert test_person.can_do(all_chores[0], tomorrow) == True

    assert test_person.can_do(all_chores[-1], today) == False
    assert test_person.can_do(all_chores[-1], tomorrow) == False


def test_can_be_trained(test_person):
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    assert test_person.can_be_trained(all_chores[0], today) == False
    assert test_person.can_be_trained(all_chores[0], tomorrow) == False

    assert test_person.can_be_trained(all_chores[-1], today) == False
    assert test_person.can_be_trained(all_chores[-1], tomorrow) == True


def test_find_person(test_person, other_person):
    person_list = [test_person, other_person]

    assert person.find_person("test_person", person_list) == test_person
    assert person.find_person("other_person", person_list) == other_person
    assert person.find_person("TEST_PERSON", person_list) == test_person
    assert person.find_person("TeSt_PeRsOn", person_list) == test_person

    with pytest.raises(person.PersonNotFound):
        person.find_person("something_else", person_list)
