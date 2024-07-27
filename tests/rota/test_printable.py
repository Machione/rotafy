import pytest
import datetime
import os
import matplotlib
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


@pytest.fixture
def future_printable():
    r = printable.PrintableRota("loadable_printable")
    r.file_path = "tests/rota/loadable_rota_data.pkl"
    r.load()

    year_later = datetime.timedelta(days=365)
    for row in r.rows:
        row.date += year_later
        for a in row.assignments:
            a.date += year_later

    r.sort()
    return r


def test_init(test_printable):
    assert test_printable.name == "test_printable"
    assert isinstance(test_printable, rota.Rota)


def test_str(test_printable, loadable_printable, future_printable):
    assert str(test_printable).startswith("Empty DataFrame")
    assert str(loadable_printable).startswith("Empty DataFrame")
    assert len(str(future_printable).splitlines()) == len(future_printable.rows) + 1


def test_draw_table_figure(test_printable, loadable_printable, future_printable):
    assert test_printable._draw_table_figure() is None
    assert loadable_printable._draw_table_figure() is None
    assert isinstance(future_printable._draw_table_figure(), matplotlib.figure.Figure)


def test_pdf(tmp_path, test_printable, loadable_printable, future_printable):
    fp = str(tmp_path) + ".pdf"

    test_printable.pdf(fp)
    assert os.path.exists(fp) == False

    loadable_printable.pdf(fp)
    assert os.path.exists(fp) == False

    future_printable.pdf(fp)
    assert os.path.exists(fp)

    os.remove(fp)


def test_print(capsys, test_printable, loadable_printable, future_printable):
    test_printable.print()
    captured_lines = capsys.readouterr().out.splitlines()
    assert captured_lines == str(test_printable).splitlines()

    loadable_printable.print()
    captured_lines = capsys.readouterr().out.splitlines()
    assert captured_lines == str(loadable_printable).splitlines()

    future_printable.print()
    captured_lines = capsys.readouterr().out.splitlines()
    assert captured_lines == str(future_printable).splitlines()


def test_dataframe(test_printable, loadable_printable, future_printable):
    assert test_printable.dataframe.shape[0] == 0
    assert loadable_printable.dataframe.shape[0] == 0

    assert future_printable.dataframe.shape[0] == len(future_printable.rows)
    all_chores = set(a.chore.name for r in future_printable.rows for a in r.assignments)
    assert set(future_printable.dataframe.columns) == all_chores


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
