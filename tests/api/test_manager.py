import pytest
import datetime
from unittest.mock import Mock, patch
from rotafy.api import manager
from rotafy.config import config, chore, person
from rotafy.rota import printable, assignment, row


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    config_data = {
        "name": "Test Rota",
        "chores": [
            {"name": "Dishes", "frequency": "daily", "people": ["Alice", "Bob"]},
            {"name": "Vacuum", "frequency": "weekly", "people": ["Alice", "Bob", "Charlie"]},
        ],
        "people": [
            {"name": "Alice", "experience": ["Dishes"]},
            {"name": "Bob", "experience": ["Vacuum"]},
            {"name": "Charlie", "experience": []},
        ],
    }
    return config.Config(config_data)


@pytest.fixture
def sample_manager(sample_config, tmp_path):
    """Create a sample manager instance for testing."""
    config_file = tmp_path / "test_config.toml"
    config_file.write_text("""
        name = "Test Rota"
        [[chores]]
        name = "Dishes"
        frequency = "daily"
        people = ["Alice", "Bob"]
        [[chores]]
        name = "Vacuum"
        frequency = "weekly"
        people = ["Alice", "Bob", "Charlie"]
        [[people]]
        name = "Alice"
        experience = ["Dishes"]
        [[people]]
        name = "Bob"
        experience = ["Vacuum"]
        [[people]]
        name = "Charlie"
        experience = []
    """)
    return manager.Manager(str(config_file))


def test_init(sample_manager):
    """Test manager initialization."""
    assert sample_manager.name == "Test Rota"
    assert len(sample_manager.configuration.chores) == 2
    assert len(sample_manager.configuration.people) == 3


def test_chores_on(sample_manager):
    """Test getting chores for a specific date."""
    test_date = datetime.date(2024, 1, 1)
    chores = list(sample_manager.chores_on(test_date))
    assert len(chores) == 2
    assert any(c.name == "Dishes" for c in chores)
    assert any(c.name == "Vacuum" for c in chores)


def test_find_assignment(sample_manager):
    """Test finding assignments for a person."""
    test_date = datetime.date(2024, 1, 1)
    # First add an assignment
    sample_manager.add_person(test_date, "Dishes", "Alice")
    # Then find it
    assignment = sample_manager.find_assignment(test_date, "Alice")
    assert assignment is not None
    assert assignment.person.name == "Alice"
    assert assignment.chore.name == "Dishes"


def test_add_person(sample_manager):
    """Test adding a person to a chore."""
    test_date = datetime.date(2024, 1, 1)
    sample_manager.add_person(test_date, "Dishes", "Alice")
    assignment = sample_manager.find_assignment(test_date, "Alice")
    assert assignment is not None
    assert assignment.person.name == "Alice"
    assert assignment.chore.name == "Dishes"


def test_remove_person(sample_manager):
    """Test removing a person from a chore."""
    test_date = datetime.date(2024, 1, 1)
    # First add an assignment
    sample_manager.add_person(test_date, "Dishes", "Alice")
    # Then remove it
    sample_manager.remove_person(test_date, "Alice")
    assignment = sample_manager.find_assignment(test_date, "Alice")
    assert assignment is None


def test_add_trainee(sample_manager):
    """Test adding a trainee to a chore."""
    test_date = datetime.date(2024, 1, 1)
    # First add a primary person
    sample_manager.add_person(test_date, "Dishes", "Alice")
    # Then add a trainee
    sample_manager.add_trainee(test_date, "Dishes", "Charlie")
    assignment = sample_manager.find_assignment(test_date, "Charlie")
    assert assignment is not None
    assert assignment.trainee.name == "Charlie"
    assert assignment.person.name == "Alice"


def test_swap(sample_manager):
    """Test swapping two people's assignments."""
    test_date = datetime.date(2024, 1, 1)
    # First add two assignments
    sample_manager.add_person(test_date, "Dishes", "Alice")
    sample_manager.add_person(test_date, "Vacuum", "Bob")
    # Then swap them
    sample_manager.swap(test_date, "Alice", "Bob")
    # Check the swap worked
    alice_assignment = sample_manager.find_assignment(test_date, "Alice")
    bob_assignment = sample_manager.find_assignment(test_date, "Bob")
    assert alice_assignment.chore.name == "Vacuum"
    assert bob_assignment.chore.name == "Dishes"


def test_replace(sample_manager):
    """Test replacing one person with another."""
    test_date = datetime.date(2024, 1, 1)
    # First add an assignment
    sample_manager.add_person(test_date, "Dishes", "Alice")
    # Then replace Alice with Charlie
    sample_manager.replace(test_date, "Alice", "Charlie")
    # Check the replacement worked
    old_assignment = sample_manager.find_assignment(test_date, "Alice")
    new_assignment = sample_manager.find_assignment(test_date, "Charlie")
    assert old_assignment is None
    assert new_assignment is not None
    assert new_assignment.person.name == "Charlie"
    assert new_assignment.chore.name == "Dishes"


def test_check_and_heal(sample_manager):
    """Test the check and heal functionality."""
    test_date = datetime.date(2024, 1, 1)
    # Add some assignments
    sample_manager.add_person(test_date, "Dishes", "Alice")
    sample_manager.add_person(test_date, "Vacuum", "Bob")
    # Run check and heal
    sample_manager.check_and_heal()
    # Verify assignments still exist
    alice_assignment = sample_manager.find_assignment(test_date, "Alice")
    bob_assignment = sample_manager.find_assignment(test_date, "Bob")
    assert alice_assignment is not None
    assert bob_assignment is not None


@patch('rotafy.api.notifier.Notifier')
def test_notify(mock_notifier, sample_manager):
    """Test the notification functionality."""
    test_date = datetime.date(2024, 1, 1)
    # Add an assignment
    sample_manager.add_person(test_date, "Dishes", "Alice")
    # Run notify
    sample_manager.notify()
    # Verify notifier was called
    mock_notifier.return_value.send.assert_called_once()


def test_row_weight(sample_manager):
    """Test the row weight calculation."""
    test_date = datetime.date(2024, 1, 1)
    # Create a row with some assignments
    sample_manager.add_person(test_date, "Dishes", "Alice")
    sample_manager.add_person(test_date, "Vacuum", "Bob")
    # Get the row and calculate its weight
    test_row = sample_manager.rota[test_date]
    weight = sample_manager.row_weight(test_row)
    assert isinstance(weight, float)
    assert weight >= 0


def test_all_independently_valid_assignments(sample_manager):
    """Test getting all valid assignments for a chore."""
    test_date = datetime.date(2024, 1, 1)
    # Get valid assignments for Dishes
    valid_assignments = list(sample_manager.all_independently_valid_assignments(test_date, sample_manager.configuration.chores[0]))
    assert len(valid_assignments) > 0
    assert all(isinstance(a, assignment.Assignment) for a in valid_assignments)
    assert all(a.chore.name == "Dishes" for a in valid_assignments)


def test_assign_chores_on(sample_manager):
    """Test assigning chores for a specific date."""
    test_date = datetime.date(2024, 1, 1)
    # Assign chores
    sample_manager.assign_chores_on(test_date)
    # Verify assignments were made
    row = sample_manager.rota[test_date]
    assert row is not None
    assert len(row.assignments) > 0


def test_fill(sample_manager):
    """Test filling the rota with assignments."""
    # Fill the rota
    sample_manager.fill()
    # Verify the rota has assignments
    assert len(sample_manager.rota.rows) > 0
    for row in sample_manager.rota.rows:
        assert len(row.assignments) > 0
