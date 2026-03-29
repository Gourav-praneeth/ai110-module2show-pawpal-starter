"""
PawPal+ Logic Layer
All backend classes for the pet care scheduling system.

Class Diagram (Mermaid.js):

```mermaid
classDiagram

    class Owner {
        +String name
        +int available_minutes
        +String preferred_start_time
        +list~Pet~ pets
        +add_pet(pet: Pet)
        +get_available_time() int
    }

    class Pet {
        +String name
        +String species
        +int age
        +list~Task~ tasks
        +add_task(task: Task)
        +get_tasks() list~Task~
    }

    class Task {
        +String title
        +int duration_minutes
        +String priority
        +String reason
        +is_high_priority() bool
        +to_dict() dict
    }

    class Scheduler {
        +Owner owner
        +Pet pet
        +list~Task~ tasks
        +schedule_day() Schedule
        +sort_by_priority(tasks: list) list
        +fits_in_time(task: Task, remaining: int) bool
    }

    class Schedule {
        +list~Task~ ordered_tasks
        +list~String~ explanations
        +int total_minutes
        +add_task(task: Task, reason: String)
        +display() String
    }

    Owner "1" --> "1..*" Pet : owns
    Pet "1" --> "0..*" Task : has
    Scheduler --> Owner : uses
    Scheduler --> Pet : uses
    Scheduler --> Task : reads
    Scheduler --> Schedule : creates
```
"""

from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Task — one care job for a pet
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", or "high"
    reason: str = ""

    def is_high_priority(self) -> bool:
        return self.priority == "high"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Pet — the animal being cared for
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", or "other"
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        return self.tasks


# ---------------------------------------------------------------------------
# Owner — the person using the app
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    name: str
    available_minutes: int = 480  # defaults to 8 hours
    preferred_start_time: str = "08:00"
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        self.pets.append(pet)

    def get_available_time(self) -> int:
        return self.available_minutes


# ---------------------------------------------------------------------------
# Schedule — the output: an ordered plan with explanations
# ---------------------------------------------------------------------------

@dataclass
class Schedule:
    ordered_tasks: List[Task] = field(default_factory=list)
    explanations: List[str] = field(default_factory=list)
    total_minutes: int = 0

    def add_task(self, task: Task, reason: str):
        self.ordered_tasks.append(task)
        self.explanations.append(reason)
        self.total_minutes += task.duration_minutes

    def display(self) -> str:
        if not self.ordered_tasks:
            return "No tasks scheduled."
        lines = ["Your PawPal+ Daily Schedule", "=" * 30]
        for i, (task, reason) in enumerate(zip(self.ordered_tasks, self.explanations), 1):
            lines.append(f"{i}. {task.title} ({task.duration_minutes} min | {task.priority} priority)")
            lines.append(f"   Why: {reason}")
        lines.append("=" * 30)
        lines.append(f"Total time: {self.total_minutes} minutes")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler — the brain that builds the daily plan
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: List[Task]):
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        return sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

    def fits_in_time(self, task: Task, remaining_minutes: int) -> bool:
        return task.duration_minutes <= remaining_minutes

    def schedule_day(self) -> Schedule:
        schedule = Schedule()
        remaining = self.owner.get_available_time()
        sorted_tasks = self.sort_by_priority(self.tasks)

        for task in sorted_tasks:
            if self.fits_in_time(task, remaining):
                reason = (
                    f"Scheduled because it is {task.priority} priority"
                    + (" — do this first!" if task.is_high_priority() else ".")
                )
                schedule.add_task(task, reason)
                remaining -= task.duration_minutes
            else:
                # Task doesn't fit — skip and note why
                schedule.explanations  # no-op, task simply not added

        return schedule
