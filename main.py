from tabulate import tabulate
from pawpal_system import Task, Pet, Owner, Scheduler

# ── Display helpers ────────────────────────────────────────────────────────

PRIORITY_LABEL = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
SPECIES_EMOJI  = {"dog": "🐕", "cat": "🐈"}
FREQ_LABEL     = {"daily": "📅 Daily", "twice daily": "🔁 Twice Daily", "weekly": "🗓️ Weekly"}

_TASK_KEYWORDS = [
    (["walk", "run", "exercise"],                  "🦮"),
    (["feed", "food", "meal", "breakfast",
      "dinner", "lunch"],                          "🍽️"),
    (["medicine", "med", "pill", "flea"],          "💊"),
    (["groom", "brush", "bath", "wash", "trim"],   "✂️"),
    (["litter", "clean", "scoop"],                 "🧹"),
    (["play", "enrich", "toy"],                    "🎾"),
    (["vet", "checkup", "appointment"],            "🏥"),
]

def _task_emoji(desc: str) -> str:
    lower = desc.lower()
    for keywords, emoji in _TASK_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return emoji
    return "📋"

def _p(priority: str) -> str:
    return PRIORITY_LABEL.get(priority, priority)

def _freq(frequency: str) -> str:
    return FREQ_LABEL.get(frequency, frequency)

def _species(species: str) -> str:
    return SPECIES_EMOJI.get(species, "🐾")

def _status(completed: bool) -> str:
    return "✅ Done" if completed else "⏳ Pending"

def print_table(rows: list, headers: list, title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))


# ── Data setup ─────────────────────────────────────────────────────────────

owner = Owner(name="Jordan", available_minutes=120, preferred_start_time="08:00")

dog = Pet(name="Mochi", species="dog", age=3, priority="high")
cat = Pet(name="Luna",  species="cat", age=5, priority="medium")

dog.add_task(Task(description="Morning walk",       time="08:00", frequency="daily",       priority="high"))
dog.add_task(Task(description="Feed breakfast",     time="08:30", frequency="twice daily",  priority="high"))
dog.add_task(Task(description="Give flea medicine", time="09:00", frequency="weekly",       priority="medium"))

# "Clean litter box" is at 09:00 intentionally to trigger conflict detection
cat.add_task(Task(description="Clean litter box",   time="09:00", frequency="daily",        priority="medium"))
cat.add_task(Task(description="Brush fur",          time="10:00", frequency="weekly",       priority="low"))

owner.add_pet(dog)
owner.add_pet(cat)

scheduler = Scheduler(owner=owner)

# ── Feature 1: Filter tasks by pet ─────────────────────────────────────────

for pet in owner.pets:
    rows = [
        [_task_emoji(t.description), t.description, t.time, _freq(t.frequency), _p(t.priority), _status(t.completed)]
        for t in scheduler.filter_by_pet(pet.name)
    ]
    print_table(
        rows,
        headers=["", "Description", "Time", "Frequency", "Priority", "Status"],
        title=f"{_species(pet.species)} {pet.name}'s Tasks",
    )

# ── Feature 2: Filter by completion status ──────────────────────────────────

pending_rows = [
    [_task_emoji(t.description), t.description, t.time, _p(t.priority)]
    for t in scheduler.filter_by_status(completed=False)
]
print_table(
    pending_rows,
    headers=["", "Description", "Time", "Priority"],
    title="⏳ Pending Tasks (all pets)",
)

# ── Feature 3: Sort by priority then time ──────────────────────────────────

all_tasks    = owner.get_all_tasks()
sorted_rows  = [
    [_task_emoji(t.description), t.description, t.time, _freq(t.frequency), _p(t.priority)]
    for t in scheduler.sort_by_priority(all_tasks)
]
print_table(
    sorted_rows,
    headers=["", "Description", "Time", "Frequency", "Priority"],
    title="📊 All Tasks — Sorted by Priority, then Time",
)

# ── Feature 4: Expand recurring tasks ──────────────────────────────────────

expanded      = scheduler.expand_recurring(all_tasks)
expanded_rows = [
    [_task_emoji(t.description), t.description, t.time, _freq(t.frequency)]
    for t in scheduler.sort_tasks(expanded)
]
print_table(
    expanded_rows,
    headers=["", "Description", "Time", "Frequency"],
    title="🔁 After Expanding Recurring Tasks",
)

# ── Feature 5: Conflict detection ──────────────────────────────────────────

conflicts = scheduler.detect_conflicts(expanded)
if conflicts:
    print_table(
        [["⚠️", c] for c in conflicts],
        headers=["", "Conflict"],
        title="🚨 Time Conflicts Detected",
    )

# ── Feature 6: Weighted priority ranking ───────────────────────────────────

ranked      = scheduler.rank_by_weight(all_tasks)
ranked_rows = [
    [i, _task_emoji(t.description), t.description, t.time, _p(t.priority), _freq(t.frequency), scheduler.weighted_score(t)]
    for i, t in enumerate(ranked, 1)
]
print_table(
    ranked_rows,
    headers=["Rank", "", "Description", "Time", "Priority", "Frequency", "Score"],
    title="⚖️ Weighted Priority Ranking",
)

# ── Full daily schedule ─────────────────────────────────────────────────────

schedule = scheduler.schedule_day()

print(f"\n{'=' * 60}")
print(f"  🗓️  Today's Schedule for {owner.name}")
print(f"{'=' * 60}")

if schedule.conflicts:
    print("\n  ⚠️  TIME CONFLICTS:")
    for c in schedule.conflicts:
        print(f"     ! {c}")

if schedule.ordered_tasks:
    sched_rows = [
        [i, _task_emoji(t.description), t.description, t.time, _freq(t.frequency), _p(t.priority), reason]
        for i, (t, reason) in enumerate(zip(schedule.ordered_tasks, schedule.explanations), 1)
    ]
    print(tabulate(
        sched_rows,
        headers=["#", "", "Task", "Time", "Frequency", "Priority", "Why"],
        tablefmt="rounded_outline",
    ))

    total_avail  = owner.available_minutes
    minutes_used = sum(
        30 if t.frequency == "daily" else 15 if t.frequency == "twice daily" else 60
        for t in schedule.ordered_tasks
    )
    bar_filled = int((minutes_used / total_avail) * 20) if total_avail else 0
    bar        = "█" * bar_filled + "░" * (20 - bar_filled)
    print(f"\n  ⏱️  Time budget: [{bar}] {minutes_used}/{total_avail} min")

if schedule.skipped_tasks:
    skip_rows = [
        [_task_emoji(t.description), t.description, reason]
        for t, reason in zip(schedule.skipped_tasks, schedule.skipped_reasons)
    ]
    print_table(
        skip_rows,
        headers=["", "Task", "Reason"],
        title="⏭️  Could Not Fit Today",
    )
