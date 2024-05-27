import datetime
import pkg_resources
import os
import pickle
import row

class Rota:
    def __init__(self, name: str) -> None:
        self.name = name
        self.file_path = pkg_resources.resource_filename(
            __name__, 
            f"/rotas/{self.name}.pkl"
        )
        self.rows = []
        self.load()
        self.sort()
    
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
            raise Warning(f"Overwrote assignments on {new_row.date}.")
        
        self.rows.append(new_row)
        self.sort()
    
    def delete_row(self, date: datetime.date) -> None:
        self.rows = [row for row in self.rows if row.date != date]
    
    @property
    def latest_date(self):
        if len(self.rows) == 0:
            return datetime.datetime.today().date()
        
        return max(row.date for row in self.rows)