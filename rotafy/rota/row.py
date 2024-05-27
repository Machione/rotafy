from typing import Iterable
import assignment

class Row:
    def __init__(self, assignments: Iterable[assignment.Assignment]) -> None:
        self.assignments = assignments
        self.date = list(self.assignments)[0].date
    
    def __getitem__(self, chore_name: str) -> assignment.Assignment | None:
        found = [
            assignment
            for assignment in self.assignments
            if assignment.chore.name == chore_name
        ]
        if len(found) == 0:
            found = [
                assignment
                for assignment in self.assignments
                if assignment.chore.name.lower() == chore_name.lower()
            ]
        
        if len(found) == 0:
            return None
        
        if len(found) > 1:
            raise Warning(
                "Ambiguous chore name given resulting in multiple matches."
            )
        
        return found[0]
    
    
    @property
    def assignments(self) -> Iterable[assignment.Assignment]:
        return self._assignments
    
    @assignments.setter
    def assignments(self, assignments: Iterable[assignment.Assignment]) -> None:
        num_assignments = len(assignments)
        
        if num_assignments == 0:
            raise IndexError("Need to provide one or more chore assignments.")
        
        distinct_assignment_dates = set(a.date for a in assignments)
        if len(distinct_assignment_dates) > 1:
            raise IndexError("Chore assignments must be all on the same date.")
        
        distinct_chores = set(a.chore for a in assignments)
        if len(distinct_chores) < num_assignments:
            raise ValueError(
                "Cannot assign more than one chore of the same name on a "
                "date."
            )
        
        distinct_people = set(a.person for a in assignments)
        if len(distinct_people) < num_assignments:
            raise ValueError(
                "Cannot assign more than one chore of the same name to the "
                "same person on a given date."
            )
        
        all_trainees = [
            a.trainee for a in assignments if a.trainee is not None
        ]
        if any(trainee in distinct_people for trainee in all_trainees):
            raise ValueError(
                "Cannot assign someone to be a trainee and also give them a "
                "chore on the same date."
            )
        
        distinct_trainees = set(all_trainees)
        if len(distinct_trainees) < len(all_trainees):
            raise ValueError(
                "Cannot assign the same trainee to more than one chore on a "
                "given date."
            )
    
        self._assignments = assignments
