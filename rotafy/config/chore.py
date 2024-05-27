import recurrent
import datetime
from dateutil import rrule
from typing import Iterable


class Chore:
    def __init__(
            self, 
            name: str, 
            ordinal: int, 
            recurrence: str, 
            notify: int | bool, 
            num_training_sessions: int,
            num_shadowing_sessions: int,
            exceptions: Iterable[datetime.date] = []
        ) -> None:
        self.name = name
        self.ordinal = ordinal
        self._raw_recurrence = recurrence
        self.recurring_rule = self.generate_rrule(recurrence)
        self.notify = notify
        self.num_training_sessions = num_training_sessions
        self.num_shadowing_sessions = num_shadowing_sessions
        self.exceptions = exceptions
    
    def __repr__(self) -> str:
        s = (
            f"Chore({self.name}, {self.ordinal}, {self._raw_recurrence}, "
            f"{self.notify}, {self.num_training_sessions}, "
            f"{self.num_shadowing_sessions}, {self.exceptions})"
        )
        return s
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __eq__(self, other) -> bool:
        return other and self.name == other.name
    
    def __hash__(self) -> int:
        return hash(self.name)
    
    
    def generate_rrule(self, recurrence: str) -> rrule.rrule:
        start_of_today = datetime.datetime.combine(
            datetime.datetime.today(),
            datetime.time.min
        )
        recurring_event = recurrent.event_parser.RecurringEvent(
            now_date=start_of_today
        )
        recurring_event.parse(recurrence.lower())
        recurring_event_rrule = recurring_event.get_RFC_rrule()
        rule = rrule.rrulestr(recurring_event_rrule)
        rule = rule.replace(dtstart=start_of_today)
        return rule
    
    def on(self, date: datetime.date) -> bool:
        timestamp = datetime.datetime.combine(date, datetime.time.min)
        in_rrule = self.recurring_rule.after(timestamp, inc=True) == timestamp
        if date in self.exceptions:
            return not(in_rrule)
            
        return in_rrule
    
    def next(self, start_date: datetime.date) -> datetime.date:
        timestamp = datetime.datetime.combine(start_date, datetime.time.min)
        next_date = self.recurring_rule.after(timestamp)
        while next_date.date() in self.exceptions:
            next_date = self.recurring_rule.after(next_date)
        
        return next_date.date()
        
    
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        if len(value.strip()) == 0:
            raise ValueError(
                "You must provide a non-empty chore name in the TOML "
                "configuration file."
            )
        
        self._name = value.strip()


def find_chore(chore_name: str, chores: Iterable[Chore]) -> Chore:
    for chore in chores:
        if chore.name == chore_name:
            return chore
    
    for chore in chores:
        if chore.name.lower() == chore_name.lower():
            return chore
    
    raise Exception(
        f"Cannot find chore named {chore_name} among the list of chores."
    )
