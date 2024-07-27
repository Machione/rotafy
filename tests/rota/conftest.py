import pytest
import os
import datetime
from rotafy.api import manager
from rotafy.rota import rota


@pytest.fixture(scope="package", autouse=True)
def loadable_data_setup():
    m = manager.Manager("tests/rota/loadable_config.toml")
    r = rota.Rota(m.rota.name)
    os.remove(m.rota.file_path)
    r.file_path = "tests/rota/loadable_rota_data.pkl"

    year_before = datetime.timedelta(days=365)
    for row in r.rows:
        row.date -= year_before
        for a in row.assignments:
            a.date -= year_before

    r.sort()
    r.save()
