import toml
from . import chore, person

class Config:
    def __init__(self, toml_file_path: str) -> None:
        self.path = toml_file_path
        self.raw = toml.load(self.path)
        
        self.chores = set()
        for raw_chore in self.raw.get("chore", []):
            this_chore = chore.Chore(
                raw_chore.get("name"),
                raw_chore.get("recurrence"),
                raw_chore.get("notify"),
                raw_chore.get("exceptions", [])
            )
            self.chores.add(this_chore)
        
        self.people = set()
        for raw_person in self.raw.get("person", []):
            this_person_skills = self._get_chores_from_names(
                raw_person.get("skills", [])
            )
            this_person_training = self._get_chores_from_names(
                raw_person.get("training", [])
            )
            
            this_person = person.Person(
                raw_person.get("name"),
                str(raw_person.get("telephone")),
                this_person_skills,
                raw_person.get("unavailable", []),
                this_person_training
            )
            self.people.add(this_person)
    
    def __repr__(self):
        return f"Config({self.path})"
    
    def __str__(self):
        s = "Chores:\n"
        for c in self.chores:
            s += "  - " + str(c) + "\n"
        
        s += "\nPeople:\n"
        for p in self.people:
            s += "  - " + str(p) + "\n"
        
        return s
    
    def _get_chores_from_names(self, names: list[str]) -> set[chore.Chore]:
        if len(names) == 1:
            singleton_name = names[0].lower()
            if singleton_name in ["any", "all"]:
                return self.chores
        
        found_chores = set()
        for name in names:
            found_chores.add(chore.find_chore(name, self.chores))
        
        return found_chores