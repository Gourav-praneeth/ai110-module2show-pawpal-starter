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

from collections import defaultdict
from dataclasses import dataclass, field
from typing import List

VALID_PRIORITIES = {"low", "medium", "high"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Single source of truth for how long each frequency type takes (minutes)
TASK_DURATIONS = {"daily": 30, "twice daily": 15, "weekly": 60}

# Weighted scoring constants
PRIORITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}
# Weekly tasks are harder to reschedule than daily ones → rarity bonus
FREQUENCY_RARITY = {"weekly": 2, "daily": 1, "twice daily": 0}


def _parse_time(time_str: str) -> int:
    """Convert 'HH:MM' to minutes since midnight. Returns 9999 for non-clock strings."""
    try:
        h, m = time_str.strip().split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return 9999


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
    conflicts: List[str] = field(default_factory=list)
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
        if self.conflicts:
            lines.append("*** TIME CONFLICTS DETECTED ***")
            for c in self.conflicts:
                lines.append(f"  ! {c}")
            lines.append("")
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
        """Sort tasks so high priority comes first (original method, kept for compatibility)."""
        return sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Sort tasks chronologically, breaking ties by priority.

        Primary key:   scheduled time (earliest first), parsed from 'HH:MM'.
                       Tasks with non-clock times (e.g. 'after meals') sort last.
        Secondary key: priority level (high → medium → low) within the same slot.

        Args:
            tasks: Any list of Task objects.

        Returns:
            A new sorted list; the original list is not modified.
        """
        return sorted(
            tasks,
            key=lambda t: (_parse_time(t.time), PRIORITY_ORDER.get(t.priority, 99))
        )

    def filter_by_pet(self, pet_name: str) -> List[Task]:
        """
        Return all tasks belonging to a specific pet.

        Args:
            pet_name: The pet's name (case-insensitive).

        Returns:
            The pet's full task list, or an empty list if the name is not found.
        """
        for pet in self.owner.pets:
            if pet.name.lower() == pet_name.lower():
                return pet.get_tasks()
        return []

    def filter_by_status(self, completed: bool) -> List[Task]:
        """
        Return tasks across all pets filtered by completion status.

        Args:
            completed: Pass True for finished tasks, False for pending ones.

        Returns:
            A list of matching Task objects.
        """
        return [t for t in self.owner.get_all_tasks() if t.completed == completed]

    def expand_recurring(self, tasks: List[Task]) -> List[Task]:
        """
        Expand 'twice daily' tasks so each appears twice in the schedule.

        The second occurrence is created 8 hours after the original time
        (e.g. 08:30 → 16:30) and labelled with '(evening)'. All other
        frequencies are passed through unchanged.

        Args:
            tasks: Pending tasks before expansion.

        Returns:
            A new list where each 'twice daily' task produces two entries.
        """
        expanded = []
        for task in tasks:
            expanded.append(task)
            if task.frequency == "twice daily":
                original_minutes = _parse_time(task.time)
                if original_minutes < 9999:
                    second_total = original_minutes + 480  # +8 hours
                    second_time = f"{second_total // 60:02d}:{second_total % 60:02d}"
                else:
                    second_time = "18:00"
                second_instance = Task(
                    description=f"{task.description} (evening)",
                    time=second_time,
                    frequency=task.frequency,
                    priority=task.priority,
                    completed=task.completed,
                )
                expanded.append(second_instance)
        return expanded

    def detect_conflicts(self, tasks: List[Task]) -> List[str]:
        """
        Identify tasks scheduled at the exact same clock time.

        Conflict detection is intentionally kept as an exact-match check
        (same 'HH:MM' string) rather than an overlap check. This is simpler
        and sufficient for a single-owner daily planner where tasks are short
        and do not carry explicit end times. See reflection.md § 2b for the
        full tradeoff discussion.

        Note: Tasks with non-clock time strings (e.g. 'after meals') are
        excluded from conflict detection because their position is ambiguous.

        Args:
            tasks: The expanded task list (after expand_recurring).

        Returns:
            A sorted list of warning strings, one per conflicting time slot.
            Returns an empty list when no conflicts exist.
        """
        time_buckets: dict = defaultdict(list)
        for task in tasks:
            if _parse_time(task.time) < 9999:
                time_buckets[task.time].append(task)
        conflicts = []
        for time_slot, slot_tasks in sorted(time_buckets.items()):
            if len(slot_tasks) > 1:
                names = ", ".join(f"'{t.description}'" for t in slot_tasks)
                conflicts.append(f"{time_slot}: {names}")
        return conflicts

    def weighted_score(self, task: Task) -> float:
        """
        Compute a composite priority score for a task.

        Score components:
          • Task priority    (high=3, medium=2, low=1)  × 2  — most important dimension
          • Pet priority     (high=3, medium=2, low=1)  × 1  — reflects the pet's overall care urgency
          • Time urgency     +1 if the task is scheduled before noon (morning tasks
                             are harder to defer because other commitments pile up later)
          • Frequency rarity weekly=+2, daily=+1, twice-daily=+0 — weekly tasks
                             can't simply be pushed to tomorrow, so they earn a bump

        Higher score = should be attempted earlier in the day.

        Args:
            task: The Task to evaluate.

        Returns:
            A non-negative float; higher means more urgent.
        """
        task_weight = PRIORITY_WEIGHT.get(task.priority, 1) * 2

        # Find which pet owns this task so we can include their priority
        pet_weight = 1  # default if task is somehow orphaned
        for pet in self.owner.pets:
            if task in pet.tasks:
                pet_weight = PRIORITY_WEIGHT.get(pet.priority, 1)
                break

        time_urgency = 1 if _parse_time(task.time) < 720 else 0  # before 12:00 → +1
        rarity_bonus = FREQUENCY_RARITY.get(task.frequency, 0)

        return task_weight + pet_weight + time_urgency + rarity_bonus

    def rank_by_weight(self, tasks: List[Task]) -> List[Task]:
        """
        Return tasks sorted by composite weighted score (highest first).

        Unlike sort_tasks (purely chronological) or sort_by_priority (single
        dimension), rank_by_weight balances four factors simultaneously:
        task priority, pet priority, time-of-day urgency, and frequency rarity.
        Use this when you want the *most important* tasks surfaced first,
        regardless of when they are scheduled.

        Args:
            tasks: Any list of Task objects.

        Returns:
            A new list sorted by descending score; ties broken by task priority.
        """
        return sorted(
            tasks,
            key=lambda t: (-self.weighted_score(t), PRIORITY_ORDER.get(t.priority, 99))
        )

    def fits_in_time(self, task: Task, remaining_minutes: int) -> bool:
        """Check whether a task can still fit in the remaining time."""
        duration = TASK_DURATIONS.get(task.frequency, 30)
        return duration <= remaining_minutes

    def schedule_day(self) -> Schedule:
        """
        Build today's plan:
        1. Gather all pending tasks across all pets.
        2. Expand recurring (twice daily) tasks into two occurrences.
        3. Detect and record any time conflicts.
        4. Sort by scheduled time, then priority.
        5. Fit tasks into the owner's available time, skipping what won't fit.
        """
        schedule = Schedule(owner=self.owner)
        remaining = self.owner.get_available_time()

        expanded = self.expand_recurring(self.get_all_tasks())
        schedule.conflicts = self.detect_conflicts(expanded)
        sorted_tasks = self.sort_tasks(expanded)

        for task in sorted_tasks:
            duration = TASK_DURATIONS.get(task.frequency, 30)
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
