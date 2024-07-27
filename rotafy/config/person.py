import datetime
from typing import Iterable
from rotafy.config import chore


class NoPersonName(Exception):
    def __init__(self) -> None:
        super().__init__("Must provide a person name in the TOML configuration file.")


class PersonNotFound(Exception):
    def __init__(self, person_name: str) -> None:
        super().__init__(
            f"Cannot find person named {person_name} among the list of people."
        )


class Person:
    def __init__(
        self,
        name: str,
        skills: Iterable[chore.Chore],
        telephone: str = "",
        unavailable: Iterable[datetime.date] = [],
        training: Iterable[chore.Chore] = [],
    ) -> None:
        self.name = name
        self.telephone = telephone
        self.skills = set(skills)
        self.unavailable = set(unavailable)

        self._raw_training = set(training)
        self.experience = {c: 0 for c in self._raw_training if c not in self.skills}

    def __repr__(self) -> str:
        init_args = (
            self.name,
            self.skills,
            self.telephone,
            self.unavailable,
            self._raw_training,
        )
        reprs = (repr(arg) for arg in init_args)
        s = f"Person({', '.join(reprs)})"
        return s

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        return other and self.name == other.name and self.telephone == other.telephone

    def __hash__(self) -> int:
        return hash((self.name, self.telephone))

    def qualified(self, chore: chore.Chore) -> bool:
        return chore in self.skills

    def is_learning(self, chore: chore.Chore) -> bool:
        return chore in self.experience.keys()

    def add_to_experience(self, chore: chore.Chore) -> None:
        if chore in self.skills:
            return

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

    def reduce_experience(self, chore: chore.Chore) -> None:
        if chore in self.skills:
            qualification_threshold = (
                chore.num_training_sessions + chore.num_shadowing_sessions
            )
            self.experience[chore] = qualification_threshold
            self.skills = set(s for s in self.skills if s != chore)

        if chore not in self.experience.keys():
            self.experience[chore] = 0

        self.experience[chore] = max(0, self.experience[chore] - 1)

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
        return not (date in self.unavailable)

    def can_do(self, chore: chore.Chore, date: datetime.date) -> bool:
        return self.qualified(chore) and self.available(date)

    def can_be_trained(self, chore: chore.Chore, date: datetime.date) -> bool:
        return self.is_learning(chore) and self.available(date)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if len(value.strip()) == 0:
            raise NoPersonName

        self._name = value.strip()


def find_person(person_name: str, people: Iterable[Person]) -> Person:
    for person in people:
        if person.name == person_name:
            return person

    for person in people:
        if person.name.lower() == person_name.lower():
            return person

    raise PersonNotFound(person_name)
