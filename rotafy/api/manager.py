import datetime
import itertools
from typing import Iterable
import random
import math
from retry.api import retry_call
from clicksend_client.rest import ApiException
from rotafy.config import config, chore, person
from rotafy.rota import printable, assignment, row
from rotafy.api import notifier


class Manager:
    def __init__(self, name: str, toml_file_path: str) -> None:
        self.name = name
        self.configuration = config.Config(toml_file_path)
        self.rota = printable.PrintableRota(self.name)
        self.notifier = notifier.Notifier(
            self.configuration.clicksend_username,
            self.configuration.clicksend_api_key
        )
    
    
    def next_chore_date(self) -> datetime.date:
        next_dates_per_chore = [
            chore.next(self.rota.latest_date)
            for chore in self.configuration.chores
        ]
        return min(next_dates_per_chore)
    
    def chores_on(self, date: datetime.date) -> Iterable[chore.Chore]:
        return set(c for c in self.configuration.chores if c.on(date))
    
    
    def add(
            self, 
            date: datetime.date, 
            chore_name: str, 
            person_name: str
        ) -> None:
        chore_to_do = chore.find_chore(chore_name, self.configuration.chores)
        person_to_assign = person.find_person(
            person_name, 
            self.configuration.people
        )
        new_assignment = assignment.Assignment(
            date, 
            chore_to_do, 
            person_to_assign
        )
        
        existing_row = self.rota[date]
        if existing_row is None:
            new_row = row.Row([new_assignment])
        else:
            new_row = existing_row
            new_row[chore] = new_assignment
        
        self.rota[date] = new_row
        self.rota.save()
    
    def replace(
            self, 
            date: datetime.date, 
            person_name: str, 
            replacement_name: str
        ) -> None:
        existing_row = self.rota[date]
        if existing_row is None:
            raise IndexError(f"No existing rota row on {date} to replace.")
        
        existing_assignment = [
            a for a in existing_row.assignments if a.person.name == person_name
        ]
        if len(existing_assignment) != 1:
            raise IndexError(
                f"{person_name} is not assigned to a chore on {date}. Use "
                ".add() to add them instead."
            )
        
        chore_name = existing_assignment[0].chore.name
        self.add(date, chore_name, replacement_name)
        
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
        
    
    def get_row_weight(self, date: datetime.date, row: row.Row) -> float:
        previous_rota = self.rota.rows_prior(date)
        previous_rota.reverse()
        # For each person, working from most recent row to least recent row, we
        # will subtract the following from the weight.
        # 1st - 1/2 if assignments match, 1/4 if person is assigned any chore
        # 2nd - 1/4 if assignments match, 1/8 if person is assigned any chore
        # etc.
        # Therefore the most this weight could ever be reduced by is 1/2 + 1/4
        # + 1/8 + ... = sum to infinity of 1/(n^2) - 1 = ((pi^2) / 6) - 1.
        weight = (((math.pi ** 2) / 6) - 1) * len(self.configuration.chores)
        
        for assignment in row.assignments:
            n = 0
            for comparison_row in previous_rota:
                same_chore = [
                    a for a in comparison_row.assignments
                    if a.chore == assignment.chore
                ]
                # Only increment n if the chore is actually being done on this
                # date.
                if len(same_chore) > 0:
                    n += 1
                    if assignment.person == same_chore[0].person:
                        # Subtract the bigger value when the chore has been
                        # assigned to this person on that date.
                        weight -= 1 / (2 ** n)
                    else:
                        not_same_chore = [
                            a for a in comparison_row.assignments
                            if a.chore != assignment.chore
                        ]
                        for a in not_same_chore:
                            # Otherwise, subtract a smaller value if the person
                            # has been assigned any chore on that date.
                            if assignment.person == a.person:
                                weight -= 1 / ((2 ** n) * 2)
        
        return weight
    
    def assign(self, date: datetime.date) -> None:
        choices = self.get_all_valid_assignments(date)
        weights = [
            self.get_row_weight(date, row) for row in choices
        ]
        row = random.choices(choices, weights=weights, k=1)[0]
        self.rota.add_row(row)
        
        for assignment in row.assignments:
            if assignment.trainee is not None:
                assignment.trainee.add_to_experience(assignment.chore)
    
    def fill(self) -> None:
        current_date = datetime.datetime.today().date()
        while (
            (self.rota.latest_date - current_date).days <= 
            self.configuration.lookahead_days
        ):
            self.assign(self.next_chore_date())
        
        self.rota.save()
    
    def notify(self) -> None:
        today = datetime.datetime.today().date()
        
        for chore in self.configuration.chores:
            if isinstance(chore.notify, int):
                delta = datetime.timedelta(days=chore.notify)
                for row in self.rota.rows:
                    if row.date - delta == today:
                        for assignment in row.assignments:
                            if assignment.notification_sent == False:
                                self.notifier.add_to_queue(
                                    self.configuration.message_template,
                                    assignment.person,
                                    row.date,
                                    assignment.chore,
                                    str(assignment)
                                )
                                if assignment.trainee is not None:
                                    self.notifier.add_to_queue(
                                        self.configuration.message_template,
                                        assignment.trainee,
                                        row.date,
                                        assignment.chore,
                                        str(assignment)
                                    )
                                
                                try:
                                    retry_call(
                                        notifier_send,
                                        fargs=[self.notifier],
                                        exceptions=ApiException,
                                        tries=3,
                                        delay=5,
                                        backoff=5
                                    )
                                    assignment.mark_notified()
                                except Exception as e:
                                    raise e
        
        self.rota.save()


def notifier_send(notifier: notifier.Notifier) -> None:
    notifier.send()