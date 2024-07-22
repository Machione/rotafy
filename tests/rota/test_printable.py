import pytest
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
