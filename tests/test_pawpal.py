from pawpal_system import Task, Pet, Owner, Scheduler


def test_mark_complete_changes_status():
    """Task completion: mark_complete() should set completed to True."""
    task = Task(description="Morning walk", time="08:00", frequency="daily", priority="high")

    assert task.completed is False  # starts incomplete

    task.mark_complete()

    assert task.completed is True   # should now be complete


def test_add_task_increases_pet_task_count():
    """Task addition: adding a task to a Pet should increase its task count by 1."""
    pet = Pet(name="Mochi", species="dog")

    assert len(pet.get_tasks()) == 0  # starts with no tasks

    pet.add_task(Task(description="Feed breakfast", time="08:30", frequency="twice daily", priority="high"))

    assert len(pet.get_tasks()) == 1  # should now have one task


def test_sort_tasks_returns_chronological_order():
    """Sorting correctness: sort_tasks() should return tasks in earliest-to-latest time order."""
    owner = Owner(name="Alex")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    t1 = Task(description="Evening walk", time="18:00", frequency="daily", priority="low")
    t2 = Task(description="Noon meds", time="12:00", frequency="daily", priority="medium")
    t3 = Task(description="Morning walk", time="08:00", frequency="daily", priority="high")

    sorted_tasks = scheduler.sort_tasks([t1, t2, t3])

    assert sorted_tasks[0].time == "08:00"
    assert sorted_tasks[1].time == "12:00"
    assert sorted_tasks[2].time == "18:00"


def test_expand_recurring_twice_daily_creates_two_entries():
    """Recurrence logic: a 'twice daily' task should expand into two scheduled entries."""
    owner = Owner(name="Sam")
    pet = Pet(name="Luna", species="cat")
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    task = Task(description="Feed lunch", time="08:30", frequency="twice daily", priority="medium")
    expanded = scheduler.expand_recurring([task])

    assert len(expanded) == 2                              # original + evening copy
    assert expanded[0].description == "Feed lunch"         # original is first
    assert "(evening)" in expanded[1].description          # second is the recurrence
    assert expanded[1].time == "16:30"                     # 8 hrs later: 08:30 + 8h = 16:30


def test_detect_conflicts_flags_duplicate_times():
    """Conflict detection: Scheduler should flag tasks scheduled at the same time."""
    owner = Owner(name="Jordan")
    scheduler = Scheduler(owner)

    t1 = Task(description="Walk dog", time="09:00", frequency="daily", priority="high")
    t2 = Task(description="Give meds", time="09:00", frequency="daily", priority="medium")
    t3 = Task(description="Brush fur", time="10:00", frequency="daily", priority="low")

    conflicts = scheduler.detect_conflicts([t1, t2, t3])

    assert len(conflicts) == 1                     # exactly one conflicting time slot
    assert "09:00" in conflicts[0]                 # the conflict is at 09:00
    assert "Walk dog" in conflicts[0]
    assert "Give meds" in conflicts[0]
