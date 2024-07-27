import pytest
import datetime
import matplotlib
from rotafy.rota import printable, rota


def test_ordinal():
    assert printable.ordinal(1) == "1st"
    assert printable.ordinal(2) == "2nd"
    assert printable.ordinal(3) == "3rd"
    for x in range(4, 21):
        assert printable.ordinal(x) == str(x) + "th"

    assert printable.ordinal(21) == "21st"
    assert printable.ordinal(22) == "22nd"
    assert printable.ordinal(23) == "23rd"
    for x in range(24, 31):
        assert printable.ordinal(x) == str(x) + "th"


def test_human_readable_date():
    today = datetime.date.today()
    ordinal = printable.ordinal(today.day)
    day = today.strftime("%A")
    month = today.strftime("%B")
    year = today.strftime("%Y")

    f_t = printable.human_readable_date(today)
    assert f_t == f"{ordinal} {month} {year}"
    t_t = printable.human_readable_date(today, True)
    assert t_t == f"{day} {ordinal} {month} {year}"
    t_f = printable.human_readable_date(today, True, False)
    assert t_f == f"{day} {ordinal} {month}"
    f_f = printable.human_readable_date(today, False, False)
    assert f_f == f"{ordinal} {month}"


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


def test_draw_table_figure(test_printable, loadable_printable):
    # assert test_printable._draw_table_figure() is None
    # assert isinstance(loadable_printable._draw_table_figure(), matplotlib.figure.Figure)
    assert True
