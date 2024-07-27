import datetime
from rotafy.config import chore, person


class NotQualified(Exception):
    def __init__(self, person: person.Person, chore: chore.Chore) -> None:
        super().__init__(f"{person.name} is not qualified to do {chore.name}.")


class PersonUnavailable(Exception):
    def __init__(self, person: person.Person, date: datetime.date) -> None:
        super().__init__(f"{person.name} is not available on {date}.")


class ChoreNotScheduled(Exception):
    def __init__(self, chore: chore.Chore, date: datetime.date) -> None:
        super().__init__(f"{chore} is not scheduled to happen on {date}.")


class Assignment:

    def __init__(
        self,
        date: datetime.date,
        chore: chore.Chore,
        person: person.Person,
        trainee: person.Person | None = None,
        notification_sent: bool = False,
    ) -> None:

        if person.qualified(chore) == False:
            raise NotQualified(person, chore)

        if person.available(date) == False:
            raise PersonUnavailable(person, date)

        if trainee is not None and trainee.available(date) == False:
            raise PersonUnavailable(person, date)

        if chore.on(date) == False:
            raise ChoreNotScheduled(chore, date)

        if person == trainee:
            trainee = None

        self.date = date
        self.chore = chore
        self.person = person
        self.trainee = trainee
        self.notification_sent = notification_sent

    def __repr__(self):
        init_args = (
            self.date,
            self.chore,
            self.person,
            self.trainee,
            self.notification_sent,
        )
        reprs = (repr(arg) for arg in init_args)
        s = f"Assignment({', '.join(reprs)})"
        return s

    def __str__(self):
        if self.trainee is None:
            return self.person.name

        if self.trainee.is_shadowing(self.chore):
            return f"{self.person.name} with {self.trainee.name} shadowing"

        if self.trainee.is_being_observed(self.chore):
            return f"{self.trainee.name} supervised by {self.person.name}"

        return f"{self.person.name} with {self.trainee.name}"

    def __eq__(self, other) -> bool:
        return (
            other
            and self.date == other.date
            and self.chore == other.chore
            and self.person == other.person
            and self.trainee == other.trainee
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.date,
                self.chore,
                self.person,
                self.trainee if self.trainee is not None else None,
            )
        )

    def mark_notified(self) -> None:
        self.notification_sent = True
