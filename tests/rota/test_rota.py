import pytest
import datetime
from rotafy.rota import rota, row, assignment
from rotafy.config import chore, person


@pytest.fixture
def test_rota():
    return rota.Rota("test_rota")


@pytest.fixture
def loadable_rota(tmp_path):
    r = rota.Rota("loadable_rota")
    r.file_path = "tests/rota/loadable_rota_data.pkl"
    r.load()
    r.sort()
    return r


@pytest.fixture
def test_row():
    c = chore.Chore("Dishes", 1, "Daily", False, 1, 1)
    p = person.Person("Ryan", [c])
    a = assignment.Assignment(datetime.date.today(), c, p)
    return row.Row([a])


def test_init(test_rota):
    assert test_rota.name == "test_rota"
    assert "test_rota.pkl" in test_rota.file_path
    assert len(test_rota.rows) == 0


def test_get_item(test_rota, loadable_rota):
    today = datetime.date.today()
    assert test_rota[today] is None

    loadable_rota_date = loadable_rota.rows[0].date
    assert isinstance(loadable_rota[loadable_rota_date], row.Row)
    assert loadable_rota[today] is None


def test_set_item(test_rota, loadable_rota, test_row):
    today = datetime.date.today()
    test_rota[today] = test_row
    for a in test_row.assignments:
        assert a in test_rota[today].assignments

    with pytest.raises(rota.MismatchedDates):
        test_rota[today + datetime.timedelta(days=1)] = test_row

    loadable_rota_date = loadable_rota.rows[0].date
    loadable_rota[today] = test_row
    for a in test_row.assignments:
        assert a in loadable_rota[today].assignments

    with pytest.raises(rota.MismatchedDates):
        loadable_rota[loadable_rota_date] = test_row

    test_row.date = loadable_rota_date
    loadable_rota[loadable_rota_date] = test_row
    for a in test_row.assignments:
        assert a in loadable_rota[loadable_rota_date].assignments


def test_del_item(test_rota, loadable_rota):
    today = datetime.date.today()
    del test_rota[today]
    assert len(test_rota.rows) == 0

    loadable_rota_size = len(loadable_rota.rows)
    del loadable_rota[today]
    assert len(loadable_rota.rows) == loadable_rota_size

    loadable_rota_date = loadable_rota.rows[0].date
    del loadable_rota[loadable_rota_date]
    assert len(loadable_rota.rows) == loadable_rota_size - 1
    assert loadable_rota[loadable_rota_date] is None
