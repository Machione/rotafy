import pytest
import datetime
from rotafy.rota import printable, rota


@pytest.fixture
def test_printable():
    return printable.PrintableRota("test_printable")


@pytest.fixture
def loadable_printable():
    r = printable.PrintableRota("loadable_printable")
    r.file_path = "tests/rota/loadable_rota_data.pkl"
    r.load()
    r.sort()
    return r


def test_init(test_printable):
    assert test_printable.name == "test_printable"
    assert isinstance(test_printable, rota.Rota)


def test_ordinal(test_printable):
    assert test_printable._ordinal(1) == "1st"
    assert test_printable._ordinal(2) == "2nd"
    assert test_printable._ordinal(3) == "3rd"
    for x in range(4, 21):
        assert test_printable._ordinal(x) == str(x) + "th"

    assert test_printable._ordinal(21) == "21st"
    assert test_printable._ordinal(22) == "22nd"
    assert test_printable._ordinal(23) == "23rd"
    for x in range(24, 31):
        assert test_printable._ordinal(x) == str(x) + "th"


def test_human_readable_date(test_printable):
    today = datetime.date.today()
    ordinal = test_printable._ordinal(today.day)
    day = today.strftime("%A")
    month = today.strftime("%B")
    year = today.strftime("%Y")

    f_t = test_printable._human_readable_date(today)
    assert f_t == f"{ordinal} {month} {year}"
    t_t = test_printable._human_readable_date(today, True)
    assert t_t == f"{day} {ordinal} {month} {year}"
    t_f = test_printable._human_readable_date(today, True, False)
    assert t_f == f"{day} {ordinal} {month}"
    f_f = test_printable._human_readable_date(today, False, False)
    assert f_f == f"{ordinal} {month}"
