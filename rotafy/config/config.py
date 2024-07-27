import toml
from typing import Iterable
from rotafy.config import chore, person


class Config:
    def __init__(self, toml_file_path: str) -> None:
        self.path = toml_file_path
        self.raw = toml.load(self.path)

        self.name = self.raw["name"]

        self.lookahead_days = self.raw.get("lookahead_days", 14)
        self.clicksend_username = self.raw.get("clicksend_username", "")
        self.clicksend_api_key = self.raw.get("clicksend_api_key", "")
        self.message_template = self.raw.get(
            "message",
            "Hi {{recipient}}! On {{date}}, {{chore}} is due to be handled by "
            "{{assignment}}. Thanks!",
        )

        self.chores = set()
        for ordinal, raw_chore in enumerate(self.raw.get("chore")):
            this_chore_notify = raw_chore.get("notify", False)
            if isinstance(this_chore_notify, bool) and this_chore_notify == True:
                this_chore_notify = self.raw.get("default_notification_days", 1)

            this_chore = chore.Chore(
                raw_chore.get("name"),
                ordinal,
                raw_chore.get("recurrence"),
                this_chore_notify,
                raw_chore.get(
                    "required_training_sessions",
                    self.raw.get("default_number_of_training_sessions", 1),
                ),
                raw_chore.get(
                    "required_shadowing_sessions",
                    self.raw.get("default_number_of_shadowing_sessions", 1),
                ),
                raw_chore.get("exceptions", []),
            )
            self.chores.add(this_chore)

        self.people = set()
        for raw_person in self.raw.get("person"):
            this_person_skills = self._get_chores_from_names(
                raw_person.get("skills", [])
            )
            this_person_training = self._get_chores_from_names(
                raw_person.get("training", [])
            )

            this_person = person.Person(
                raw_person.get("name"),
                this_person_skills,
                str(raw_person.get("telephone", "")),
                raw_person.get("unavailable", []),
                this_person_training,
            )
            self.people.add(this_person)

    def __repr__(self):
        return f"Config({repr(self.path)})"

    def __str__(self):
        s = self.name + "\n"
        s += "  Chores:\n"
        for c in self.chores:
            s += "    - " + str(c) + "\n"

        s += "  People:\n"
        for p in self.people:
            s += "    - " + str(p) + "\n"

        return s.strip()

    def __eq__(self, other) -> bool:
        return other and self.name == other.name

    def _get_chores_from_names(self, names: Iterable[str]) -> Iterable[chore.Chore]:
        if len(names) == 1:
            singleton_name = names[0].lower()
            if singleton_name in ("any", "all"):
                return self.chores

        found_chores = set()
        for name in names:
            found_chores.add(chore.find_chore(name, self.chores))

        return found_chores
