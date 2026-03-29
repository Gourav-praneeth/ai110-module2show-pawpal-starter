from pawpal_system import Task, Pet


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
