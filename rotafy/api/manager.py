import datetime
import logging
import itertools
from typing import Iterable
import random
from retry.api import retry_call
from clicksend_client.rest import ApiException
from rotafy.config import config, chore, person
from rotafy.rota import printable, assignment, row
from rotafy.api import notifier


logger = logging.getLogger(__name__)


class DateNotFound(Exception):
    def __init__(self, date: datetime.date) -> None:
        super().__init__(f"No existing rota row on {date}. Try `add_person` instead.")


class PersonNotAssigned(Exception):
    def __init__(self, date: datetime.date, person_name: str) -> None:
        super().__init__(
            f"{person_name} is not assigned to a chore on {date}. Try `add_person` instead."
        )


class ReplacementPersonAlreadyAssigned(Exception):
    def __init__(self, date: datetime.date, person_name: str) -> None:
        super().__init__(
            f"{person_name} is already assigned to a chore on {date}. Try `swap` instead."
        )


class NoValidAssignments(Exception):
    def __init__(self, date: datetime.date) -> None:
        super().__init__(f"Cannot find any valid assignments on {date}.")


class Manager:
    def __init__(self, toml_file_path: str) -> None:
        self.configuration = config.Config(toml_file_path)
        self.name = self.configuration.name

        logger.info(f"Creating rotafy.Manager named {self.name}")
        logger.info(f"Loaded configuration file from {toml_file_path}")

        self.rota = printable.PrintableRota(self.name)
        self.notifier = notifier.Notifier(
            self.configuration.clicksend_username,
            self.configuration.clicksend_api_key,
            self.configuration.message_template,
        )
        self.update_experience()
        self.check_and_heal()

    def print(self) -> None:
        self.rota.print()

    def to_pdf(self, output_file: str) -> None:
        self.rota.pdf(output_file)

    def chores_on(self, date: datetime.date) -> Iterable[chore.Chore]:
        found_chores = set(c for c in self.configuration.chores if c.on(date))
        logger.info(f"Found chores on {date}: {[c.name for c in found_chores]}")
        return found_chores

    def update_experience(self):
        for r in self.rota.rows:
            for a in r.assignments:
                if a.trainee is not None:
                    t = person.find_person(a.trainee.name, self.configuration.people)
                    t.add_to_experience(a.chore)

    def find_assignment(
        self, date: datetime.date, person_name: str
    ) -> None | assignment.Assignment:
        existing_row = self.rota[date]
        if existing_row is None:
            logger.info(f"No existing row on {date}")
            return None

        person_assignment = [
            a
            for a in existing_row.assignments
            if a.person.name == person_name or a.trainee.name == person_name
        ]
        if len(person_assignment) != 1:
            logger.info(f"No existing assignment for {person_name} on {date}")
            return None

        logger.info(f"Found existing assignment for {person_name} on {date}")
        return person_assignment[0]

    def remove_person(self, date: datetime.date, person_name: str) -> None:
        existing_row = self.rota[date]
        if existing_row is None:
            raise DateNotFound(date)

        person_assignment = self.find_assignment(date, person_name)
        if person_assignment is None:
            raise PersonNotAssigned(date, person_name)

        logger.info(
            f"Removing {person_name} from {person_assignment.chore.name} on {date}"
        )

        new_row = existing_row
        if person_assignment.trainee.name == person_name:
            person_assignment.trainee.reduce_experience(person_assignment.chore)
            person_assignment.trainee = None
            new_row[person_assignment.chore] = person_assignment
        else:
            del new_row[person_assignment.chore]

        if len(new_row.assignments) == 0:
            del self.rota[date]
        else:
            self.rota[date] = new_row

        self.rota.save()

    def add_person(
        self, date: datetime.date, chore_name: str, person_name: str
    ) -> None:
        chore_to_do = chore.find_chore(chore_name, self.configuration.chores)
        person_to_assign = person.find_person(person_name, self.configuration.people)
        new_assignment = assignment.Assignment(date, chore_to_do, person_to_assign)

        logger.info(f"Adding {person_name} to {chore_name} on {date}")

        existing_row = self.rota[date]
        if existing_row is None:
            new_row = row.Row([new_assignment])
        else:
            new_row = existing_row
            new_row[chore_to_do] = new_assignment

        self.rota[date] = new_row
        self.rota.save()

    def swap(self, date: datetime.date, person1_name: str, person2_name: str) -> None:
        existing_row = self.rota[date]
        if existing_row is None:
            raise DateNotFound(date)

        person1_assignment = self.find_assignment(date, person1_name)
        if person1_assignment is None:
            raise PersonNotAssigned(date, person1_name)

        person2_assignment = self.find_assignment(date, person2_name)
        if person2_assignment is None:
            raise PersonNotAssigned(date, person2_name)

        logger.info(f"Swapping {person1_name} and {person2_name} on {date}")

        person1_assigned_as_trainee = person1_assignment.trainee.name == person1_name
        person2_assigned_as_trainee = person2_assignment.trainee.name == person2_name

        self.remove_person(date, person1_name)
        self.remove_person(date, person2_name)

        if not (person1_assigned_as_trainee):
            self.add_person(date, person1_assignment.chore, person2_name)

        if not (person2_assigned_as_trainee):
            self.add_person(date, person2_assignment.chore, person1_name)

    def replace(
        self, date: datetime.date, person_name: str, replacement_name: str
    ) -> None:
        replacement_assignment = self.find_assignment(date, replacement_name)
        if replacement_assignment is not None:
            raise ReplacementPersonAlreadyAssigned(date, replacement_name)

        logger.info(f"Replacing {person_name} with {replacement_name} on {date}")

        self.remove_person(date, person_name)
        self.add_person(date, replacement_name)

    def check_and_heal(self):
        # Remove all chores that no longer should be carried out and assigned people
        # that are no longer available.
        upcoming_rota = self.rota.rows_after(datetime.date.today(), True)
        for row in upcoming_rota:
            for a in row.assignments:
                try:
                    updated_chore = chore.find_chore(
                        a.chore.name, self.configuration.chores
                    )
                except chore.ChoreNotFound:
                    logger.info(
                        f"Removing {a.chore.name} from {a.date} - no longer configured"
                    )
                    if len([_ for _ in row.assignments if _.chore != a.chore]) == 0:
                        del self.rota[row.date]
                    else:
                        del self.rota[row.date][a.chore]

                try:
                    updated_person = person.find_person(
                        a.person.name, self.configuration.people
                    )
                except person.PersonNotFound:
                    logger.info(
                        f"Removing {a.person.name} from {a.date} - no longer configured"
                    )
                    if len([_ for _ in row.assignments if _.chore != a.chore]) == 0:
                        del self.rota[row.date]
                    else:
                        del self.rota[row.date][a.chore]

                updated_trainee = None
                if a.trainee is not None:
                    try:
                        updated_trainee = person.find_person(
                            a.trainee.name, self.configuration.people
                        )
                    except person.PersonNotFound:
                        logger.info(
                            f"Removing {a.trainee.name} as trainee from {a.date} - no longer configured"
                        )
                        a.trainee.reduce_experience(a.chore)
                        a.trainee = None
                        self.rota[row.date][a.chore] = a
                        updated_trainee = None

                if (
                    updated_chore.on(a.date) == False
                    or updated_person.available(a.date) == False
                ):
                    if updated_chore.on(a.date) == False:
                        logger.info(f"Removing {a.chore.name} - no longer on {a.date}")
                    elif updated_person.available(a.date) == False:
                        logger.info(
                            f"Removing {a.person.name} - no longer available on {a.date}"
                        )

                    if len([_ for _ in row.assignments if _.chore != a.chore]) == 0:
                        del self.rota[row.date]
                    else:
                        del self.rota[row.date][a.chore]
                else:
                    if (
                        updated_trainee is not None
                        and updated_trainee.available(a.date) == False
                    ):
                        logger.info(
                            f"Removing {a.trainee.name} - no longer available on {a.date}"
                        )
                        a.trainee.reduce_experience(a.chore)
                        a.trainee = None
                        self.rota[row.date][a.chore] = a

        self.fill()

    def all_independently_valid_assignments(
        self, date: datetime.date, chore_to_assign: chore.Chore
    ) -> Iterable[assignment.Assignment]:
        valid_people = [
            p for p in self.configuration.people if p.can_do(chore_to_assign, date)
        ]
        valid_trainees = [None] + [
            t
            for t in self.configuration.people
            if t.can_be_trained(chore_to_assign, date)
        ]
        valid_assignments = []
        for p, t in itertools.product(valid_people, valid_trainees):
            new_assignment = assignment.Assignment(date, chore_to_assign, p, t)
            valid_assignments.append(new_assignment)

        logging.info(
            f"Found valid assignments for {chore_to_assign.name} on {date}: {[str(a) for a in valid_assignments]}"
        )
        return valid_assignments

    def row_weight(self, row_to_check: row.Row) -> float:
        date = row_to_check.date
        previous_rows = self.rota.rows_prior(date)
        previous_rows.reverse()
        max_look_back = 10
        previous_rows = [r for i, r in enumerate(previous_rows) if i < max_look_back]

        # For each person, working from most recent row to least recent row, we
        # will subtract the following from the weight.
        # latest:        1/2 if chore matches, 1/4 if person is assigned any chore
        # second latest: 1/4 if chore matches, 1/8 if person is assigned any chore
        # etc.
        # Therefore the most this weight could ever be reduced by is
        #   1/2 + 1/4 + 1/8 + ... + 1/(2 ^ max_look_back)
        # = ((2 ^ max_look_back) - 1) / 2 ^ max_look_back
        # = very close to but never > 1
        weight = len(self.configuration.chores)

        for assignment_to_check in row_to_check.assignments:
            n = 0
            for comparison_row in previous_rows:
                same_chore_assignment = [
                    a
                    for a in comparison_row.assignments
                    if a.chore == assignment_to_check.chore
                ]
                # Only increment n if the chore is actually being done on this
                # date.
                if len(same_chore_assignment) == 0:
                    continue

                n += 1
                if assignment_to_check.person == same_chore_assignment[0].person:
                    weight -= 1 / (2**n)
                else:
                    not_same_chore = [
                        a
                        for a in comparison_row.assignments
                        if a.chore != assignment_to_check.chore
                    ]
                    for a in not_same_chore:
                        # Otherwise, subtract a smaller value if the person has been
                        # assigned any chore on that date.
                        if assignment_to_check.person == a.person:
                            weight -= 1 / ((2**n) * 2)
                            break

        row_s = [f"{a.chore.name}: {str(a)}" for a in row_to_check.assignments]
        logger.info(f"Weight of {weight} calculated for {', '.join(row_s)}")
        return weight

    def assign_chores_on(self, date: datetime.date) -> None:
        chores_on_date = self.chores_on(date)
        if len(chores_on_date) == 0:
            logger.info(f"No chores on {date} to assign")
            return

        existing_row = self.rota[date]
        existing_assignments = []
        if existing_row is not None:
            existing_assignments = [existing_row[c] for c in chores_on_date]

        existing_assignments = [a for a in existing_assignments if a is not None]
        existing_chores = [a.chore for a in existing_assignments]
        logger.info(f"Existing chores already assigned on {date}: {existing_chores}")

        chores_to_assign = [c for c in chores_on_date if c not in existing_chores]
        logger.info(f"New assignments required on {date} for {chores_to_assign}")
        if len(chores_to_assign) == 0:
            return

        # TODO: Work from the chore with the least possible assignments to the most.
        for c in chores_to_assign:
            existing_row = self.rota[date]
            existing_assignments = []
            if existing_row is not None:
                existing_assignments = [existing_row[c] for c in chores_on_date]
            existing_assignments = [a for a in existing_assignments if a is not None]
            unchanged_assignments = [a for a in existing_assignments if a.chore != c]

            choices = self.all_independently_valid_assignments(date, c)
            valid_rows = []
            for choice in choices:
                try:
                    new_row = row.Row(unchanged_assignments + [choice])
                except Exception:
                    pass
                else:
                    valid_rows.append(new_row)

            if len(valid_rows) == 0:
                logger.info(f"No valid combination of assignments found for {date}")
                if len(existing_assignments) > 0:
                    logger.info(f"Re-evaluating all chores due on {date}")
                    del self.rota[date]
                    self.assign_chores_on(date)
                else:
                    raise NoValidAssignments(date)

            weights = [self.row_weight(r) for r in valid_rows]
            max_weight = max(weights)
            index_with_max = [i for i, w in enumerate(weights) if w == max_weight]
            best_rows = [valid_rows[i] for i in index_with_max]
            best_row = random.choice(best_rows)

            for a in best_row.assignments:
                if a.trainee is not None:
                    a.trainee.add_to_experience(c)

            self.rota.add_row(best_row)

    def fill(self) -> None:
        today = datetime.date.today()
        all_lookahead_days = [
            today + datetime.timedelta(days=days_to_add)
            for days_to_add in range(self.configuration.lookahead_days + 1)
        ]
        for r in self.rota.rows_after(today, True):
            if r.date not in all_lookahead_days:
                all_lookahead_days.append(row.date)

        chores_on_dates = [
            date for date in all_lookahead_days if len(self.chores_on(date)) > 0
        ]
        logger.info(f"Attempting to fill assignments for {chores_on_dates}")
        chores_on_dates.sort()
        for date in chores_on_dates:
            self.assign_chores_on(date)

        self.rota.save()

    def notify(self) -> None:
        today = datetime.date.today()

        for c in self.configuration.chores:
            if c.notify == False:
                continue

            notification_cut_off = today + datetime.timedelta(days=c.notify)
            for r in self.rota.rows_prior(notification_cut_off, True):
                a = r[c]
                if a is not None and a.notification_sent == False:
                    self.notifier.message_from_assignment(a)
                    try:
                        retry_call(
                            _notifier_send,
                            fargs=[self.notifier],
                            exceptions=ApiException,
                            tries=3,
                            delay=5,
                            backoff=5,
                        )
                    except Exception as e:
                        raise e
                    else:
                        a.mark_notified()
                        self.rota.save()


def _notifier_send(notifier: notifier.Notifier) -> None:
    notifier.send()
