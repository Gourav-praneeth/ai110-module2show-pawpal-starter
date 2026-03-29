"""
PawPal+ Logic Layer
All backend classes for the pet care scheduling system.

Class Diagram (Mermaid.js):

```mermaid
classDiagram

    class Task {
        +String description
        +String time
        +String frequency
        +bool completed
        +mark_complete()
        +mark_incomplete()
        +is_high_priority() bool
        +to_dict() dict
    }

    class Pet {
        +String name
        +String species
        +int age
        +String priority
        +list~Task~ tasks
        +add_task(task: Task)
        +get_tasks() list~Task~
        +get_pending_tasks() list~Task~
    }

    class Owner {
        +String name
        +int available_minutes
        +String preferred_start_time
        +list~Pet~ pets
        +add_pet(pet: Pet)
        +get_all_tasks() list~Task~
        +get_all_pending_tasks() list~Task~
        +get_available_time() int
    }

    class Scheduler {
        +Owner owner
        +schedule_day() Schedule
        +get_all_tasks() list~Task~
        +sort_by_priority(tasks: list) list
        +fits_in_time(task: Task, remaining: int) bool
    }

    class Schedule {
        +Owner owner
        +list~Task~ ordered_tasks
        +list~String~ explanations
        +list~Task~ skipped_tasks
        +list~String~ skipped_reasons
        +int total_minutes
        +add_task(task: Task, reason: String)
        +skip_task(task: Task, reason: String)
        +display() String
    }

    Owner "1" --> "1..*" Pet : owns
    Pet "1" --> "0..*" Task : has
    Scheduler --> Owner : uses
    Scheduler --> Schedule : creates
    Schedule --> Owner : belongs to
```
"""

from dataclasses import dataclass, field
from typing import List

VALID_PRIORITIES = {"low", "medium", "high"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Task — a single care activity for a pet
# Fields: description, time, frequency, completed
# ---------------------------------------------------------------------------

@dataclass
class Task:
    description: str        # what needs to be done, e.g. "Morning walk"
    time: str               # when it should happen, e.g. "08:00" or "after meals"
    frequency: str          # how often, e.g. "daily", "twice daily", "weekly"
    priority: str = "medium"  # "low", "medium", or "high"
    completed: bool = False   # tracks whether this task is done today

    def __post_init__(self):
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{self.priority}'. Choose from: {VALID_PRIORITIES}"
            )

    def mark_complete(self):
        """Mark this task as done."""
        self.completed = True

    def mark_incomplete(self):
        """Reset this task so it can be done again."""
        self.completed = False

    def is_high_priority(self) -> bool:
        return self.priority == "high"

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "time": self.time,
            "frequency": self.frequency,
            "priority": self.priority,
            "completed": self.completed,
        }


# ---------------------------------------------------------------------------
# Pet — stores pet details and a list of tasks
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str      # "dog", "cat", or "other"
    age: int = 0
    priority: str = "medium"  # overall care priority for this pet
    tasks: List[Task] = field(default_factory=list)

    def __post_init__(self):
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{self.priority}'. Choose from: {VALID_PRIORITIES}"
            )

    def add_task(self, task: Task):
        """Add a care task to this pet."""
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        return self.tasks

    def get_pending_tasks(self) -> List[Task]:
        """Return only tasks that have not been completed yet."""
        return [t for t in self.tasks if not t.completed]


# ---------------------------------------------------------------------------
# Owner — manages multiple pets and provides access to all their tasks
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    name: str
    available_minutes: int = 480   # how much free time the owner has today (default 8 hrs)
    preferred_start_time: str = "08:00"
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        """Add a pet to this owner's care list."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Collect and return every task across all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def get_all_pending_tasks(self) -> List[Task]:
        """Collect and return only incomplete tasks across all pets."""
        pending = []
        for pet in self.pets:
            pending.extend(pet.get_pending_tasks())
        return pending

    def get_available_time(self) -> int:
        return self.available_minutes


# ---------------------------------------------------------------------------
# Schedule — the output: an ordered plan with explanations
# ---------------------------------------------------------------------------

@dataclass
class Schedule:
    owner: Owner = None
    ordered_tasks: List[Task] = field(default_factory=list)
    explanations: List[str] = field(default_factory=list)
    skipped_tasks: List[Task] = field(default_factory=list)
    skipped_reasons: List[str] = field(default_factory=list)
    total_minutes: int = 0

    def add_task(self, task: Task, reason: str):
        self.ordered_tasks.append(task)
        self.explanations.append(reason)

    def skip_task(self, task: Task, reason: str):
        self.skipped_tasks.append(task)
        self.skipped_reasons.append(reason)

    def display(self) -> str:
        if not self.ordered_tasks:
            return "No tasks scheduled."
        owner_label = f" for {self.owner.name}" if self.owner else ""
        lines = [f"PawPal+ Daily Schedule{owner_label}", "=" * 35]
        for i, (task, reason) in enumerate(zip(self.ordered_tasks, self.explanations), 1):
            status = "✓" if task.completed else "○"
            lines.append(
                f"{i}. [{status}] {task.description} "
                f"@ {task.time} | {task.frequency} | {task.priority} priority"
            )
            lines.append(f"   Why: {reason}")
        lines.append("=" * 35)
        if self.skipped_tasks:
            lines.append("\nCould not fit into today's schedule:")
            for task, reason in zip(self.skipped_tasks, self.skipped_reasons):
                lines.append(f"  - {task.description}: {reason}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler — the "brain" that retrieves, organizes, and manages tasks
#             across ALL of the owner's pets
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def get_all_tasks(self) -> List[Task]:
        """Pull all pending tasks from every pet the owner has."""
        return self.owner.get_all_pending_tasks()

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks so high priority comes first."""
        return sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

    def fits_in_time(self, task: Task, remaining_minutes: int) -> bool:
        """Check whether a task can still fit in the remaining time."""
        # Each task is assumed to take a fixed block of time based on frequency:
        # daily = 30 min block, twice daily = 15 min, weekly = 60 min
        estimated = {"daily": 30, "twice daily": 15, "weekly": 60}
        duration = estimated.get(task.frequency, 30)
        return duration <= remaining_minutes

    def schedule_day(self) -> Schedule:
        """
        Build today's plan:
        1. Gather all pending tasks across all pets.
        2. Sort by priority (high first).
        3. Fit tasks into the owner's available time.
        4. Record skipped tasks with a reason.
        """
        schedule = Schedule(owner=self.owner)
        remaining = self.owner.get_available_time()
        sorted_tasks = self.sort_by_priority(self.get_all_tasks())

        estimated_durations = {"daily": 30, "twice daily": 15, "weekly": 60}

        for task in sorted_tasks:
            duration = estimated_durations.get(task.frequency, 30)
            if self.fits_in_time(task, remaining):
                reason = (
                    f"Scheduled at {task.time} ({task.frequency})"
                    + (" — high priority, do this first!" if task.is_high_priority() else ".")
                )
                schedule.add_task(task, reason)
                remaining -= duration
            else:
                schedule.skip_task(
                    task,
                    f"Not enough time left today "
                    f"({remaining} min remaining, needs ~{duration} min)."
                )

        return schedule
