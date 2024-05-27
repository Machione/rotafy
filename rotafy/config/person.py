import datetime
from typing import Iterable
from rotafy.config import chore


class Person:
    def __init__(
            self, 
            name: str, 
            skills: set[chore.Chore], 
            telephone: str = "",
            unavailable: Iterable[datetime.date] = [],
            training: Iterable[chore.Chore] = []
        ) -> None:
        self.name = name
        self.telephone = telephone
        self.skills = skills
        self.unavailable = unavailable
        
        self._raw_training = training
        self.experience = {
            c: 0 for c in self._raw_training if c not in self.skills
        }
    
    def __repr__(self):
        s = (
            f"Person({self.name}, {self.telephone}, {self.skills}, "
            f"{self.unavailable}, {self._raw_training})"
        )
        return s
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __eq__(self, other) -> bool:
        return other and self.name == other.name
    
    def __hash__(self) -> int:
        return hash(self.name)
    
    
    def qualified(self, chore: chore.Chore) -> bool:
        return chore in self.skills
    
    def is_learning(self, chore: chore.Chore) -> bool:
        return chore in self.experience.keys()
    
    def add_to_experience(self, chore: chore.Chore) -> None:
        if chore in self.experience.keys():
            self.experience[chore] += 1
        else:
            self.experience[chore] = 1
        
        qualification_threshold = (
            chore.num_training_sessions + chore.num_shadowing_sessions
        )
        if self.experience[chore] >= qualification_threshold:
            del self.experience[chore]
            self.skills.add(chore)
    
    def is_shadowing(self, chore: chore.Chore) -> bool:
        if chore not in self.experience.keys():
            return False
        
        if self.experience[chore] < chore.num_training_sessions:
            return True
        
        return False
        
    def is_being_observed(self, chore: chore.Chore) -> bool:
        if chore not in self.experience.keys():
            return False
        
        if self.experience[chore] >= chore.num_training_sessions:
            return True
        
        return False
    
    def available(self, date: datetime.date) -> bool:
        return not(date in self.unavailable)
    
    def can_do(self, chore: chore.Chore, date: datetime.date) -> bool:
        return self.qualified(chore) and self.available(date)
    
    def can_be_trained(self, chore: chore.Chore, date: datetime.date) -> bool:
        return self.is_learning(chore) and self.available(date)