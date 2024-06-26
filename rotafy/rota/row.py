import datetime
from collections import Counter
from typing import Iterable
from rotafy.config import chore, person
from rotafy.rota import assignment


class NoAssignments(Exception):
    def __init__(self) -> None:
        super().__init__("Need to provide one or more chore assignments.")


class MultipleDates(Exception):
    def __init__(self, dates: Iterable[datetime.date]) -> None:
        super().__init__(
            f"Chore assignments must be all on the same date. Given dates: {dates}."
        )


class ChoreAssignedMultipleTimes(Exception):
    def __init__(self, chore: chore.Chore) -> None:
        super().__init__(f"Cannot assign {chore.name} more than once on the same date.")


class PersonAssignedMultipleTimes(Exception):
    def __init__(self, person: person.Person) -> None:
        super().__init__(
            f"Cannot assign {person.name} more than once on the same date."
        )


class Row:
    def __init__(self, assignments: Iterable[assignment.Assignment]) -> None:
        self.assignments = assignments
        self.date = list(self.assignments)[0].date

    def __getitem__(self, chore: chore.Chore) -> assignment.Assignment | None:
        matches = [a for a in self.assignments if a.chore == chore]
        if len(matches) != 1:
            return None

        return matches[0]

    def __setitem__(
        self, chore: chore.Chore, new_assignment: assignment.Assignment
    ) -> None:
        kept_assignments = [a for a in self.assignments if a.chore != chore]
        override = kept_assignments + [new_assignment]
        self.assignments = override

    def __delitem__(self, chore: chore.Chore) -> None:
        kept_assignments = [a for a in self.assignments if a.chore != chore]
        self.assignments = kept_assignments

    @property
    def assignments(self) -> Iterable[assignment.Assignment]:
        return self._assignments

    @assignments.setter
    def assignments(self, assignments: Iterable[assignment.Assignment]) -> None:
        num_assignments = len(assignments)

        if num_assignments == 0:
            raise NoAssignments

        distinct_dates = set(a.date for a in assignments)
        if len(distinct_dates) > 1:
            raise MultipleDates(distinct_dates)

        chore_counts = Counter(a.chore for a in assignments)
        if any(v > 1 for v in chore_counts.values()):
            raise ChoreAssignedMultipleTimes(chore_counts.most_common(1)[0][0])

        people_counts = Counter(a.person for a in assignments)
        people_counts.update(a.trainee for a in assignments if a.trainee is not None)
        if any(v > 1 for v in people_counts.values()):
            raise PersonAssignedMultipleTimes(people_counts.most_common(1)[0][0])

        self._assignments = assignments
        self._assignments.sort(key=lambda a: a.chore.ordinal)
