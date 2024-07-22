import pytest
import datetime
import pickle
import os
import random
from rotafy.rota import rota, row, assignment
from rotafy.config import chore, person


@pytest.fixture
def test_rota():
    return rota.Rota("test_rota")


@pytest.fixture
def loadable_rota():
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

    loadable_rota[today] = test_row
    for a in test_row.assignments:
        assert a in loadable_rota[today].assignments

    loadable_rota_date = loadable_rota.rows[0].date
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


def test_load(test_rota, loadable_rota):
    test_rota.load()
    assert len(test_rota.rows) == 0

    with open(loadable_rota.file_path, "rb") as f:
        loadable_rota_data = pickle.load(f)

    loadable_rota.load()
    assert len(loadable_rota.rows) == len(loadable_rota_data)
    for x in loadable_rota.rows:
        assert isinstance(x, row.Row)


def test_save(test_rota, loadable_rota):
    current_modified_time = os.path.getmtime(loadable_rota.file_path)
    current_number_rows = len(loadable_rota.rows)
    loadable_rota.save()
    assert os.path.getmtime(loadable_rota.file_path) > current_modified_time
    loadable_rota.load()
    assert len(loadable_rota.rows) == current_number_rows

    test_rota.save()
    assert os.path.isfile(test_rota.file_path)
    test_rota.load()
    assert len(test_rota.rows) == 0
    os.remove(test_rota.file_path)


def test_sort(loadable_rota):
    random.shuffle(loadable_rota.rows)
    loadable_rota.sort()
    dates = [r.date for r in loadable_rota.rows]
    assert dates == sorted(dates)


def test_add_row(test_rota, loadable_rota, test_row):
    today = datetime.date.today()
    test_rota.add_row(test_row)
    for a in test_row.assignments:
        assert a in test_rota[today].assignments

    loadable_rota.add_row(test_row)
    for a in test_row.assignments:
        assert a in loadable_rota[today].assignments

    loadable_rota_date = loadable_rota.rows[0].date
    test_row.date = loadable_rota_date
    loadable_rota.add_row(test_row)
    for a in test_row.assignments:
        assert a in loadable_rota[loadable_rota_date].assignments


def test_del_item(test_rota, loadable_rota):
    today = datetime.date.today()
    test_rota.delete_row(today)
    assert len(test_rota.rows) == 0

    loadable_rota_size = len(loadable_rota.rows)
    loadable_rota.delete_row(today)
    assert len(loadable_rota.rows) == loadable_rota_size

    loadable_rota_date = loadable_rota.rows[0].date
    loadable_rota.delete_row(loadable_rota_date)
    assert len(loadable_rota.rows) == loadable_rota_size - 1
    assert loadable_rota[loadable_rota_date] is None


def test_rows_prior(test_rota, loadable_rota):
    today = datetime.date.today()
    assert len(test_rota.rows_prior(today)) == 0

    first_date = min(x.date for x in loadable_rota.rows)
    assert len(loadable_rota.rows_prior(first_date)) == 0
    assert len(loadable_rota.rows_prior(first_date, True)) == 1
    assert loadable_rota.rows_prior(first_date, True)[0].date == first_date

    last_date = max(x.date for x in loadable_rota.rows)
    assert len(loadable_rota.rows_prior(last_date)) == len(loadable_rota.rows) - 1
    assert len(loadable_rota.rows_prior(last_date, True)) == len(loadable_rota.rows)

    assert len(loadable_rota.rows_prior(today)) == len(loadable_rota.rows)
    assert len(loadable_rota.rows_prior(today, True)) == len(loadable_rota.rows)

    mid_date_index = round(len(loadable_rota.rows) / 2)
    mid_date = loadable_rota.rows[mid_date_index].date
    rows_prior_noninc = loadable_rota.rows_prior(mid_date)
    assert len(rows_prior_noninc) > 0
    assert len(rows_prior_noninc) < len(loadable_rota.rows)
    for r in rows_prior_noninc:
        assert r.date < mid_date

    rows_prior_inc = loadable_rota.rows_prior(mid_date, True)
    assert mid_date in [r.date for r in rows_prior_inc]
    assert len(rows_prior_inc) == len(rows_prior_noninc) + 1
    for r in rows_prior_inc:
        assert r.date <= mid_date


def test_latest_date(test_rota, loadable_rota):
    assert test_rota.latest_date == datetime.date.today()
    assert loadable_rota.latest_date == max(r.date for r in loadable_rota.rows)
