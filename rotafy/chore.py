import recurrent
import datetime
from dateutil import rrule

class Chore:
    def __init__(
            self, 
            name: str, 
            recurrence: str, 
            notify: bool | str, 
            exceptions: list[datetime.date]
        ) -> None:
        self.name = name
        self._raw_recurrence = recurrence
        self.recurring_rule = self.generate_rrule(recurrence)
        self._raw_notify = notify
        self.notify = notify
        self.exceptions = exceptions
    
    def __repr__(self) -> str:
        s = (
            f"Chore({self.name}, {self._raw_recurrence}, {self._raw_notify}, "
            f"{self.exceptions})"
        )
        return s
    
    def __str__(self) -> str:
        return self.__repr__()
        
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
    
    @property
    def notify(self) -> bool | rrule.rrule:
        return self._notify
    
    @notify.setter
    def notify(self, value: bool | str) -> None:
        if isinstance(value, str):
            self._notify = self.generate_rrule(value)
        elif value == True: 
            self._notify = self.recurring_rule
        else:
            self._notify = self.generate_rrule("never")


def find_chore(chore_name: str, chores: list[Chore]) -> Chore:
    for chore in chores:
        if chore.name == chore_name:
            return chore
    
    for chore in chores:
        if chore.name.lower() == chore_name.lower():
            return chore
    
    raise Exception(
        f"Cannot find chore named {chore_name} among the list of chores."
    )
