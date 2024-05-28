import datetime
import itertools
from typing import Iterable
import random
from rotafy.config import config, chore
from rotafy.rota import printable, assignment, row


class Manager:
    def __init__(self, name: str, toml_file_path: str) -> None:
        self.name = name
        self.configuration = config.Config(toml_file_path)
        self.rota = printable.PrintableRota(self.name)
        self.fill_up_lookahead_period()
        self.rota.save()
    
    
    def next_chore_date(self) -> datetime.date:
        next_dates_per_chore = [
            chore.next(self.rota.latest_date)
            for chore in self.configuration.chores
        ]
        return min(next_dates_per_chore)
    
    def chores_on(self, date: datetime.date) -> Iterable[chore.Chore]:
        return set(c for c in self.configuration.chores if c.on(date))
    
    
    def try_to_generate_row(
            self, 
            assignments: Iterable[assignment.Assignment]
        ) -> row.Row | None:
        try:
            return row.Row(assignments)
        except Exception:
            return None
        
    def get_all_valid_assignments(
            self, 
            date: datetime.date
        ) -> Iterable[assignment.Assignment]:
        # TODO: This could probably be improved in efficiency.
        chores_to_assign = self.chores_on(date)
        all_possible_assignments_with_trainees = [
            assignment.Assignment(date, chore, person, trainee)
            for person in self.configuration.people
            for trainee in self.configuration.people
            for chore in chores_to_assign
            if (
                person.can_do(chore, date) and 
                trainee.can_be_trained(chore, date)
            )
        ]
        all_possible_assignments_without_trainees = [
            assignment.Assignment(date, chore, person)
            for person in self.configuration.people
            for chore in chores_to_assign
            if person.can_do(chore, date)
        ]
        all_possible_assignments = (
            all_possible_assignments_with_trainees + 
            all_possible_assignments_without_trainees
        )
        
        all_assignment_combinations = itertools.combinations(
            all_possible_assignments,
            len(chores_to_assign)
        )
        checked_assignment_combinations = [
            self.try_to_generate_row(assignments)
            for assignments in all_assignment_combinations
        ]
        all_valid_rows = list(set(
            row for row in checked_assignment_combinations if row is not None
        ))
        return all_valid_rows
        
    
    def assign(self, date: datetime.date) -> None:
        choices = self.get_all_valid_assignments(date)
        # TODO: Don't just randomly assign, but use weights
        row = random.choice(choices)
        self.rota.add_row(row)
        
        for assignment in row.assignments:
            if assignment.trainee is not None:
                assignment.trainee.add_to_experience(assignment.chore)
    
    def fill_up_lookahead_period(self) -> None:
        current_date = datetime.datetime.today().date()
        while (
            (self.rota.latest_date - current_date).days <= 
            self.configuration.lookahead_days
        ):
            self.assign(self.next_chore_date())