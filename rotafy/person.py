import datetime
from . import chore

class Person:
    def __init__(
            self, 
            name: str, 
            telephone: str, 
            skills: list[chore.Chore], 
            unavailable: list[datetime.date],
            training: list[chore.Chore]
        ) -> None:
        self.name = name
        self.telephone = telephone
        self.skills = skills
        self.unavailable = unavailable
        self.training = training
    
    def __repr__(self):
        s = (
            f"Person({self.name}, {self.telephone}, {self.skills}, "
            f"{self.unavailable}, {self.training})"
        )
        return s
    
    def __str__(self) -> str:
        return self.__repr__()