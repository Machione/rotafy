import datetime
from rotafy.config import chore, person

class Assignment:
    def __init__(
            self, 
            date: datetime.date, 
            chore: chore.Chore, 
            person: person.Person, 
            trainee: person.Person | None = None,
            notification_sent: bool = False
        ) -> None:
        self.date = date
        self.chore = chore
        self.person = person
        self.trainee = trainee
        self.notification_sent = notification_sent
    
    def __repr__(self):
        s = (
            f"Assignment({self.date}, {self.chore}, {self.person}, "
            f"{self.trainee})"
        )
        return s
    
    def __str__(self):
        if self.trainee is None:
            return self.person.name
        
        if self.trainee.is_shadowing(self.chore):
            return f"{self.person.name} with {self.trainee.name} shadowing"
        
        if self.trainee.is_being_observed(self.chore):
            return f"{self.trainee.name} supervised by {self.person.name}"
        
        return f"Other - {self.person.name} with {self.trainee.name}"
    
    def __eq__(self, other) -> bool:
        return (
            other and 
            self.date == other.date and 
            self.chore == other.chore and 
            self.person == other.person and 
            self.trainee == other.trainee
        )
    
    def __hash__(self) -> int:
        return hash(
            (
                self.date, 
                self.chore, 
                self.person, 
                self.trainee if self.trainee is not None else None
            )
        )