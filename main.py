from pawpal_system import Task, Pet, Owner, Scheduler

# --- Create Owner ---
owner = Owner(name="Jordan", available_minutes=120, preferred_start_time="08:00")

# --- Create Pets ---
dog = Pet(name="Mochi", species="dog", age=3, priority="high")
cat = Pet(name="Luna", species="cat", age=5, priority="medium")

# --- Add Tasks to Mochi (dog) ---
dog.add_task(Task(description="Morning walk",       time="08:00", frequency="daily",       priority="high"))
dog.add_task(Task(description="Feed breakfast",     time="08:30", frequency="twice daily",  priority="high"))
dog.add_task(Task(description="Give flea medicine", time="09:00", frequency="weekly",       priority="medium"))

# --- Add Tasks to Luna (cat) ---
# "Clean litter box" is intentionally at 09:00 to trigger conflict detection
cat.add_task(Task(description="Clean litter box",   time="09:00", frequency="daily",        priority="medium"))
cat.add_task(Task(description="Brush fur",          time="10:00", frequency="weekly",       priority="low"))

# --- Register Pets with Owner ---
owner.add_pet(dog)
owner.add_pet(cat)

# --- Build Scheduler ---
scheduler = Scheduler(owner=owner)

# ------------------------------------------------------------------
# Feature 1: Filter tasks by pet name
# ------------------------------------------------------------------
print("=== Mochi's Tasks ===")
for t in scheduler.filter_by_pet("Mochi"):
    print(f"  {t.time}  {t.description} [{t.priority}]")

print("\n=== Luna's Tasks ===")
for t in scheduler.filter_by_pet("Luna"):
    print(f"  {t.time}  {t.description} [{t.priority}]")

# ------------------------------------------------------------------
# Feature 2: Filter by completion status
# ------------------------------------------------------------------
print("\n=== Pending Tasks (all pets) ===")
for t in scheduler.filter_by_status(completed=False):
    print(f"  {t.time}  {t.description} [{t.priority}]")

# ------------------------------------------------------------------
# Feature 3: Sort all tasks by time (then priority within same slot)
# ------------------------------------------------------------------
all_tasks = owner.get_all_tasks()
print("\n=== All Tasks Sorted by Time ===")
for t in scheduler.sort_tasks(all_tasks):
    print(f"  {t.time}  {t.description} [{t.priority}]")

# ------------------------------------------------------------------
# Feature 4: Expand recurring tasks (twice daily → 2 occurrences)
# ------------------------------------------------------------------
expanded = scheduler.expand_recurring(all_tasks)
print("\n=== After Expanding Recurring Tasks ===")
for t in scheduler.sort_tasks(expanded):
    print(f"  {t.time}  {t.description} [{t.frequency}]")

# ------------------------------------------------------------------
# Feature 5: Conflict detection
# ------------------------------------------------------------------
conflicts = scheduler.detect_conflicts(expanded)
if conflicts:
    print("\n=== Time Conflicts Detected ===")
    for c in conflicts:
        print(f"  WARNING: {c}")

# ------------------------------------------------------------------
# Run Scheduler and print the full daily plan
# ------------------------------------------------------------------
schedule = scheduler.schedule_day()
print("\n" + schedule.display())
