import datetime
import pkg_resources
import os
import pickle
import copy
from typing import Iterable
from rotafy.rota import row


class MismatchedDates(Exception):
    def __init__(self, set_date: datetime.date, new_date: datetime.date) -> None:
        super().__init__(
            f"Date of new row ({new_date}) must match the and date being set ({set_date})."
        )


class Rota:
    def __init__(self, name: str) -> None:
        self.name = name
        self.file_path = pkg_resources.resource_filename(
            __name__, f"/rotas/{self.name}.pkl"
        )
        self.rows = []
        self.load()
        self.sort()

    def __getitem__(self, date: datetime.date) -> row.Row | None:
        matches = [r for r in self.rows if r.date == date]
        if len(matches) != 1:
            return None

        return matches[0]

    def __setitem__(self, date: datetime.date, new_row: row.Row) -> None:
        if date != new_row.date:
            raise MismatchedDates(date, new_row.date)

        return self.add_row(new_row)

    def __delitem__(self, date: datetime.date) -> None:
        return self.delete_row(date)

    def load(self) -> None:
        if os.path.exists(self.file_path):
            with open(self.file_path, "rb") as f:
                self.rows = pickle.load(f)

    def save(self) -> None:
        if os.path.exists(self.file_path) == False:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        with open(self.file_path, "wb") as f:
            pickle.dump(self.rows, f)

    def sort(self) -> None:
        self.rows.sort(key=lambda r: r.date)

    def add_row(self, new_row: row.Row) -> None:
        all_row_dates = set(r.date for r in self.rows)
        if new_row.date in all_row_dates:
            self.delete_row(new_row.date)
            print(f"Overwrote assignments on {new_row.date}.")

        self.rows.append(copy.deepcopy(new_row))
        self.sort()

    def delete_row(self, date: datetime.date) -> None:
        self.rows = [row for row in self.rows if row.date != date]

    def rows_prior(self, date: datetime.date, inc: bool = False) -> Iterable[row.Row]:
        self.sort()

        if inc:
            prior = [row for row in self.rows if row.date <= date]
        else:
            prior = [row for row in self.rows if row.date < date]

        return prior

    @property
    def latest_date(self):
        if len(self.rows) == 0:
            return datetime.datetime.today().date()

        return max(row.date for row in self.rows)
