import pytest
import os
import toml
import datetime
from rotafy.config import config, chore, person


data = {
    "name": "test",
    "lookahead_days": 10,
    "clicksend_username": "test_username",
    "clicksend_api_key": "test_api_key",
    "message": "{{recipient}}, pleas do {{chore}} on {{date}}.",
    "default_number_of_training_sessions": 2,
    "default_number_of_shadowing_sessions": 1,
    "default_notification_days": 5,
    "chore": [
        {"name": "test_chore", "recurrence": "every day", "notify": False},
        {
            "name": "other_chore",
            "recurrence": "every day",
            "notify": 2,
            "required_training_sessions": 5,
            "required_shadowing_sessions": 5,
            "exceptions": [datetime.date.today()],
        },
        {"name": "one_more_chore", "recurrence": "every day", "notify": True},
    ],
    "person": [
        {
            "name": "John",
            "telephone": 1234,
            "skills": ["other_chore"],
            "training": ["test_chore"],
            "unavailable": [datetime.date.today()],
        },
        {"name": "Jane", "skills": ["ALL"]},
        {"name": "Janice", "training": ["ALL"]},
    ],
}

bare_data = {
    "name": "bare",
    "chore": [{"name": "test_chore", "recurrence": "every day", "notify": True}],
    "person": [{"name": "John"}],
}


def write_toml(d, fp):
    with open(fp, "w") as f:
        toml.dump(d, f)


@pytest.fixture
def test_toml_file_path(tmp_path):
    fp = os.path.join(tmp_path, "test.toml")
    write_toml(data, fp)
    return fp


@pytest.fixture
def bare_toml_file_path(tmp_path):
    fp = os.path.join(tmp_path, "bare.toml")
    write_toml(bare_data, fp)
    return fp


@pytest.fixture
def test_config(test_toml_file_path):
    return config.Config(test_toml_file_path)


@pytest.fixture
def bare_config(bare_toml_file_path):
    return config.Config(bare_toml_file_path)


def init_tester(cfg, raw_data):
    assert os.path.isfile(cfg.path)
    assert isinstance(cfg.raw, dict)

    assert cfg.name == raw_data["name"]

    assert cfg.lookahead_days == raw_data.get("lookahead_days", 14)
    assert cfg.clicksend_username == raw_data.get("clicksend_username", "")
    assert cfg.clicksend_api_key == raw_data.get("clicksend_api_key", "")
    assert len(cfg.message_template) > 0
    assert isinstance(cfg.message_template, str)

    assert len(cfg.chores) == len(raw_data["chore"])
    for i, raw_chore in enumerate(raw_data["chore"]):
        c = chore.find_chore(raw_chore["name"], cfg.chores)

        assert c.name == raw_chore["name"]
        assert c.ordinal == i
        assert c._raw_recurrence == raw_chore["recurrence"]

        if raw_chore.get("notify", False) == False:
            assert c.notify == False
        elif isinstance(raw_chore.get("notify"), bool):
            assert c.notify == raw_data.get("default_notification_days", 1)
        else:
            assert c.notify == raw_chore["notify"]

        assert c.num_training_sessions == raw_chore.get(
            "required_training_sessions",
            raw_data.get("default_number_of_training_sessions", 1),
        )
        assert c.num_shadowing_sessions == raw_chore.get(
            "required_shadowing_sessions",
            raw_data.get("default_number_of_shadowing_sessions", 1),
        )

        assert len(c.exceptions) == len(raw_chore.get("exceptions", []))
        for dt in raw_chore.get("exceptions", []):
            assert dt in c.exceptions

    assert len(cfg.people) == len(raw_data["person"])
    for raw_person in raw_data["person"]:
        p = person.find_person(raw_person["name"], cfg.people)

        assert p.name == raw_person["name"]

        if "skills" in raw_person.keys():
            for chore_name in raw_person["skills"]:
                if chore_name.lower() in ("any", "all"):
                    assert p.skills == cfg.chores
                else:
                    s = chore.find_chore(chore_name, cfg.chores)
                    assert s.name == chore_name
        else:
            assert len(p.skills) == 0

        assert p.telephone == str(raw_person.get("telephone", ""))
        assert len(p.unavailable) == len(raw_person.get("unavailable", []))
        for dt in raw_person.get("unavailable", []):
            assert dt in p.unavailable

        if "training" in raw_person.keys():
            for chore_name in raw_person["training"]:
                if chore_name.lower() in ("any", "all"):
                    assert p._raw_training == cfg.chores
                else:
                    t = chore.find_chore(chore_name, cfg.chores)
                    assert t.name == chore_name
        else:
            assert len(p.experience) == 0


def test_init(test_config, bare_config):
    init_tester(test_config, data)
    init_tester(bare_config, bare_data)


def test_repr(test_config):
    assert eval("config." + repr(test_config)) == test_config


def test_str(test_config):
    s = str(test_config)
    assert test_config.name in s
    assert "Chores:" in s
    assert "People:" in s

    for c in test_config.chores:
        assert c.name in s

    for p in test_config.people:
        assert p.name in s

    assert len(s.split("\n")) == 3 + len(test_config.chores) + len(test_config.people)


def test_eq(test_config, bare_config):
    assert test_config == test_config
    assert test_config != bare_config


def test_get_chores_from_names(test_config):
    assert len(test_config._get_chores_from_names([])) == 0
    assert test_config._get_chores_from_names(["ANY"]) == test_config.chores
    assert test_config._get_chores_from_names(["ALL"]) == test_config.chores
    assert test_config._get_chores_from_names(["aLl"]) == test_config.chores
